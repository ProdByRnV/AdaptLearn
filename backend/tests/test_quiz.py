"""Quiz generation tests: LLM output validation, retries/fallback, answer-key security.

The Groq call is always replaced by a fake (see conftest.no_real_groq), so these tests are
fast, free and deterministic. Phase 11 adds the submission tests to this file.
"""

import json
from collections import Counter
from datetime import datetime, timedelta, timezone

import groq
import httpx
import pytest
from neo4j.exceptions import ServiceUnavailable
from sqlalchemy import select

from config import get_settings
from models import QuizAttempt, QuizSession, TopicProgress
from schemas.quiz import QuizContent, QuizQuestion
from seed.curriculum import TOPICS
from seed.fallback_questions import FALLBACK_QUESTIONS
from services import llm_quiz
from services.llm_quiz import InvalidQuizOutput, generate_questions, parse_quiz
from services.quiz_service import shuffle_options
from services.topic_service import TopicInfo

TOPIC = TopicInfo("async_javascript", "Async JavaScript", "Promises and async/await.", 3)
ROOT = "git_basics"


# --- Helpers ------------------------------------------------------------------------

def make_question(n: int, **overrides) -> dict:
    q = {
        "question": f"Sample question number {n}?",
        "options": [f"Right answer {n}", f"Wrong A{n}", f"Wrong B{n}", f"Wrong C{n}"],
        "correct": 0,
        "explanation": f"Because answer {n} is right.",
    }
    q.update(overrides)
    return q


def quiz_json(*questions) -> str:
    return json.dumps({"questions": list(questions) or [make_question(i) for i in range(3)]})


VALID = quiz_json()


def api_status_error(status_code: int) -> groq.APIStatusError:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(status_code, request=request)
    return groq.APIStatusError(f"HTTP {status_code}", response=response, body=None)


def connection_error() -> groq.APIConnectionError:
    return groq.APIConnectionError(request=httpx.Request("POST", "https://api.groq.com"))


@pytest.fixture()
def fake_llm(monkeypatch):
    """Script the LLM: each call returns (or raises) the next item. Records the calls."""

    class Fake:
        def __init__(self):
            self.script: list = []
            self.calls: list = []

        def __call__(self, messages, timeout):
            self.calls.append({"messages": messages, "timeout": timeout})
            item = self.script.pop(0) if self.script else VALID
            if isinstance(item, Exception):
                raise item
            return item

    fake = Fake()
    monkeypatch.setattr(llm_quiz, "call_groq", fake)
    monkeypatch.setattr(get_settings(), "groq_api_key", "gsk_test_key")
    return fake


@pytest.fixture()
def no_api_key(monkeypatch):
    monkeypatch.setattr(get_settings(), "groq_api_key", "")


# --- parse_quiz: validation of model output ----------------------------------------------

def test_valid_output_is_accepted():
    questions = parse_quiz(VALID)
    assert len(questions) == 3
    assert questions[0].options[questions[0].correct] == "Right answer 0"


def test_accidental_code_fences_are_stripped():
    assert len(parse_quiz(f"```json\n{VALID}\n```")) == 3
    assert len(parse_quiz(f"```\n{VALID}\n```")) == 3


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        ("", "empty"),
        ("   ", "empty"),
        ("Here are your questions!", "not valid JSON"),
        ('{"questions": [', "not valid JSON"),
        (json.dumps([make_question(i) for i in range(3)]), "schema"),
        (quiz_json(make_question(0), make_question(1)), "schema"),
        (quiz_json(*[make_question(i) for i in range(4)]), "schema"),
        (quiz_json(make_question(0, options=["a", "b", "c"]), make_question(1), make_question(2)), "schema"),
        (quiz_json(make_question(0, options=["a", "b", "c", "d", "e"]), make_question(1), make_question(2)), "schema"),
        (quiz_json(make_question(0, correct=4), make_question(1), make_question(2)), "schema"),
        (quiz_json(make_question(0, correct=-1), make_question(1), make_question(2)), "schema"),
        (quiz_json(make_question(0, correct="1"), make_question(1), make_question(2)), "schema"),
        (quiz_json(make_question(0, correct=True), make_question(1), make_question(2)), "schema"),
        (quiz_json(make_question(0, correct=1.0), make_question(1), make_question(2)), "schema"),
        (quiz_json(make_question(0, question="  "), make_question(1), make_question(2)), "schema"),
        (quiz_json(make_question(0, options=["a", " ", "c", "d"]), make_question(1), make_question(2)), "schema"),
        (quiz_json(make_question(0, explanation=""), make_question(1), make_question(2)), "schema"),
        (quiz_json(make_question(0, options=["Yes", "yes ", "No", "Maybe"]), make_question(1), make_question(2)),
         "distinct"),
        (quiz_json(make_question(0), make_question(0), make_question(2)), "distinct"),
    ],
    ids=[
        "empty", "whitespace", "prose", "truncated-json", "top-level-list", "two-questions", "four-questions",
        "three-options", "five-options", "correct-4", "correct-negative", "correct-string", "correct-bool",
        "correct-float", "blank-question", "blank-option", "missing-explanation", "duplicate-options",
        "duplicate-questions",
    ],
)
def test_invalid_output_is_rejected(raw, reason):
    with pytest.raises(InvalidQuizOutput, match=reason):
        parse_quiz(raw)


def test_missing_field_is_rejected():
    q = make_question(0)
    del q["explanation"]
    with pytest.raises(InvalidQuizOutput):
        parse_quiz(quiz_json(q, make_question(1), make_question(2)))


# --- generate_questions: retries and fallback ---------------------------------------------

def test_valid_first_answer_uses_ai(fake_llm):
    result = generate_questions(TOPIC, "Web Development")
    assert result.source == "ai"
    assert len(fake_llm.calls) == 1


def test_prompt_contains_topic_details(fake_llm):
    generate_questions(TOPIC, "Web Development")
    system, user = fake_llm.calls[0]["messages"]
    assert system["role"] == "system" and "Return ONLY valid JSON" in system["content"]
    assert "exactly 3" in system["content"]
    for text in ("Web Development", "Async JavaScript", "Promises and async/await.", "3 of 4"):
        assert text in user["content"]


def test_invalid_output_is_retried(fake_llm):
    fake_llm.script = ["not json", VALID]
    result = generate_questions(TOPIC, "Web Development")
    assert result.source == "ai"
    assert len(fake_llm.calls) == 2


def test_two_retries_then_fallback(fake_llm):
    fake_llm.script = ["not json", "still not json", '{"questions": []}', VALID]
    result = generate_questions(TOPIC, "Web Development")
    assert result.source == "fallback"
    assert len(fake_llm.calls) == 3  # initial attempt + 2 retries, never a 4th
    assert [q.question for q in result.questions] == [q["question"] for q in FALLBACK_QUESTIONS[TOPIC.id]]


def test_groq_json_validation_400_is_retried(fake_llm):
    fake_llm.script = [api_status_error(400), VALID]
    result = generate_questions(TOPIC, "Web Development")
    assert result.source == "ai"
    assert len(fake_llm.calls) == 2


@pytest.mark.parametrize("error", [connection_error, lambda: api_status_error(401), lambda: api_status_error(429),
                                   lambda: api_status_error(503)])
def test_unavailable_groq_falls_back_without_retrying(fake_llm, error):
    fake_llm.script = [error()]
    result = generate_questions(TOPIC, "Web Development")
    assert result.source == "fallback"
    assert len(fake_llm.calls) == 1


def test_timeout_falls_back(fake_llm):
    fake_llm.script = [groq.APITimeoutError(request=httpx.Request("POST", "https://api.groq.com"))]
    assert generate_questions(TOPIC, "Web Development").source == "fallback"


def test_no_api_key_uses_fallback_without_calling_groq(no_api_key):
    # conftest.no_real_groq would raise if the LLM were called.
    result = generate_questions(TOPIC, "Web Development")
    assert result.source == "fallback"


def test_time_budget_stops_retries(fake_llm, monkeypatch):
    monkeypatch.setattr(llm_quiz, "TOTAL_BUDGET_SECONDS", 0.5)
    result = generate_questions(TOPIC, "Web Development")
    assert result.source == "fallback"
    assert fake_llm.calls == []


def test_request_timeout_never_exceeds_the_limit(fake_llm):
    generate_questions(TOPIC, "Web Development")
    assert 0 < fake_llm.calls[0]["timeout"] <= llm_quiz.REQUEST_TIMEOUT_SECONDS


def test_no_fallback_and_no_groq_returns_none(fake_llm, monkeypatch):
    monkeypatch.setitem(FALLBACK_QUESTIONS, TOPIC.id, [])
    fake_llm.script = [connection_error()]
    assert generate_questions(TOPIC, "Web Development") is None


# --- Fallback bank -----------------------------------------------------------------------

def test_fallback_bank_covers_exactly_the_curriculum():
    assert set(FALLBACK_QUESTIONS) == {t.id for t in TOPICS}


@pytest.mark.parametrize("topic_id", sorted(FALLBACK_QUESTIONS))
def test_fallback_questions_pass_the_same_validation_as_ai_output(topic_id):
    items = FALLBACK_QUESTIONS[topic_id]
    assert len(items) >= 3
    QuizContent.model_validate({"questions": items[:3]})


def test_fallback_questions_are_unique_across_the_bank():
    texts = [q["question"] for items in FALLBACK_QUESTIONS.values() for q in items]
    assert len(texts) == len(set(texts))


# --- Option shuffling ---------------------------------------------------------------------

def test_shuffle_keeps_the_correct_answer_text():
    question = QuizQuestion(**make_question(7, correct=2))
    for _ in range(50):
        shuffled = shuffle_options(question)
        assert sorted(shuffled["options"]) == sorted(question.options)
        assert shuffled["options"][shuffled["correct"]] == question.options[2]
        assert shuffled["explanation"] == question.explanation


def test_shuffle_spreads_the_answer_across_positions():
    question = QuizQuestion(**make_question(1))
    positions = Counter(shuffle_options(question)["correct"] for _ in range(400))
    assert set(positions) == {0, 1, 2, 3}
    assert min(positions.values()) > 40  # ~100 expected each


# --- GET /api/quiz/generate/{topic_id} --------------------------------------------------------

pytestmark_api = pytest.mark.usefixtures("curriculum")


def generate(client, headers, topic_id=ROOT):
    return client.get(f"/api/quiz/generate/{topic_id}", headers=headers)


def onboard(client, headers, topic_ids=()):
    client.post("/api/topics/mark-known", json={"topic_ids": list(topic_ids)}, headers=headers)


def progress_row(db, user_id, topic_id) -> TopicProgress:
    db.expire_all()
    return db.scalar(select(TopicProgress).where(TopicProgress.user_id == user_id, TopicProgress.topic_id == topic_id))


@pytestmark_api
def test_generate_requires_authentication(client):
    assert client.get(f"/api/quiz/generate/{ROOT}").status_code == 401


@pytestmark_api
def test_unknown_topic_returns_404(client, make_user, fake_llm):
    _, headers = make_user()
    response = generate(client, headers, "quantum_css")
    assert response.status_code == 404
    assert response.json() == {"detail": "Topic 'quantum_css' not found"}
    assert fake_llm.calls == []


@pytestmark_api
def test_locked_topic_returns_403(client, make_user, fake_llm):
    _, headers = make_user()
    onboard(client, headers)
    response = generate(client, headers, "react_fundamentals")
    assert response.status_code == 403
    assert response.json() == {"detail": "Topic is still locked. Complete its prerequisites first."}
    assert fake_llm.calls == []  # no LLM cost for a locked topic


@pytestmark_api
def test_response_has_three_sanitised_questions(client, make_user, fake_llm):
    _, headers = make_user()
    onboard(client, headers)
    response = generate(client, headers)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"quiz_id", "topic", "questions", "expires_in_seconds", "source"}
    assert body["topic"] == {"id": ROOT, "name": "Git Basics"}
    assert body["source"] == "ai"
    assert body["expires_in_seconds"] == get_settings().quiz_session_ttl_minutes * 60
    assert [q["id"] for q in body["questions"]] == [0, 1, 2]
    for q in body["questions"]:
        assert set(q) == {"id", "question", "options"}
        assert len(q["options"]) == 4


@pytestmark_api
def test_answer_key_is_never_in_the_response(client, make_user, fake_llm):
    _, headers = make_user()
    onboard(client, headers)
    text = generate(client, headers).text
    # No answer-key fields, and no explanation text (which would give the answer away).
    for leaked in ('"correct"', '"correct_answer"', '"answer"', '"explanation"', "Because answer"):
        assert leaked not in text


@pytestmark_api
def test_answer_key_is_stored_server_side(client, make_user, fake_llm, db):
    user_id, headers = make_user()
    onboard(client, headers)
    body = generate(client, headers).json()

    session = db.get(QuizSession, body["quiz_id"])
    assert session.user_id == user_id and session.topic_id == ROOT
    assert session.submitted_at is None
    for out, stored in zip(body["questions"], session.questions):
        assert out["options"] == stored["options"]
        assert stored["options"][stored["correct"]].startswith("Right answer")
        assert stored["explanation"]
    expected_expiry = datetime.now(timezone.utc) + timedelta(minutes=get_settings().quiz_session_ttl_minutes)
    assert abs((session.expires_at - expected_expiry).total_seconds()) < 10


@pytestmark_api
def test_unlocked_topic_becomes_in_progress(client, make_user, fake_llm, db):
    user_id, headers = make_user()
    onboard(client, headers)
    assert progress_row(db, user_id, ROOT).status == "unlocked"

    generate(client, headers)
    assert progress_row(db, user_id, ROOT).status == "in_progress"
    generate(client, headers)
    assert progress_row(db, user_id, ROOT).status == "in_progress"


@pytestmark_api
def test_completed_topic_can_be_retaken_and_stays_completed(client, make_user, fake_llm, db):
    user_id, headers = make_user()
    onboard(client, headers, [ROOT])
    response = generate(client, headers)
    assert response.status_code == 200
    assert progress_row(db, user_id, ROOT).status == "completed"


@pytestmark_api
def test_quiz_before_onboarding_initialises_progress(client, make_user, fake_llm, db):
    user_id, headers = make_user()
    response = generate(client, headers)

    assert response.status_code == 200
    db.expire_all()
    rows = db.scalars(select(TopicProgress).where(TopicProgress.user_id == user_id)).all()
    assert len(rows) == 30
    assert progress_row(db, user_id, ROOT).status == "in_progress"
    assert progress_row(db, user_id, "react_fundamentals").status == "locked"


@pytestmark_api
def test_groq_down_still_produces_a_quiz(client, make_user, fake_llm, db):
    """Phase 10 exit gate: the Groq-unavailable case."""
    user_id, headers = make_user()
    onboard(client, headers)
    fake_llm.script = [connection_error()]

    response = generate(client, headers)

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "fallback"
    assert len(body["questions"]) == 3
    assert '"correct"' not in response.text
    session = db.get(QuizSession, body["quiz_id"])
    fallback_texts = {q["question"] for q in FALLBACK_QUESTIONS[ROOT]}
    assert {q["question"] for q in session.questions} == fallback_texts


@pytestmark_api
def test_no_api_key_serves_fallback_quiz(client, make_user, no_api_key):
    _, headers = make_user()
    onboard(client, headers)
    body = generate(client, headers).json()
    assert body["source"] == "fallback"


@pytestmark_api
def test_no_questions_anywhere_returns_503(client, make_user, fake_llm, monkeypatch):
    _, headers = make_user()
    onboard(client, headers)
    monkeypatch.setitem(FALLBACK_QUESTIONS, ROOT, [])
    fake_llm.script = [connection_error()]

    response = generate(client, headers)

    assert response.status_code == 503
    assert response.json() == {"detail": "Quiz generation is temporarily unavailable. Please try again shortly."}


@pytestmark_api
def test_each_quiz_is_a_new_session(client, make_user, fake_llm):
    _, headers = make_user()
    onboard(client, headers)
    first, second = generate(client, headers).json(), generate(client, headers).json()
    assert first["quiz_id"] != second["quiz_id"]


# =====================================================================================
# POST /api/quiz/submit (Phase 11)
# =====================================================================================

SUBMIT_TOPIC = "html_basics"  # completing it unlocks css_basics and semantic_html


def start_quiz(client, headers, topic_id=SUBMIT_TOPIC) -> str:
    response = generate(client, headers, topic_id)
    assert response.status_code == 200, response.text
    return response.json()["quiz_id"]


def answer_key(db, quiz_id) -> list[int]:
    db.expire_all()
    return [q["correct"] for q in db.get(QuizSession, quiz_id).questions]


def answers_for(key: list[int], pattern: str) -> list[int]:
    """Pattern like CCW: correct, correct, wrong."""
    return [k if p == "C" else (k + 1) % 4 for k, p in zip(key, pattern)]


def submit(client, headers, quiz_id, answers):
    return client.post("/api/quiz/submit", json={"quiz_id": quiz_id, "answers": answers}, headers=headers)


def take_quiz(client, headers, db, pattern, topic_id=SUBMIT_TOPIC):
    quiz_id = start_quiz(client, headers, topic_id)
    return submit(client, headers, quiz_id, answers_for(answer_key(db, quiz_id), pattern))


def attempts_for(db, user_id) -> list[QuizAttempt]:
    db.expire_all()
    return db.scalars(select(QuizAttempt).where(QuizAttempt.user_id == user_id)).all()


@pytest.fixture()
def learner(client, make_user, fake_llm):
    """An onboarded learner (nothing known) with the LLM faked."""
    user_id, headers = make_user()
    onboard(client, headers)
    return user_id, headers


@pytestmark_api
def test_submit_requires_authentication(client):
    body = {"quiz_id": "00000000-0000-0000-0000-000000000000", "answers": [0, 0, 0]}
    assert client.post("/api/quiz/submit", json=body).status_code == 401


@pytestmark_api
def test_perfect_quiz_passes_masters_and_unlocks(client, learner, db):
    _, headers = learner
    response = take_quiz(client, headers, db, "CCC")

    assert response.status_code == 200
    body = response.json()
    assert (body["topic_id"], body["score"], body["total"], body["passed"]) == (SUBMIT_TOPIC, 3, 3, True)
    assert body["p_know_before"] == pytest.approx(0.10)
    assert body["p_know_after"] == pytest.approx(0.9890160183, abs=1e-9)
    assert body["mastered"] is True
    assert body["status"] == "completed"
    assert body["needs_attention"] is False
    assert body["recommended_resources"] == []
    assert body["newly_unlocked"] == ["css_basics", "semantic_html"]
    assert [t["id"] for t in body["next_topics"]] == ["css_basics", "git_basics", "javascript_fundamentals"]


@pytestmark_api
def test_feedback_reveals_answers_and_explanations_after_submission(client, learner, db):
    _, headers = learner
    quiz_id = start_quiz(client, headers)
    key = answer_key(db, quiz_id)
    answers = answers_for(key, "CWC")

    feedback = submit(client, headers, quiz_id, answers).json()["feedback"]

    assert [f["selected"] for f in feedback] == answers
    assert [f["correct"] for f in feedback] == key
    assert [f["is_correct"] for f in feedback] == [True, False, True]
    for item in feedback:
        assert len(item["options"]) == 4 and item["question"] and item["explanation"].startswith("Because")


@pytestmark_api
def test_submission_persists_progress_attempt_and_session(client, learner, db):
    """ARCHITECTURE 23: successful submission writes attempt and progress."""
    user_id, headers = learner
    quiz_id = start_quiz(client, headers)
    key = answer_key(db, quiz_id)
    submit(client, headers, quiz_id, answers_for(key, "CCW"))

    row = progress_row(db, user_id, SUBMIT_TOPIC)
    assert (row.status, row.attempts, row.correct) == ("completed", 1, 2)
    assert row.p_know == pytest.approx(0.7589958159, abs=1e-9)

    (attempt,) = attempts_for(db, user_id)
    assert (attempt.topic_id, attempt.score, attempt.passed) == (SUBMIT_TOPIC, 2, True)
    assert attempt.submitted_answers == answers_for(key, "CCW")
    assert attempt.p_know_before == pytest.approx(0.10)
    assert attempt.p_know_after == pytest.approx(0.7589958159, abs=1e-9)
    assert [q["correct"] for q in attempt.questions] == key  # full snapshot for history

    assert db.get(QuizSession, quiz_id).submitted_at is not None


@pytest.mark.parametrize(
    ("pattern", "expected_after", "passed"),
    [
        ("CCC", 0.9890160183, True),
        ("CCW", 0.7589958159, True),
        ("WCC", 0.9780068729, True),
        ("CWC", 0.8890173410, True),
        ("WWC", 0.8708761442, False),
        ("CWW", 0.4654292343, False),
        ("WWW", 0.4551879666, False),
    ],
)
@pytestmark_api
def test_bkt_is_applied_to_answers_in_order(client, learner, db, pattern, expected_after, passed):
    _, headers = learner
    body = take_quiz(client, headers, db, pattern).json()
    assert body["p_know_after"] == pytest.approx(expected_after, abs=1e-9)
    assert body["passed"] is passed
    assert body["score"] == pattern.count("C")


@pytestmark_api
def test_failed_quiz_keeps_topic_in_progress_and_recommends_resources(client, learner, db):
    user_id, headers = learner
    body = take_quiz(client, headers, db, "CWW").json()

    assert body["passed"] is False
    assert body["status"] == "in_progress"
    assert body["newly_unlocked"] == []
    html = next(t for t in TOPICS if t.id == SUBMIT_TOPIC)
    assert body["recommended_resources"] == [{"title": r.title, "url": r.url, "type": r.type} for r in html.resources]
    assert progress_row(db, user_id, "css_basics").status == "locked"


@pytestmark_api
def test_failed_retake_never_undoes_completion(client, make_user, fake_llm, db):
    user_id, headers = make_user()
    onboard(client, headers, [SUBMIT_TOPIC])  # completed at 0.95

    body = take_quiz(client, headers, db, "WWW").json()

    assert body["passed"] is False
    assert body["status"] == "completed"
    assert body["p_know_after"] < 0.95
    assert progress_row(db, user_id, SUBMIT_TOPIC).status == "completed"
    assert progress_row(db, user_id, "css_basics").status == "unlocked"


@pytestmark_api
def test_needs_attention_after_more_than_two_poor_attempts_then_clears(client, learner, db):
    user_id, headers = learner

    first = take_quiz(client, headers, db, "WWW").json()
    second = take_quiz(client, headers, db, "WWW").json()
    assert first["needs_attention"] is False and second["needs_attention"] is False  # attempts not yet > 2

    third = take_quiz(client, headers, db, "WWW").json()
    assert third["needs_attention"] is True  # attempts 3, p_know ~0.455 < 0.50
    assert third["recommended_resources"]
    assert progress_row(db, user_id, SUBMIT_TOPIC).needs_attention is True

    recovered = take_quiz(client, headers, db, "CCC").json()
    assert recovered["needs_attention"] is False
    assert progress_row(db, user_id, SUBMIT_TOPIC).needs_attention is False


@pytestmark_api
def test_counters_accumulate_across_attempts(client, learner, db):
    user_id, headers = learner
    take_quiz(client, headers, db, "CWW")
    take_quiz(client, headers, db, "CCW")
    row = progress_row(db, user_id, SUBMIT_TOPIC)
    assert (row.attempts, row.correct) == (2, 3)
    assert len(attempts_for(db, user_id)) == 2


@pytestmark_api
def test_submission_changes_progress_and_recommendations(client, learner, db):
    """Phase 11 exit gate."""
    _, headers = learner
    path_before = client.get("/api/topics/learning-path", headers=headers).json()["recommended"]
    assert [t["id"] for t in path_before] == ["git_basics", "html_basics", "javascript_fundamentals"]

    body = take_quiz(client, headers, db, "CCC").json()

    path_after = client.get("/api/topics/learning-path", headers=headers).json()["recommended"]
    assert [t["id"] for t in path_after] == ["css_basics", "git_basics", "javascript_fundamentals"]
    assert path_after == body["next_topics"]
    nodes = {n["id"]: n for n in client.get("/api/topics/graph", headers=headers).json()["nodes"]}
    assert (nodes[SUBMIT_TOPIC]["status"], nodes[SUBMIT_TOPIC]["mastered"]) == ("completed", True)
    assert nodes["semantic_html"]["status"] == "unlocked"


@pytestmark_api
def test_another_users_quiz_is_not_found_and_left_untouched(client, make_user, fake_llm, db):
    """ARCHITECTURE 23: wrong user's quiz submission rejected."""
    _, owner = make_user("owner@example.com")
    _, intruder = make_user("intruder@example.com")
    onboard(client, owner)
    quiz_id = start_quiz(client, owner)
    key = answer_key(db, quiz_id)

    response = submit(client, intruder, quiz_id, key)

    assert response.status_code == 404
    assert response.json() == {"detail": "Quiz not found"}
    assert db.get(QuizSession, quiz_id).submitted_at is None
    assert submit(client, owner, quiz_id, key).status_code == 200


@pytestmark_api
def test_unknown_quiz_returns_404(client, learner):
    _, headers = learner
    response = submit(client, headers, "11111111-2222-3333-4444-555555555555", [0, 1, 2])
    assert response.status_code == 404


@pytestmark_api
def test_expired_quiz_is_rejected(client, learner, db):
    """ARCHITECTURE 23: expired quiz rejected."""
    user_id, headers = learner
    quiz_id = start_quiz(client, headers)
    session = db.get(QuizSession, quiz_id)
    session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()

    response = submit(client, headers, quiz_id, [0, 0, 0])

    assert response.status_code == 410
    assert response.json() == {"detail": "This quiz has expired. Start a new quiz for this topic."}
    assert attempts_for(db, user_id) == []
    assert progress_row(db, user_id, SUBMIT_TOPIC).attempts == 0


@pytestmark_api
def test_second_submission_is_rejected(client, learner, db):
    """ARCHITECTURE 23: second submission rejected."""
    user_id, headers = learner
    quiz_id = start_quiz(client, headers)
    key = answer_key(db, quiz_id)
    assert submit(client, headers, quiz_id, key).status_code == 200

    response = submit(client, headers, quiz_id, key)

    assert response.status_code == 409
    assert response.json() == {"detail": "This quiz has already been submitted"}
    assert len(attempts_for(db, user_id)) == 1
    assert progress_row(db, user_id, SUBMIT_TOPIC).attempts == 1


@pytest.mark.parametrize(
    "answers",
    [[0, 1], [0, 1, 2, 3], [0, 1, 4], [0, -1, 2], ["0", 1, 2], [True, 1, 2], [0.0, 1, 2], None],
    ids=["two", "four", "index-4", "negative", "string", "bool", "float", "missing"],
)
@pytestmark_api
def test_invalid_answers_are_rejected(client, learner, db, answers):
    _, headers = learner
    quiz_id = start_quiz(client, headers)
    body = {"quiz_id": quiz_id} if answers is None else {"quiz_id": quiz_id, "answers": answers}

    response = client.post("/api/quiz/submit", json=body, headers=headers)

    assert response.status_code == 422
    assert db.get(QuizSession, quiz_id).submitted_at is None


@pytestmark_api
def test_malformed_quiz_id_is_rejected(client, learner):
    _, headers = learner
    assert submit(client, headers, "not-a-uuid", [0, 1, 2]).status_code == 422


@pytestmark_api
def test_failure_midway_saves_nothing_and_allows_resubmission(client, learner, db, monkeypatch):
    """Neo4j dies after progress was updated in memory: the whole submission rolls back."""
    from db import neo4j_db

    user_id, headers = learner
    quiz_id = start_quiz(client, headers)
    key = answer_key(db, quiz_id)

    real_read, calls = neo4j_db.read, []

    def flaky_read(*args, **kwargs):
        calls.append(1)
        if len(calls) >= 2:  # 1st read: topic lookup; 2nd: frontier, after the progress changes
            raise ServiceUnavailable("Neo4j went away")
        return real_read(*args, **kwargs)

    monkeypatch.setattr(neo4j_db, "read", flaky_read)
    response = submit(client, headers, quiz_id, key)
    assert response.status_code == 503

    assert db.get(QuizSession, quiz_id).submitted_at is None
    assert attempts_for(db, user_id) == []
    row = progress_row(db, user_id, SUBMIT_TOPIC)
    assert (row.status, row.attempts, row.p_know) == ("in_progress", 0, pytest.approx(0.10))

    monkeypatch.setattr(neo4j_db, "read", real_read)
    assert submit(client, headers, quiz_id, key).status_code == 200
