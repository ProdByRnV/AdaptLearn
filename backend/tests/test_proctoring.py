"""Proctoring (Phase 12.5): integrity scoring, one-question-at-a-time delivery with deadlines,
integrity events, rate limits, the single active quiz, and flagged attempts not counting."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from config import get_settings
from models import ProctoringEvent, QuizAttempt, QuizIntegrity, QuizSession, TopicProgress
from services import proctoring, quiz_service
from services.proctoring import AnswerTiming, heartbeat_gaps, score_integrity

T0 = datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc)


def at(seconds: float) -> datetime:
    return T0 + timedelta(seconds=seconds)


def steady_heartbeats(until: float, every: float = 5) -> list[datetime]:
    return [at(s) for s in range(int(every), int(until) + 1, int(every))]


def clean_answers() -> list[AnswerTiming]:
    return [AnswerTiming(at(0), at(10)), AnswerTiming(at(12), at(22)), AnswerTiming(at(24), at(34))]


def score(events=(), heartbeats=None, answers=None, start=0, end=34):
    return score_integrity(
        events,
        steady_heartbeats(end) if heartbeats is None else heartbeats,
        clean_answers() if answers is None else answers,
        at(start),
        at(end),
    )


# =====================================================================================
# Pure scoring
# =====================================================================================

def test_clean_attempt_is_verified_with_full_score():
    result = score()
    assert (result.score, result.verdict, result.counted, result.reasons) == (100, "verified", True, [])


@pytest.mark.parametrize(
    ("event", "penalty"),
    [("tab_hidden", 10), ("window_blur", 5), ("fullscreen_exit", 15), ("copy_attempt", 10),
     ("paste_attempt", 10), ("context_menu", 5), ("multiple_screens", 20)],
)
def test_each_browser_event_costs_its_penalty(event, penalty):
    result = score([event])
    assert result.score == 100 - penalty
    assert result.reasons == [{"code": event, "count": 1, "penalty": penalty, "message": proctoring.RULES[event].message}]


def test_repeated_events_add_up_but_once_rules_do_not():
    assert score(["tab_hidden"] * 3).score == 70
    assert score(["multiple_screens"] * 4).score == 80


def test_threshold_boundary():
    at_threshold = score(["fullscreen_exit", "window_blur"])  # -20 -> 80
    below = score(["fullscreen_exit", "window_blur", "context_menu"])  # -25 -> 75
    assert (at_threshold.score, at_threshold.verdict, at_threshold.counted) == (80, "verified", True)
    assert (below.score, below.verdict, below.counted) == (75, "flagged", False)


def test_fast_answers_are_penalised():
    answers = [AnswerTiming(at(0), at(1)), AnswerTiming(at(5), at(7.9)), AnswerTiming(at(10), at(13))]
    result = score(answers=answers, end=13)
    assert result.score == 80  # two answers under 3 s; exactly 3 s is fine
    assert result.reasons[0]["code"] == "fast_answer" and result.reasons[0]["count"] == 2


def test_no_heartbeat_means_monitoring_missing_and_flags_the_attempt():
    result = score(heartbeats=[])
    assert (result.score, result.verdict) == (50, "flagged")
    assert result.reasons[0]["code"] == "monitoring_missing"


def test_heartbeat_gap_detection():
    assert heartbeat_gaps([at(5), at(20)], at(0), at(25)) == 0  # gaps of 5, 15, 5: 15 s is allowed
    assert heartbeat_gaps([at(5), at(21)], at(0), at(25)) == 1  # 16 s gap
    assert heartbeat_gaps([at(5)], at(0), at(40)) == 1  # silence until the end of the window
    assert heartbeat_gaps([at(100)], at(0), at(40)) == 1  # heartbeats outside the window don't help
    assert heartbeat_gaps([], at(0), at(0)) == 0


def test_heartbeat_gaps_are_penalised_each():
    # Gaps: 0->5 (5 s), 5->25 (20 s), 25->45 (20 s), 45->60 (15 s, allowed) = two penalised gaps.
    result = score(heartbeats=[at(5), at(25), at(45)], end=60)
    assert result.score == 70
    assert result.reasons == [{"code": "heartbeat_gap", "count": 2, "penalty": 30,
                               "message": proctoring.RULES["heartbeat_gap"].message}]


def test_reasons_are_sorted_by_penalty_and_score_never_negative():
    result = score(["tab_hidden"] * 20 + ["context_menu"])
    assert result.score == 0
    assert [r["code"] for r in result.reasons] == ["tab_hidden", "context_menu"]


def test_proctoring_module_imports_no_database_code():
    import subprocess
    import sys
    from pathlib import Path

    code = "import sys, services.proctoring; print([m for m in ('sqlalchemy','fastapi','db','models') if m in sys.modules])"
    out = subprocess.run([sys.executable, "-c", code], cwd=Path(__file__).resolve().parent.parent,
                         capture_output=True, text=True, check=True).stdout.strip()
    assert out == "[]"


# =====================================================================================
# API flow
# =====================================================================================

pytestmark_api = pytest.mark.usefixtures("curriculum", "fake_llm")
TOPIC = "html_basics"


@pytest.fixture()
def learner(client, make_user):
    user_id, headers = make_user()
    client.post("/api/topics/mark-known", json={"topic_ids": []}, headers=headers)
    return user_id, headers


def start(client, headers, topic=TOPIC) -> str:
    response = client.get(f"/api/quiz/generate/{topic}", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["quiz_id"]


def nxt(client, headers, quiz_id):
    return client.post(f"/api/quiz/{quiz_id}/next", headers=headers)


def answer(client, headers, quiz_id, question_id, value=0):
    return client.post(f"/api/quiz/{quiz_id}/answer", json={"question_id": question_id, "answer": value}, headers=headers)


def events(client, headers, quiz_id, *types):
    return client.post(f"/api/quiz/{quiz_id}/events", json={"events": [{"type": t} for t in types]}, headers=headers)


def progress(db, user_id, topic=TOPIC) -> TopicProgress:
    db.expire_all()
    return db.scalar(select(TopicProgress).where(TopicProgress.user_id == user_id, TopicProgress.topic_id == topic))


# --- One question at a time ---------------------------------------------------------------

@pytestmark_api
def test_questions_are_served_one_at_a_time(client, learner, clock):
    _, headers = learner
    quiz_id = start(client, headers)

    first = nxt(client, headers, quiz_id).json()
    assert (first["question_id"], first["number"], first["total"]) == (0, 1, 3)
    assert len(first["options"]) == 4 and first["seconds_remaining"] == get_settings().quiz_seconds_per_question

    # Asking again before answering returns the same question; q2 is not reachable yet.
    clock.advance(20)
    again = nxt(client, headers, quiz_id).json()
    assert again["question_id"] == 0 and again["question"] == first["question"]
    assert again["seconds_remaining"] == get_settings().quiz_seconds_per_question - 20  # reload doesn't reset the clock
    assert answer(client, headers, quiz_id, 1).status_code == 409


@pytestmark_api
def test_answers_lock_and_questions_cannot_be_reopened(client, learner, clock):
    _, headers = learner
    quiz_id = start(client, headers)
    nxt(client, headers, quiz_id)
    clock.advance(10)
    assert answer(client, headers, quiz_id, 0, 2).json() == {
        "question_id": 0, "accepted": True, "timed_out": False, "remaining_questions": 2,
    }
    assert answer(client, headers, quiz_id, 0, 3).status_code == 409  # can't change it
    assert nxt(client, headers, quiz_id).json()["question_id"] == 1  # moved on; q1 can't be served again


@pytestmark_api
def test_late_answer_is_refused_and_counts_as_wrong(client, learner, clock, db):
    user_id, headers = learner
    quiz_id = start(client, headers)
    nxt(client, headers, quiz_id)
    key = db.get(QuizSession, quiz_id).questions[0]["correct"]

    clock.advance(get_settings().quiz_seconds_per_question + quiz_service.ANSWER_GRACE_SECONDS + 1)
    ack = answer(client, headers, quiz_id, 0, key).json()

    assert (ack["accepted"], ack["timed_out"]) == (False, True)


@pytestmark_api
def test_answer_within_grace_period_is_accepted(client, learner, clock):
    _, headers = learner
    quiz_id = start(client, headers)
    nxt(client, headers, quiz_id)
    clock.advance(get_settings().quiz_seconds_per_question + quiz_service.ANSWER_GRACE_SECONDS)
    assert answer(client, headers, quiz_id, 0).json()["accepted"] is True


@pytestmark_api
def test_unanswered_overdue_question_is_closed_when_the_next_is_requested(client, learner, clock):
    _, headers = learner
    quiz_id = start(client, headers)
    nxt(client, headers, quiz_id)
    clock.advance(get_settings().quiz_seconds_per_question + 10)
    assert nxt(client, headers, quiz_id).json()["question_id"] == 1
    assert answer(client, headers, quiz_id, 0).status_code == 409


@pytestmark_api
def test_next_after_last_question_says_submit(client, learner, clock):
    _, headers = learner
    quiz_id = start(client, headers)
    for index in range(3):
        nxt(client, headers, quiz_id)
        clock.advance(10)
        answer(client, headers, quiz_id, index)
    response = nxt(client, headers, quiz_id)
    assert response.status_code == 409
    assert response.json() == {"detail": "All questions have been answered. Submit the quiz."}


@pytestmark_api
def test_submitting_early_counts_unseen_questions_as_wrong(client, learner, clock, db):
    _, headers = learner
    quiz_id = start(client, headers)
    key = db.get(QuizSession, quiz_id).questions[0]["correct"]
    nxt(client, headers, quiz_id)
    for _ in range(2):
        clock.advance(5)
        events(client, headers, quiz_id, "heartbeat")
    answer(client, headers, quiz_id, 0, key)

    body = client.post("/api/quiz/submit", json={"quiz_id": quiz_id}, headers=headers).json()

    assert body["score"] == 1
    assert [f["selected"] for f in body["feedback"]][1:] == [None, None]


# --- Integrity consequences -----------------------------------------------------------------

@pytestmark_api
def test_flagged_attempt_is_recorded_but_changes_nothing(learner, quiz_taker, db):
    """Owner decision: a flagged attempt doesn't count."""
    user_id, headers = learner
    before = progress(db, user_id)

    body = quiz_taker(headers, TOPIC, "CCC", events=[{"type": "fullscreen_exit"}, {"type": "paste_attempt"}])

    assert body["integrity"]["verdict"] == "flagged" and body["integrity"]["counted"] is False
    assert body["integrity"]["score"] == 75
    assert {r["code"] for r in body["integrity"]["reasons"]} == {"fullscreen_exit", "paste_attempt"}
    assert body["score"] == 3 and body["passed"] is True  # the answers were right...
    assert body["p_know_after"] == body["p_know_before"] == pytest.approx(0.10)  # ...but nothing changed
    assert body["newly_unlocked"] == [] and body["status"] == "in_progress"
    after = progress(db, user_id)
    assert (after.p_know, after.attempts, after.correct) == (before.p_know, before.attempts, before.correct)
    assert progress(db, user_id, "css_basics").status == "locked"

    attempt = db.scalar(select(QuizAttempt).where(QuizAttempt.user_id == user_id))
    integrity = db.scalar(select(QuizIntegrity).where(QuizIntegrity.attempt_id == attempt.id))
    assert (integrity.verdict, integrity.counted, integrity.score) == ("flagged", False, 75)


@pytestmark_api
def test_minor_events_still_verify_and_count(learner, quiz_taker, db):
    user_id, headers = learner
    body = quiz_taker(headers, TOPIC, "CCC", events=[{"type": "window_blur"}, {"type": "context_menu"}])
    assert body["integrity"] == {
        "score": 90, "verdict": "verified", "counted": True,
        "reasons": [
            {"code": "context_menu", "count": 1, "penalty": 5, "message": proctoring.RULES["context_menu"].message},
            {"code": "window_blur", "count": 1, "penalty": 5, "message": proctoring.RULES["window_blur"].message},
        ],
    }
    assert progress(db, user_id).status == "completed"


@pytestmark_api
def test_quiz_without_monitoring_is_flagged(learner, quiz_taker, db):
    user_id, headers = learner
    body = quiz_taker(headers, TOPIC, "CCC", heartbeats=False)
    assert body["integrity"]["verdict"] == "flagged"
    assert body["integrity"]["reasons"][0]["code"] == "monitoring_missing"
    assert progress(db, user_id).status == "in_progress"


@pytestmark_api
def test_answering_too_fast_is_flagged(learner, quiz_taker):
    _, headers = learner
    body = quiz_taker(headers, TOPIC, "CCC", seconds=1)
    assert body["integrity"]["score"] == 70
    assert body["integrity"]["reasons"][0] == {
        "code": "fast_answer", "count": 3, "penalty": 30, "message": proctoring.RULES["fast_answer"].message,
    }


@pytestmark_api
def test_dashboard_reports_flagged_attempts(client, learner, quiz_taker):
    _, headers = learner
    quiz_taker(headers, TOPIC, "CCC", heartbeats=False)
    quiz_taker(headers, TOPIC, "CCC")

    body = client.get("/api/progress/dashboard", headers=headers).json()

    assert (body["stats"]["total_attempts"], body["stats"]["flagged_attempts"]) == (2, 1)
    newest, older = body["recent_attempts"][:2]
    assert (newest["counted"], newest["integrity_verdict"], newest["integrity_score"]) == (True, "verified", 100)
    assert (older["counted"], older["integrity_verdict"]) == (False, "flagged")


# --- Events endpoint ------------------------------------------------------------------------

@pytestmark_api
def test_events_are_stored_with_server_time(client, learner, clock, db):
    _, headers = learner
    quiz_id = start(client, headers)
    response = client.post(
        f"/api/quiz/{quiz_id}/events",
        json={"events": [{"type": "tab_hidden", "duration_ms": 4200, "occurred_at": "2000-01-01T00:00:00Z"},
                         {"type": "heartbeat"}]},
        headers=headers,
    )
    assert response.json() == {"accepted": 2, "ignored": 0}
    stored = db.scalars(select(ProctoringEvent).where(ProctoringEvent.session_id == quiz_id)).all()
    tab = next(e for e in stored if e.event_type == "tab_hidden")
    assert tab.duration_ms == 4200
    assert tab.received_at == clock.now  # trusted server time, not the page's claim


@pytest.mark.parametrize(
    "body",
    [{"events": [{"type": "teleported"}]}, {"events": []}, {"events": [{"type": "heartbeat"}] * 101},
     {"events": [{"type": "tab_hidden", "duration_ms": -1}]}, {}],
    ids=["unknown-type", "empty", "too-many", "negative-duration", "missing"],
)
@pytestmark_api
def test_invalid_event_batches_are_rejected(client, learner, body):
    _, headers = learner
    quiz_id = start(client, headers)
    assert client.post(f"/api/quiz/{quiz_id}/events", json=body, headers=headers).status_code == 422


@pytestmark_api
def test_events_beyond_the_per_quiz_limit_are_ignored(client, learner, monkeypatch):
    _, headers = learner
    monkeypatch.setattr(quiz_service, "MAX_EVENTS_PER_SESSION", 3)
    quiz_id = start(client, headers)
    assert events(client, headers, quiz_id, "heartbeat", "heartbeat").json() == {"accepted": 2, "ignored": 0}
    assert events(client, headers, quiz_id, "heartbeat", "heartbeat").json() == {"accepted": 1, "ignored": 1}


@pytestmark_api
def test_events_after_submission_are_rejected(client, learner, clock):
    _, headers = learner
    quiz_id = start(client, headers)
    client.post("/api/quiz/submit", json={"quiz_id": quiz_id}, headers=headers)
    assert events(client, headers, quiz_id, "heartbeat").status_code == 409


# --- Rate limits ----------------------------------------------------------------------------

@pytestmark_api
def test_topic_rate_limit_returns_429_before_calling_the_llm(client, learner, clock, fake_llm):
    _, headers = learner
    for _ in range(get_settings().quiz_max_per_topic_per_hour):
        start(client, headers)
        clock.advance(60)
    calls_before = len(fake_llm.calls)

    response = client.get(f"/api/quiz/generate/{TOPIC}", headers=headers)

    assert response.status_code == 429
    assert "for this topic" in response.json()["detail"]
    retry_after = int(response.headers["retry-after"])
    assert 0 < retry_after <= 3600
    assert len(fake_llm.calls) == calls_before
    assert start(client, headers, "git_basics")  # other topics are still allowed

    clock.advance(retry_after + 1)
    assert client.get(f"/api/quiz/generate/{TOPIC}", headers=headers).status_code == 200


@pytestmark_api
def test_overall_rate_limit(client, learner, clock, monkeypatch):
    _, headers = learner
    monkeypatch.setattr(get_settings(), "quiz_max_per_hour", 2)
    start(client, headers, "html_basics")
    start(client, headers, "git_basics")
    frontend = {**headers, "Origin": get_settings().cors_origins[0]}
    response = client.get("/api/quiz/generate/sql_basics", headers=frontend)
    assert response.status_code == 429
    assert "overall" in response.json()["detail"]
    # The browser may read Retry-After from the cross-origin 429.
    assert int(response.headers["retry-after"]) > 0
    assert "retry-after" in response.headers["access-control-expose-headers"].lower()


# --- One active quiz --------------------------------------------------------------------------

@pytestmark_api
def test_active_quiz_can_be_resumed(client, learner, clock):
    _, headers = learner
    assert client.get("/api/quiz/active", headers=headers).json() == {"active": None}

    quiz_id = start(client, headers)
    nxt(client, headers, quiz_id)
    clock.advance(10)
    answer(client, headers, quiz_id, 0)

    active = client.get("/api/quiz/active", headers=headers).json()["active"]
    assert active["quiz_id"] == quiz_id
    assert (active["answered_questions"], active["total_questions"], active["source"]) == (1, 3, None)
    assert active["topic"] == {"id": TOPIC, "name": "HTML Basics"}


@pytestmark_api
def test_starting_a_new_quiz_abandons_the_old_one(client, learner, db):
    user_id, headers = learner
    old = start(client, headers)
    new = start(client, headers, "git_basics")

    assert client.post("/api/quiz/submit", json={"quiz_id": old}, headers=headers).status_code == 409
    integrity = db.get(QuizIntegrity, old)
    assert (integrity.verdict, integrity.counted, integrity.attempt_id) == ("abandoned", False, None)
    assert client.get("/api/quiz/active", headers=headers).json()["active"]["quiz_id"] == new
    assert db.scalars(select(QuizAttempt).where(QuizAttempt.user_id == user_id)).all() == []


@pytestmark_api
def test_expired_quiz_is_not_active(client, learner, clock):
    _, headers = learner
    start(client, headers)
    clock.advance(get_settings().quiz_session_ttl_minutes * 60 + 1)
    assert client.get("/api/quiz/active", headers=headers).json() == {"active": None}
