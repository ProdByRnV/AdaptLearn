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
from models import QuizAttempt, QuizIntegrity, QuizSession, TopicProgress
from schemas.quiz import QuizContent, QuizQuestion
from seed.curriculum import TOPICS
from seed.fallback_questions import FALLBACK_QUESTIONS, merge
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


# fake_llm (scripted LLM) comes from conftest.py; its default quiz equals VALID.


def test_conftest_default_quiz_matches_valid():
    from conftest import sample_quiz_json

    assert json.loads(sample_quiz_json()) == json.loads(VALID)


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
        (quiz_json(make_question(0, options=["Yes", "Yes  ", "No", "Maybe"]), make_question(1), make_question(2)),
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


@pytest.mark.parametrize("options", [["D", "A", "B", "C"], ["a)", "(b)", "C.", "d:"]])
def test_options_that_only_name_letters_are_rejected(options):
    # The page shows its own A-D labels, so "C: B" would be unreadable.
    q = make_question(0, question="Which is most specific? A) p B) #main C) .x D) div", options=options)
    with pytest.raises(InvalidQuizOutput, match="not letters"):
        parse_quiz(quiz_json(q, make_question(1), make_question(2)))


@pytest.mark.parametrize(
    ("options", "correct", "kept", "key"),
    [
        # Seen in Phase 27 samples: a blank fifth option failed a sound question.
        (["W", "X", "Y", "Z", ""], 0, ["W", "X", "Y", "Z"], 0),
        (["", "W", "X", "  ", "Y", "Z"], 4, ["W", "X", "Y", "Z"], 2),  # the key still names "Y"
    ],
)
def test_blank_extra_options_are_dropped_and_the_key_follows_its_answer(options, correct, kept, key):
    q = make_question(0, options=options, correct=correct)
    parsed = parse_quiz(quiz_json(q, make_question(1), make_question(2)))[0]
    assert (parsed.options, parsed.correct) == (kept, key)
    assert parsed.options[parsed.correct] == options[correct]


@pytest.mark.parametrize(
    ("options", "correct"),
    [
        (["W", "X", "Y", "Z", ""], 4),  # the key is the blank option
        (["W", "", "X", "Y", "Z"], 1),  # ...in the middle: it must not pass to the next answer
        (["W", "X", "", "Y"], 0),  # only three real answers
    ],
)
def test_blank_options_still_fail_when_the_key_or_count_is_wrong(options, correct):
    q = make_question(0, options=options, correct=correct)
    with pytest.raises(InvalidQuizOutput):
        parse_quiz(quiz_json(q, make_question(1), make_question(2)))


def test_options_differing_only_in_letter_case_are_distinct():
    # String results: "DataScience".lower() and .upper() are different answers (seen in Phase 26 samples).
    q = make_question(0, options=["DataScience", "datascience", "DATASCIENCE", "Data Science"])
    assert parse_quiz(quiz_json(q, make_question(1), make_question(2)))[0].options[1] == "datascience"


def test_options_differing_only_in_spaces_look_the_same_and_are_rejected():
    q = make_question(0, options=["HELLO, PYTHON!", "  HELLO,   PYTHON!  ", "hello", "Hello"])
    with pytest.raises(InvalidQuizOutput, match="distinct"):
        parse_quiz(quiz_json(q, make_question(1), make_question(2)))


def test_a_single_letter_among_real_options_is_allowed():
    q = make_question(0, options=["A", "65", "undefined", "NaN"])
    assert parse_quiz(quiz_json(q, make_question(1), make_question(2)))[0].options[0] == "A"


def test_double_escaped_line_breaks_in_code_are_repaired():
    # The model sent a literal backslash-n instead of a line break inside a code fence.
    question = "What is logged?\\n```javascript\\nlet n = 0;\\nconsole.log(n);\\n```"
    q = make_question(0, question=question, explanation="It logs 0.\\n```js\\nn === 0\\n```")
    parsed = parse_quiz(quiz_json(q, make_question(1), make_question(2)))[0]
    assert parsed.question == "What is logged?\n```javascript\nlet n = 0;\nconsole.log(n);\n```"
    assert parsed.explanation == "It logs 0.\n```js\nn === 0\n```"


@pytest.mark.parametrize(
    "question",
    [
        "What does `console.log('a\\nb')` print?",  # a backslash-n that belongs to the code
        "What is logged?\n```js\nconsole.log('a\\nb')\n```",  # real line breaks already present
        "Is \\( a \\neq b \\) true?",  # \neq is a LaTeX command, not a line break
    ],
)
def test_meaningful_backslash_n_is_kept(question):
    parsed = parse_quiz(quiz_json(make_question(0, question=question), make_question(1), make_question(2)))[0]
    assert parsed.question == question


@pytest.mark.parametrize(
    "question, options",
    [
        # Seen in Phase 26 samples: line breaks escaped in only part of the text show as \n.
        ("What does the code print?\\n```python\nprint(3 in {3})\nprint(1)\n```", None),
        ("What is printed?", ["True\\n7", "False\\n4", "True\\n4", "True\\n5"]),
        ("Which snippet works?", ['"import requests\\nr = requests.get(url, timeout=5)"', "b", "c", "d"]),
        # Code belongs in backticks; outside them a backslash-n can't be told apart from a broken line break.
        ("What does console.log('a\\nb') print?", None),
    ],
)
def test_a_line_break_escaped_outside_code_is_rejected(question, options):
    q = make_question(0, question=question, **({"options": options} if options else {}))
    with pytest.raises(InvalidQuizOutput, match="line break is written as"):
        parse_quiz(quiz_json(q, make_question(1), make_question(2)))


@pytest.mark.parametrize(
    "question, options",
    [
        # Seen in Phase 27 samples: maths whose delimiters were lost shows its commands raw.
        ("How many weights does the layer have?", ["(5 \\times 5 \\times 64 = 1600)", "b", "c", "d"]),
        ("Which is the third element?", ["\\sin\\left(\\frac{3}{10}\\right)", "b", "c", "d"]),
        ("Which interval is right? (44.8 \\text{ to } 59.2)", None),
    ],
)
def test_latex_outside_maths_is_rejected(question, options):
    q = make_question(0, question=question, **({"options": options} if options else {}))
    with pytest.raises(InvalidQuizOutput, match="LaTeX is written outside"):
        parse_quiz(quiz_json(q, make_question(1), make_question(2)))


@pytest.mark.parametrize(
    "text",
    [
        "What is \\( 5 \\times 5 \\)?",  # inside maths
        "What does `re.sub(r'\\sin', '', s)` do?",  # inside code
        "Run .\\env\\Scripts\\activate on Windows",  # a path, not LaTeX
        "Does \\textbf stay?",  # not a command in the list: the next letters continue the word
    ],
)
def test_backslash_words_that_are_not_stray_latex_are_kept(text):
    parsed = parse_quiz(quiz_json(make_question(0, question=text), make_question(1), make_question(2)))[0]
    assert parsed.question == text


@pytest.mark.parametrize(
    "placeholder",
    [
        "```javascript\n# your answer\n```",  # seen live: a comment-only block after a shell question
        "```bash\n# your commands here\n```",
        "```python\n\n```",
        "```\n// TODO\n```",
        "```sql\n-- write your query\n```",
    ],
)
def test_placeholder_code_blocks_are_removed(placeholder):
    question = f"Which command lists hidden files?{placeholder}"
    parsed = parse_quiz(quiz_json(make_question(0, question=question), make_question(1), make_question(2)))[0]
    assert parsed.question == "Which command lists hidden files?"


@pytest.mark.parametrize(
    "question",
    [
        "What is printed?\n```python\nprint(2 ** 3)\n```",
        "What does this do?\n```bash\n# list everything\nls -a\n```",  # comments alongside real code
        "Which layer handles line 4?\n```text\n1. SYN\n4. GET /index.html HTTP/1.1\n```",
    ],
)
def test_code_blocks_with_content_are_kept(question):
    parsed = parse_quiz(quiz_json(make_question(0, question=question), make_question(1), make_question(2)))[0]
    assert parsed.question == question


def test_a_question_that_is_only_a_placeholder_block_is_rejected():
    q = make_question(0, question="```bash\n# your answer\n```")
    with pytest.raises(InvalidQuizOutput, match="only an empty code block"):
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


def test_fallback_banks_merge_and_reject_a_topic_defined_twice():
    one, two = {"a": [{"question": "1"}]}, {"b": [{"question": "2"}]}
    assert merge(one, two) == {"a": [{"question": "1"}], "b": [{"question": "2"}]}
    with pytest.raises(ValueError, match="fallback questions for a are defined twice"):
        merge(one, {"a": []})


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

ANSWER_KEY_LEAKS = ('"correct"', '"correct_answer"', '"answer"', '"explanation"', "Because answer")


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
    assert response.json() == {
        "detail": "Topic is still locked. Complete its prerequisites first: CSS Basics, HTML Basics, JavaScript Fundamentals."
    }
    assert fake_llm.calls == []  # no LLM cost for a locked topic


@pytestmark_api
def test_generate_returns_quiz_info_without_any_question(client, make_user, fake_llm):
    _, headers = make_user()
    onboard(client, headers)
    response = generate(client, headers)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "quiz_id", "topic", "total_questions", "answered_questions", "seconds_per_question",
        "expires_in_seconds", "source", "proctoring",
    }
    assert body["topic"] == {"id": ROOT, "name": "Git Basics"}
    assert (body["total_questions"], body["answered_questions"], body["source"]) == (3, 0, "ai")
    assert body["seconds_per_question"] == get_settings().quiz_seconds_per_question
    assert body["expires_in_seconds"] == get_settings().quiz_session_ttl_minutes * 60
    assert body["proctoring"]["verified_threshold"] == 80
    assert {r["code"] for r in body["proctoring"]["rules"]} >= {"tab_hidden", "fullscreen_exit", "monitoring_missing"}
    assert "Sample question" not in response.text  # questions come one at a time from /next


@pytestmark_api
def test_answer_key_is_never_sent_before_submission(client, make_user, fake_llm, clock):
    _, headers = make_user()
    onboard(client, headers)
    texts = [generate(client, headers).text]
    quiz_id = json.loads(texts[0])["quiz_id"]
    for index in range(3):
        served = client.post(f"/api/quiz/{quiz_id}/next", headers=headers)
        texts.append(served.text)
        clock.advance(10)
        texts.append(client.post(f"/api/quiz/{quiz_id}/answer", json={"question_id": index, "answer": 0}, headers=headers).text)
    texts.append(client.get("/api/quiz/active", headers=headers).text)
    for text in texts:
        for leaked in ANSWER_KEY_LEAKS:
            assert leaked not in text


@pytestmark_api
def test_answer_key_is_stored_server_side(client, make_user, fake_llm, db):
    user_id, headers = make_user()
    onboard(client, headers)
    quiz_id = generate(client, headers).json()["quiz_id"]
    served = client.post(f"/api/quiz/{quiz_id}/next", headers=headers).json()

    session = db.get(QuizSession, quiz_id)
    assert session.user_id == user_id and session.topic_id == ROOT and session.submitted_at is None
    assert served["options"] == session.questions[0]["options"]
    for stored in session.questions:
        assert stored["options"][stored["correct"]].startswith("Right answer")
    expected_expiry = datetime.now(timezone.utc) + timedelta(minutes=get_settings().quiz_session_ttl_minutes)
    assert abs((session.expires_at - expected_expiry).total_seconds()) < 10


@pytestmark_api
def test_unlocked_topic_becomes_in_progress(client, make_user, fake_llm, db):
    user_id, headers = make_user()
    onboard(client, headers)
    assert progress_row(db, user_id, ROOT).status == "unlocked"
    generate(client, headers)
    assert progress_row(db, user_id, ROOT).status == "in_progress"


@pytestmark_api
def test_completed_topic_can_be_retaken_and_stays_completed(client, make_user, fake_llm, db):
    user_id, headers = make_user()
    onboard(client, headers, [ROOT])
    assert generate(client, headers).status_code == 200
    assert progress_row(db, user_id, ROOT).status == "completed"


@pytestmark_api
def test_quiz_before_onboarding_initialises_progress(client, make_user, fake_llm, db):
    user_id, headers = make_user()
    assert generate(client, headers).status_code == 200
    db.expire_all()
    # The quizzed topic gets a row, and so does every topic open to a new learner (in every domain);
    # the rest stay derived from the graph until they become reachable.
    rows = db.scalars(select(TopicProgress).where(TopicProgress.user_id == user_id)).all()
    assert {r.topic_id for r in rows} == {
        ROOT, "html_basics", "javascript_fundamentals", "sql_basics", "command_line_basics", "how_the_internet_works",
        "how_computers_work", "programming_concepts", "python_basics", "ds_descriptive_stats", "ml_what_is_ml",
        "ml_linear_algebra",
    }
    assert progress_row(db, user_id, ROOT).status == "in_progress"
    nodes = {n["id"]: n for n in client.get("/api/topics/graph", headers=headers).json()["nodes"]}
    assert nodes["react_fundamentals"]["status"] == "locked"


@pytestmark_api
def test_groq_down_still_produces_a_quiz(client, make_user, fake_llm, db):
    """Phase 10 exit gate: the Groq-unavailable case."""
    _, headers = make_user()
    onboard(client, headers)
    fake_llm.script = [connection_error()]

    body = generate(client, headers).json()

    assert body["source"] == "fallback"
    session = db.get(QuizSession, body["quiz_id"])
    assert {q["question"] for q in session.questions} == {q["question"] for q in FALLBACK_QUESTIONS[ROOT]}
    served = client.post(f"/api/quiz/{body['quiz_id']}/next", headers=headers).json()
    assert served["question"] in {q["question"] for q in FALLBACK_QUESTIONS[ROOT]}


@pytestmark_api
def test_no_api_key_serves_fallback_quiz(client, make_user, no_api_key):
    _, headers = make_user()
    onboard(client, headers)
    assert generate(client, headers).json()["source"] == "fallback"


@pytestmark_api
def test_no_questions_anywhere_returns_503(client, make_user, fake_llm, monkeypatch):
    _, headers = make_user()
    onboard(client, headers)
    monkeypatch.setitem(FALLBACK_QUESTIONS, ROOT, [])
    fake_llm.script = [connection_error()]

    response = generate(client, headers)

    assert response.status_code == 503
    assert response.json() == {"detail": "Quiz generation is temporarily unavailable. Please try again shortly."}


# =====================================================================================
# Submission (Phase 11, proctored flow since Phase 12.5)
# =====================================================================================

SUBMIT_TOPIC = "html_basics"  # completing it unlocks css_basics and semantic_html


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
    assert client.post("/api/quiz/submit", json={"quiz_id": "00000000-0000-0000-0000-000000000000"}).status_code == 401


@pytestmark_api
def test_perfect_quiz_passes_masters_and_unlocks(learner, quiz_taker):
    _, headers = learner
    body = quiz_taker(headers, SUBMIT_TOPIC, "CCC")

    assert (body["topic_id"], body["score"], body["total"], body["passed"]) == (SUBMIT_TOPIC, 3, 3, True)
    assert body["p_know_before"] == pytest.approx(0.10)
    assert body["p_know_after"] == pytest.approx(0.9890160183, abs=1e-9)
    assert (body["mastered"], body["status"], body["needs_attention"]) == (True, "completed", False)
    assert body["recommended_resources"] == []
    assert body["newly_unlocked"] == ["css_basics", "semantic_html"]
    assert [t["id"] for t in body["next_topics"]] == ["css_basics", "git_basics", "javascript_fundamentals"]
    assert body["integrity"] == {"score": 100, "verdict": "verified", "counted": True, "reasons": []}


@pytestmark_api
def test_feedback_reveals_answers_and_explanations_after_submission(learner, quiz_taker):
    _, headers = learner
    feedback = quiz_taker(headers, SUBMIT_TOPIC, "CWT")["feedback"]

    assert [f["is_correct"] for f in feedback] == [True, False, False]
    assert [f["timed_out"] for f in feedback] == [False, False, True]
    assert feedback[0]["selected"] == feedback[0]["correct"]
    assert feedback[1]["selected"] != feedback[1]["correct"]
    assert feedback[2]["selected"] is None
    for item in feedback:
        assert len(item["options"]) == 4 and item["question"] and item["explanation"].startswith("Because")


@pytestmark_api
def test_submission_persists_progress_attempt_and_integrity(learner, quiz_taker, db):
    """ARCHITECTURE 23: successful submission writes attempt and progress."""
    user_id, headers = learner
    quiz_taker(headers, SUBMIT_TOPIC, "CCW")

    row = progress_row(db, user_id, SUBMIT_TOPIC)
    assert (row.status, row.attempts, row.correct) == ("completed", 1, 2)
    assert row.p_know == pytest.approx(0.7589958159, abs=1e-9)

    (attempt,) = attempts_for(db, user_id)
    assert (attempt.topic_id, attempt.score, attempt.passed) == (SUBMIT_TOPIC, 2, True)
    assert attempt.p_know_after == pytest.approx(0.7589958159, abs=1e-9)
    key = [q["correct"] for q in attempt.questions]
    assert attempt.submitted_answers[:2] == key[:2] and attempt.submitted_answers[2] != key[2]
    integrity = db.scalar(select(QuizIntegrity).where(QuizIntegrity.attempt_id == attempt.id))
    assert (integrity.verdict, integrity.counted, integrity.score) == ("verified", True, 100)
    assert db.get(QuizSession, integrity.session_id).submitted_at is not None


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
        ("CCT", 0.7589958159, True),  # a timeout counts as a wrong answer
    ],
)
@pytestmark_api
def test_bkt_is_applied_to_answers_in_order(learner, quiz_taker, pattern, expected_after, passed):
    _, headers = learner
    body = quiz_taker(headers, SUBMIT_TOPIC, pattern)
    assert body["p_know_after"] == pytest.approx(expected_after, abs=1e-9)
    assert body["passed"] is passed
    assert body["score"] == pattern.count("C")


@pytestmark_api
def test_failed_quiz_keeps_topic_in_progress_and_recommends_resources(learner, quiz_taker, db):
    user_id, headers = learner
    body = quiz_taker(headers, SUBMIT_TOPIC, "CWW")

    assert (body["passed"], body["status"], body["newly_unlocked"]) == (False, "in_progress", [])
    html = next(t for t in TOPICS if t.id == SUBMIT_TOPIC)
    assert body["recommended_resources"] == [{"title": r.title, "url": r.url, "type": r.type} for r in html.resources]
    assert progress_row(db, user_id, "css_basics").status == "locked"


@pytestmark_api
def test_failed_retake_never_undoes_completion(client, make_user, fake_llm, quiz_taker, db):
    user_id, headers = make_user()
    onboard(client, headers, [SUBMIT_TOPIC])  # completed at 0.95

    body = quiz_taker(headers, SUBMIT_TOPIC, "WWW")

    assert (body["passed"], body["status"]) == (False, "completed")
    assert body["p_know_after"] < 0.95
    assert progress_row(db, user_id, "css_basics").status == "unlocked"


@pytestmark_api
def test_needs_attention_after_more_than_two_poor_attempts_then_clears(learner, quiz_taker, db):
    user_id, headers = learner
    first = quiz_taker(headers, SUBMIT_TOPIC, "WWW")
    second = quiz_taker(headers, SUBMIT_TOPIC, "WWW")
    assert first["needs_attention"] is False and second["needs_attention"] is False

    third = quiz_taker(headers, SUBMIT_TOPIC, "WWW")
    assert third["needs_attention"] is True and third["recommended_resources"]
    assert progress_row(db, user_id, SUBMIT_TOPIC).needs_attention is True

    assert quiz_taker(headers, SUBMIT_TOPIC, "CCC")["needs_attention"] is False
    assert progress_row(db, user_id, SUBMIT_TOPIC).needs_attention is False


@pytestmark_api
def test_counters_accumulate_across_attempts(learner, quiz_taker, db):
    user_id, headers = learner
    quiz_taker(headers, SUBMIT_TOPIC, "CWW")
    quiz_taker(headers, SUBMIT_TOPIC, "CCW")
    row = progress_row(db, user_id, SUBMIT_TOPIC)
    assert (row.attempts, row.correct) == (2, 3)
    assert len(attempts_for(db, user_id)) == 2


@pytestmark_api
def test_submission_changes_progress_and_recommendations(client, learner, quiz_taker):
    """Phase 11 exit gate."""
    _, headers = learner
    before = client.get("/api/topics/learning-path", headers=headers).json()["recommended"]
    assert [t["id"] for t in before] == ["git_basics", "html_basics", "javascript_fundamentals"]

    body = quiz_taker(headers, SUBMIT_TOPIC, "CCC")

    after = client.get("/api/topics/learning-path", headers=headers).json()["recommended"]
    assert [t["id"] for t in after] == ["css_basics", "git_basics", "javascript_fundamentals"]
    assert after == body["next_topics"]


@pytestmark_api
def test_another_users_quiz_is_not_found_and_left_untouched(client, make_user, fake_llm, db, clock):
    """ARCHITECTURE 23: wrong user's quiz submission rejected - for every quiz endpoint."""
    _, owner = make_user("owner@example.com")
    _, intruder = make_user("intruder@example.com")
    onboard(client, owner)
    quiz_id = generate(client, owner).json()["quiz_id"]

    attempts = [
        client.post(f"/api/quiz/{quiz_id}/next", headers=intruder),
        client.post(f"/api/quiz/{quiz_id}/answer", json={"question_id": 0, "answer": 0}, headers=intruder),
        client.post(f"/api/quiz/{quiz_id}/events", json={"events": [{"type": "heartbeat"}]}, headers=intruder),
        client.post("/api/quiz/submit", json={"quiz_id": quiz_id}, headers=intruder),
    ]
    for response in attempts:
        assert response.status_code == 404
        assert response.json() == {"detail": "Quiz not found"}
    db.expire_all()
    assert db.get(QuizSession, quiz_id).submitted_at is None
    assert client.post(f"/api/quiz/{quiz_id}/next", headers=owner).status_code == 200


@pytestmark_api
def test_unknown_quiz_returns_404(client, learner):
    _, headers = learner
    unknown = "11111111-2222-3333-4444-555555555555"
    assert client.post("/api/quiz/submit", json={"quiz_id": unknown}, headers=headers).status_code == 404
    assert client.post(f"/api/quiz/{unknown}/next", headers=headers).status_code == 404


@pytestmark_api
def test_expired_quiz_is_rejected_everywhere(client, learner, db):
    """ARCHITECTURE 23: expired quiz rejected."""
    user_id, headers = learner
    quiz_id = generate(client, headers).json()["quiz_id"]
    session = db.get(QuizSession, quiz_id)
    session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()

    for response in (
        client.post(f"/api/quiz/{quiz_id}/next", headers=headers),
        client.post(f"/api/quiz/{quiz_id}/answer", json={"question_id": 0, "answer": 0}, headers=headers),
        client.post("/api/quiz/submit", json={"quiz_id": quiz_id}, headers=headers),
    ):
        assert response.status_code == 410
        assert response.json() == {"detail": "This quiz has expired. Start a new quiz for this topic."}
    assert attempts_for(db, user_id) == []
    assert progress_row(db, user_id, SUBMIT_TOPIC).attempts == 0


@pytestmark_api
def test_second_submission_is_rejected(client, learner, quiz_taker, db):
    """ARCHITECTURE 23: second submission rejected."""
    user_id, headers = learner
    quiz_taker(headers, SUBMIT_TOPIC, "CCC")
    (attempt,) = attempts_for(db, user_id)
    session_id = db.scalar(select(QuizIntegrity.session_id).where(QuizIntegrity.attempt_id == attempt.id))

    response = client.post("/api/quiz/submit", json={"quiz_id": str(session_id)}, headers=headers)

    assert response.status_code == 409
    assert response.json() == {"detail": "This quiz has already been submitted"}
    assert len(attempts_for(db, user_id)) == 1
    assert progress_row(db, user_id, SUBMIT_TOPIC).attempts == 1


@pytest.mark.parametrize(
    "payload",
    [{"question_id": 0, "answer": 4}, {"question_id": 0, "answer": -1}, {"question_id": 0, "answer": "0"},
     {"question_id": 0, "answer": True}, {"question_id": 0, "answer": 0.0}, {"question_id": 3, "answer": 0},
     {"question_id": -1, "answer": 0}, {"answer": 0}, {"question_id": 0}],
    ids=["index-4", "negative", "string", "bool", "float", "question-3", "question-negative", "no-question", "no-answer"],
)
@pytestmark_api
def test_invalid_answer_payloads_are_rejected(client, learner, payload):
    _, headers = learner
    quiz_id = generate(client, headers).json()["quiz_id"]
    client.post(f"/api/quiz/{quiz_id}/next", headers=headers)
    assert client.post(f"/api/quiz/{quiz_id}/answer", json=payload, headers=headers).status_code == 422


@pytestmark_api
def test_old_style_submit_with_answers_list_is_rejected(client, learner):
    _, headers = learner
    quiz_id = generate(client, headers).json()["quiz_id"]
    response = client.post("/api/quiz/submit", json={"quiz_id": quiz_id, "answers": [0, 1, 2]}, headers=headers)
    assert response.status_code == 422


@pytestmark_api
def test_malformed_quiz_id_is_rejected(client, learner):
    _, headers = learner
    assert client.post("/api/quiz/submit", json={"quiz_id": "not-a-uuid"}, headers=headers).status_code == 422
    assert client.post("/api/quiz/not-a-uuid/next", headers=headers).status_code == 422


@pytestmark_api
def test_failure_midway_saves_nothing_and_allows_resubmission(client, learner, db, clock, monkeypatch):
    """Neo4j dies after progress was updated in memory: the whole submission rolls back."""
    from db import neo4j_db

    user_id, headers = learner
    quiz_id = generate(client, headers, SUBMIT_TOPIC).json()["quiz_id"]
    key = [q["correct"] for q in db.get(QuizSession, quiz_id).questions]
    for index in range(3):
        client.post(f"/api/quiz/{quiz_id}/next", headers=headers)
        for _ in range(2):
            clock.advance(5)
            client.post(f"/api/quiz/{quiz_id}/events", json={"events": [{"type": "heartbeat"}]}, headers=headers)
        client.post(f"/api/quiz/{quiz_id}/answer", json={"question_id": index, "answer": key[index]}, headers=headers)

    real_read, calls = neo4j_db.read, []

    def flaky_read(*args, **kwargs):
        calls.append(1)
        if len(calls) >= 2:  # 1st read: topic lookup; 2nd: frontier, after the progress changes
            raise ServiceUnavailable("Neo4j went away")
        return real_read(*args, **kwargs)

    monkeypatch.setattr(neo4j_db, "read", flaky_read)
    assert client.post("/api/quiz/submit", json={"quiz_id": quiz_id}, headers=headers).status_code == 503

    db.expire_all()
    assert db.get(QuizSession, quiz_id).submitted_at is None
    assert attempts_for(db, user_id) == []
    row = progress_row(db, user_id, SUBMIT_TOPIC)
    assert (row.status, row.attempts, row.p_know) == ("in_progress", 0, pytest.approx(0.10))

    monkeypatch.setattr(neo4j_db, "read", real_read)
    assert client.post("/api/quiz/submit", json={"quiz_id": quiz_id}, headers=headers).status_code == 200
