"""Quiz sessions: generation (this phase) and submission (Phase 11).

The full questions, including the answer key, are stored server-side in quiz_sessions.
The browser only ever receives question text and options (ARCHITECTURE.md section 15).
"""

import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import get_settings
from models import QuizAttempt, QuizSession, TopicProgress, TopicStatus
from schemas.quiz import QuizQuestion
from seed.curriculum import DOMAIN, DOMAIN_NAME
from services.bkt import mastery_reached, update_bkt_sequence
from services.learning_path import ensure_progress_rows, recommendations, sync_statuses
from services.llm_quiz import generate_questions
from services.topic_service import get_progress_map, get_topics

logger = logging.getLogger("adaptlearn")

_rng = random.SystemRandom()


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


PASS_SCORE = 2  # PRD 6.2: pass with at least 2 of 3


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

    generated = generate_questions(topic, DOMAIN_NAME)
    if generated is None:
        raise QuizUnavailableError(topic_id)

    ttl_minutes = get_settings().quiz_session_ttl_minutes
    session = QuizSession(
        user_id=user_id,
        topic_id=topic_id,
        questions=[shuffle_options(q) for q in generated.questions],
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes),
    )
    db.add(session)
    if row.status == TopicStatus.UNLOCKED:
        row.status = TopicStatus.IN_PROGRESS.value  # decision 2
    db.commit()
    logger.info("Quiz %s created for user id=%s topic=%s (%s)", session.id, user_id, topic_id, generated.source)

    return {
        "quiz_id": session.id,
        "topic": {"id": topic.id, "name": topic.name},
        # Sanitised: no answer index and no explanation until submission.
        "questions": [
            {"id": index, "question": q["question"], "options": q["options"]}
            for index, q in enumerate(session.questions)
        ],
        "expires_in_seconds": ttl_minutes * 60,
        "source": generated.source,
    }


def submit_quiz(db: Session, user_id: int, quiz_id: UUID, answers: list[int], domain: str = DOMAIN) -> dict[str, Any]:
    """Score a quiz server-side and update the learner's progress (ARCHITECTURE.md 13.9 and 15).

    Everything happens in one transaction: if any step fails (e.g. Neo4j is down) nothing is
    saved and the session can be submitted again.
    """
    # Lock the session row so two simultaneous submits can't both score it.
    session = db.scalar(
        select(QuizSession).where(QuizSession.id == quiz_id, QuizSession.user_id == user_id).with_for_update()
    )
    if session is None:
        raise QuizNotFoundError(quiz_id)  # also for another user's quiz: don't reveal that it exists
    if session.submitted_at is not None:
        raise QuizAlreadySubmittedError(quiz_id)
    now = datetime.now(timezone.utc)
    if session.expires_at <= now:
        raise QuizExpiredError(quiz_id)

    questions = session.questions
    results = [answer == question["correct"] for answer, question in zip(answers, questions, strict=True)]
    score = sum(results)
    passed = score >= PASS_SCORE

    topic = next((t for t in get_topics(domain) if t.id == session.topic_id), None)

    row = _locked_progress_row(db, user_id, session.topic_id)
    p_know_before = row.p_know
    trajectory = update_bkt_sequence(p_know_before, results, row.p_learn, row.p_guess, row.p_slip)
    p_know_after = trajectory[-1]

    row.p_know = p_know_after
    row.attempts += 1
    row.correct += score
    if passed:
        row.status = TopicStatus.COMPLETED.value
    elif row.status != TopicStatus.COMPLETED:
        # A failed retake never undoes a completion (ARCHITECTURE.md section 10: never relock).
        row.status = TopicStatus.IN_PROGRESS.value
    row.needs_attention = needs_attention(row.attempts, p_know_after)

    db.add(
        QuizAttempt(
            user_id=user_id,
            topic_id=session.topic_id,
            score=score,
            passed=passed,
            questions=questions,
            submitted_answers=list(answers),
            p_know_before=p_know_before,
            p_know_after=p_know_after,
        )
    )
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
                "explanation": question["explanation"],
            }
            for question, answer, is_correct in zip(questions, answers, results)
        ],
        "recommended_resources": topic.resources if (struggling and topic is not None) else [],
        "newly_unlocked": newly_unlocked,
        "next_topics": recommendations(frontier, progress),
    }
    db.commit()
    logger.info(
        "Quiz %s submitted by user id=%s: %s %d/%d, p_know %.3f -> %.3f%s",
        quiz_id, user_id, session.topic_id, score, len(questions), p_know_before, p_know_after,
        " (needs attention)" if row.needs_attention else "",
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
