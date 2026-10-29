"""Proctored quiz sessions: generation, one-question-at-a-time delivery, answers, integrity
events and submission (Phases 10, 11 and 12.5).

The full questions, including the answer key, are stored server-side in quiz_sessions and only
revealed after submission (ARCHITECTURE.md section 15). Proctoring layer 1 lives here: questions
are served one at a time with server-enforced deadlines, answers lock once given, generation is
rate limited and only one quiz is active per learner. Layer 2 events are stored here and scored
by services/proctoring.py; a flagged attempt is recorded but changes no progress.
"""

import logging
import math
import random
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, true
from sqlalchemy.orm import Session

from config import get_settings
from models import ProctoringEvent, QuizAttempt, QuizIntegrity, QuizResponse, QuizSession, TopicProgress, TopicStatus
from schemas.quiz import QuizQuestion
from seed.curriculum import DOMAIN, DOMAIN_NAME
from services import proctoring
from services.bkt import mastery_reached, update_bkt_sequence
from services.learning_path import ensure_progress_rows, recommendations, sync_statuses
from services.llm_quiz import generate_questions
from services.topic_service import get_progress_map, get_topics

logger = logging.getLogger("adaptlearn")

_rng = random.SystemRandom()

PASS_SCORE = 2  # PRD 6.2: pass with at least 2 of 3
ANSWER_GRACE_SECONDS = 2  # network latency allowance on each question deadline
MAX_EVENTS_PER_SESSION = 1000
RATE_WINDOW = timedelta(hours=1)


def utc_now() -> datetime:
    """Current time. A function so tests can control the clock."""
    return datetime.now(timezone.utc)


# --- Errors --------------------------------------------------------------------------

class TopicNotFoundError(Exception):
    pass


class TopicLockedError(Exception):
    pass


class QuizUnavailableError(Exception):
    pass


class QuizNotFoundError(Exception):
    pass


class QuizAlreadySubmittedError(Exception):
    pass


class QuizExpiredError(Exception):
    pass


class QuizCompleteError(Exception):
    """Every question has been answered or timed out; the quiz should be submitted."""


class QuestionNotOpenError(Exception):
    """The question was never served, or was already answered or timed out."""


class QuizRateLimitedError(Exception):
    def __init__(self, retry_after_seconds: int, scope: str):
        super().__init__(scope)
        self.retry_after_seconds = retry_after_seconds
        self.scope = scope


# --- Helpers -------------------------------------------------------------------------

def needs_attention(attempts: int, p_know: float) -> bool:
    """PRD 6.3 confusion rule."""
    return attempts > 2 and p_know < 0.50


def shuffle_options(question: QuizQuestion) -> dict[str, Any]:
    """Shuffle the options and remap the answer index, so the stored position reveals nothing
    and any position bias in LLM output disappears."""
    order = list(range(len(question.options)))
    _rng.shuffle(order)
    return {
        "question": question.question,
        "options": [question.options[i] for i in order],
        "correct": order.index(question.correct),
        "explanation": question.explanation,
    }


def _proctoring_info() -> dict[str, Any]:
    return {
        "verified_threshold": proctoring.VERIFIED_THRESHOLD,
        "heartbeat_interval_seconds": proctoring.HEARTBEAT_INTERVAL_SECONDS,
        "rules": proctoring.rules_summary(),
    }


def _responses(db: Session, session_id: UUID) -> dict[int, QuizResponse]:
    rows = db.scalars(select(QuizResponse).where(QuizResponse.session_id == session_id))
    return {r.question_index: r for r in rows}


def _close_overdue(responses: dict[int, QuizResponse], now: datetime) -> None:
    for response in responses.values():
        if response.is_open and now > response.deadline + timedelta(seconds=ANSWER_GRACE_SECONDS):
            response.timed_out = True


def _quiz_info(db: Session, session: QuizSession, topic_name: str, now: datetime, source: str | None = None) -> dict:
    responses = _responses(db, session.id)
    return {
        "quiz_id": session.id,
        "topic": {"id": session.topic_id, "name": topic_name},
        "total_questions": len(session.questions),
        "answered_questions": sum(1 for r in responses.values() if not r.is_open),
        "seconds_per_question": get_settings().quiz_seconds_per_question,
        "expires_in_seconds": max(0, int((session.expires_at - now).total_seconds())),
        "source": source,
        "proctoring": _proctoring_info(),
    }


def _load_open_session(db: Session, user_id: int, quiz_id: UUID, now: datetime) -> QuizSession:
    # Locked, so concurrent requests on the same quiz are processed one at a time.
    session = db.scalar(
        select(QuizSession).where(QuizSession.id == quiz_id, QuizSession.user_id == user_id).with_for_update()
    )
    if session is None:
        raise QuizNotFoundError(quiz_id)  # also for another user's quiz: don't reveal that it exists
    if session.submitted_at is not None:
        raise QuizAlreadySubmittedError(quiz_id)
    if session.expires_at <= now:
        raise QuizExpiredError(quiz_id)
    return session


def _check_rate_limits(db: Session, user_id: int, topic_id: str, now: datetime) -> None:
    settings = get_settings()
    since = now - RATE_WINDOW
    for scope, limit, extra in (
        ("topic", settings.quiz_max_per_topic_per_hour, QuizSession.topic_id == topic_id),
        ("total", settings.quiz_max_per_hour, true()),
    ):
        count, oldest = db.execute(
            select(func.count(), func.min(QuizSession.created_at)).where(
                QuizSession.user_id == user_id, QuizSession.created_at > since, extra
            )
        ).one()
        if count >= limit:
            retry_after = math.ceil((oldest + RATE_WINDOW - now).total_seconds())
            raise QuizRateLimitedError(max(1, retry_after), scope)


def _abandon_open_sessions(db: Session, user_id: int) -> int:
    """Close the learner's unfinished quizzes. Abandoned quizzes never count."""
    open_sessions = db.scalars(
        select(QuizSession).where(QuizSession.user_id == user_id, QuizSession.submitted_at.is_(None)).with_for_update()
    ).all()
    for session in open_sessions:
        session.submitted_at = utc_now()
        db.add(QuizIntegrity(
            session_id=session.id, attempt_id=None, score=None, verdict=proctoring.VERDICT_ABANDONED, counted=False,
            reasons=[{"code": "abandoned", "count": 1, "penalty": 0,
                      "message": "A new quiz was started before this one was submitted"}],
        ))
    return len(open_sessions)


# --- Generation ------------------------------------------------------------------------

def create_quiz(db: Session, user_id: int, topic_id: str, domain: str = DOMAIN) -> dict[str, Any]:
    topics = get_topics(domain)
    topic = next((t for t in topics if t.id == topic_id), None)
    if topic is None:
        raise TopicNotFoundError(topic_id)

    progress = get_progress_map(db, user_id)
    if topic_id not in progress:
        # No progress yet (quiz requested before onboarding) or a topic added after onboarding:
        # initialise rows exactly as onboarding with nothing known would.
        ensure_progress_rows(db, user_id, [t.id for t in topics])
        sync_statuses(db, user_id, domain)
        progress = get_progress_map(db, user_id)
    row = progress[topic_id]
    if row.status == TopicStatus.LOCKED:
        raise TopicLockedError(topic_id)

    now = utc_now()
    _check_rate_limits(db, user_id, topic_id, now)  # before the LLM call, so limits also save quota

    generated = generate_questions(topic, DOMAIN_NAME)
    if generated is None:
        raise QuizUnavailableError(topic_id)

    abandoned = _abandon_open_sessions(db, user_id)
    session = QuizSession(
        user_id=user_id,
        topic_id=topic_id,
        questions=[shuffle_options(q) for q in generated.questions],
        created_at=now,
        expires_at=now + timedelta(minutes=get_settings().quiz_session_ttl_minutes),
    )
    db.add(session)
    if row.status == TopicStatus.UNLOCKED:
        row.status = TopicStatus.IN_PROGRESS.value  # decision 2
    db.flush()
    info = _quiz_info(db, session, topic.name, now, generated.source)
    db.commit()
    logger.info(
        "Quiz %s created for user id=%s topic=%s (%s)%s", session.id, user_id, topic_id, generated.source,
        f", abandoned {abandoned} unfinished quiz(zes)" if abandoned else "",
    )
    return info


def get_active_quiz(db: Session, user_id: int, domain: str = DOMAIN) -> dict[str, Any] | None:
    now = utc_now()
    session = db.scalar(
        select(QuizSession)
        .where(QuizSession.user_id == user_id, QuizSession.submitted_at.is_(None), QuizSession.expires_at > now)
        .order_by(QuizSession.created_at.desc())
        .limit(1)
    )
    if session is None:
        return None
    names = {t.id: t.name for t in get_topics(domain)}
    return _quiz_info(db, session, names.get(session.topic_id, session.topic_id), now)


# --- One question at a time -------------------------------------------------------------

def next_question(db: Session, user_id: int, quiz_id: UUID) -> dict[str, Any]:
    """Serve the current question. Asking again returns the same question with the time that is
    left, so reloading the page never resets the clock; questions already closed can't be reopened."""
    now = utc_now()
    session = _load_open_session(db, user_id, quiz_id, now)
    responses = _responses(db, session.id)
    _close_overdue(responses, now)

    current = next((r for r in sorted(responses.values(), key=lambda r: r.question_index) if r.is_open), None)
    if current is None:
        index = len(responses)
        if index >= len(session.questions):
            db.commit()  # keep any timeouts just recorded
            raise QuizCompleteError(quiz_id)
        current = QuizResponse(
            session_id=session.id,
            question_index=index,
            served_at=now,
            deadline=now + timedelta(seconds=get_settings().quiz_seconds_per_question),
        )
        db.add(current)
    db.commit()

    question = session.questions[current.question_index]
    return {
        "question_id": current.question_index,
        "number": current.question_index + 1,
        "total": len(session.questions),
        "question": question["question"],
        "options": question["options"],
        "deadline": current.deadline,
        "seconds_remaining": max(0, math.ceil((current.deadline - now).total_seconds())),
    }


def record_answer(db: Session, user_id: int, quiz_id: UUID, question_id: int, answer: int) -> dict[str, Any]:
    now = utc_now()
    session = _load_open_session(db, user_id, quiz_id, now)
    responses = _responses(db, session.id)
    response = responses.get(question_id)
    if response is None or not response.is_open:
        raise QuestionNotOpenError(question_id)

    accepted = now <= response.deadline + timedelta(seconds=ANSWER_GRACE_SECONDS)
    if accepted:
        response.answer = answer
        response.answered_at = now
    else:
        response.timed_out = True
    closed = sum(1 for r in responses.values() if not r.is_open)
    db.commit()
    return {
        "question_id": question_id,
        "accepted": accepted,
        "timed_out": not accepted,
        "remaining_questions": len(session.questions) - closed,
    }


def record_events(db: Session, user_id: int, quiz_id: UUID, events: list[dict[str, Any]]) -> dict[str, int]:
    now = utc_now()
    session = _load_open_session(db, user_id, quiz_id, now)
    stored = db.scalar(select(func.count()).select_from(ProctoringEvent).where(ProctoringEvent.session_id == session.id))
    room = max(0, MAX_EVENTS_PER_SESSION - stored)
    for event in events[:room]:
        db.add(ProctoringEvent(
            session_id=session.id,
            event_type=event["type"],
            received_at=now,
            occurred_at=event.get("occurred_at"),
            duration_ms=event.get("duration_ms"),
            details=event.get("details"),
        ))
    db.commit()
    return {"accepted": min(len(events), room), "ignored": max(0, len(events) - room)}


# --- Submission ---------------------------------------------------------------------------

def _assess_integrity(db: Session, session: QuizSession, responses: dict[int, QuizResponse], now: datetime):
    events = db.execute(
        select(ProctoringEvent.event_type, ProctoringEvent.received_at).where(ProctoringEvent.session_id == session.id)
    ).all()
    heartbeats = [received for kind, received in events if kind == "heartbeat"]
    client_events = [kind for kind, _ in events if kind != "heartbeat"]
    answered = [
        proctoring.AnswerTiming(r.served_at, r.answered_at) for r in responses.values() if r.answered_at is not None
    ]
    window_start = min((r.served_at for r in responses.values()), default=None)
    closes = [r.answered_at if r.answered_at is not None else r.deadline for r in responses.values()]
    window_end = min(max(closes), now) if closes else None
    return proctoring.score_integrity(client_events, heartbeats, answered, window_start, window_end)


def submit_quiz(db: Session, user_id: int, quiz_id: UUID, domain: str = DOMAIN) -> dict[str, Any]:
    """Score a quiz server-side, judge its integrity and, if verified, update progress.

    Unanswered, timed-out and never-served questions count as wrong. Everything happens in one
    transaction: if any step fails (e.g. Neo4j is down) nothing is saved and the quiz can be
    submitted again.
    """
    now = utc_now()
    session = _load_open_session(db, user_id, quiz_id, now)
    responses = _responses(db, session.id)
    _close_overdue(responses, now)

    questions = session.questions
    answers: list[int | None] = []
    for index in range(len(questions)):
        response = responses.get(index)
        answers.append(response.answer if response is not None and response.answered_at is not None else None)
    results = [answer is not None and answer == q["correct"] for answer, q in zip(answers, questions, strict=True)]
    score = sum(results)
    passed = score >= PASS_SCORE

    integrity = _assess_integrity(db, session, responses, now)
    topic = next((t for t in get_topics(domain) if t.id == session.topic_id), None)

    row = _locked_progress_row(db, user_id, session.topic_id)
    p_know_before = row.p_know
    p_know_after = p_know_before
    if integrity.counted:
        p_know_after = update_bkt_sequence(p_know_before, results, row.p_learn, row.p_guess, row.p_slip)[-1]
        row.p_know = p_know_after
        row.attempts += 1
        row.correct += score
        if passed:
            row.status = TopicStatus.COMPLETED.value
        elif row.status != TopicStatus.COMPLETED:
            # A failed retake never undoes a completion (ARCHITECTURE.md section 10: never relock).
            row.status = TopicStatus.IN_PROGRESS.value
        row.needs_attention = needs_attention(row.attempts, p_know_after)

    attempt = QuizAttempt(
        user_id=user_id,
        topic_id=session.topic_id,
        score=score,
        passed=passed,
        questions=questions,
        submitted_answers=answers,
        p_know_before=p_know_before,
        p_know_after=p_know_after,
    )
    db.add(attempt)
    db.flush()
    db.add(QuizIntegrity(
        session_id=session.id, attempt_id=attempt.id, score=integrity.score, verdict=integrity.verdict,
        counted=integrity.counted, reasons=integrity.reasons,
    ))
    session.submitted_at = now

    statuses_before = {tid: r.status for tid, r in get_progress_map(db, user_id).items()}
    frontier = sync_statuses(db, user_id, domain)
    progress = get_progress_map(db, user_id)
    newly_unlocked = sorted(
        tid
        for tid, r in progress.items()
        if r.status == TopicStatus.UNLOCKED and statuses_before.get(tid) != TopicStatus.UNLOCKED
    )

    struggling = not passed or row.needs_attention
    result = {
        "topic_id": session.topic_id,
        "score": score,
        "total": len(questions),
        "passed": passed,
        "p_know_before": p_know_before,
        "p_know_after": p_know_after,
        "mastered": mastery_reached(p_know_after),
        "status": row.status,
        "needs_attention": row.needs_attention,
        "feedback": [
            {
                "question": question["question"],
                "options": question["options"],
                "selected": answer,
                "correct": question["correct"],
                "is_correct": is_correct,
                "timed_out": bool(responses.get(index) and responses[index].timed_out),
                "explanation": question["explanation"],
            }
            for index, (question, answer, is_correct) in enumerate(zip(questions, answers, results, strict=True))
        ],
        "recommended_resources": topic.resources if (struggling and topic is not None) else [],
        "newly_unlocked": newly_unlocked,
        "next_topics": recommendations(frontier, progress),
        "integrity": {
            "score": integrity.score, "verdict": integrity.verdict, "counted": integrity.counted,
            "reasons": integrity.reasons,
        },
    }
    db.commit()
    logger.info(
        "Quiz %s submitted by user id=%s: %s %d/%d, integrity %d (%s), p_know %.3f -> %.3f%s",
        quiz_id, user_id, session.topic_id, score, len(questions), integrity.score, integrity.verdict,
        p_know_before, p_know_after, " (needs attention)" if row.needs_attention else "",
    )
    return result


def _locked_progress_row(db: Session, user_id: int, topic_id: str) -> TopicProgress:
    query = (
        select(TopicProgress)
        .where(TopicProgress.user_id == user_id, TopicProgress.topic_id == topic_id)
        .with_for_update()
    )
    row = db.scalar(query)
    if row is None:
        # Rows are created when the quiz is generated; this only guards against manual deletion.
        ensure_progress_rows(db, user_id, [topic_id])
        row = db.scalar(query)
    return row
