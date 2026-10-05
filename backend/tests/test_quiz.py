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
from sqlalchemy import select

from config import get_settings
from models import QuizSession, TopicProgress
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
