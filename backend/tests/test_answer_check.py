"""Phase 25: the answer check, maths in quiz text, and domain rules in the quiz prompt.

The answer check is a second Groq call that answers every new question independently; a question
whose key it disagrees with, that has more than one correct option, or that it judges unsound is
replaced from the fallback bank. A quiz that can't be checked is never served.
"""

import json
import logging

import pytest

from config import get_settings
from schemas.quiz import QuizQuestion, maths_problem, repair_maths
from seed.fallback_questions import FALLBACK_QUESTIONS
from services import llm_quiz
from services.llm_quiz import AnswerCheck, InvalidQuizOutput, generate_questions, parse_check, parse_quiz
from services.topic_service import TopicInfo
from test_quiz import VALID, api_status_error, connection_error, make_question, quiz_json

TOPIC = TopicInfo("async_javascript", "Async JavaScript", "Promises and async/await.", 3)
BANK = [q["question"] for q in FALLBACK_QUESTIONS[TOPIC.id]]


def check(*entries) -> str:
    """An answer-check response: each entry is (correct options, sound) or (correct options, sound, reason)."""
    return json.dumps({"checks": [
        {"correct": list(e[0]), "sound": e[1], "reason": e[2] if len(e) > 2 else "Checked."} for e in entries
    ]})


AGREE = check(([0], True), ([0], True), ([0], True))


# --- The check call ---------------------------------------------------------------------

def test_every_generated_quiz_is_checked_once_without_its_answer_key(fake_llm):
    result = generate_questions(TOPIC, "Web Development")
    assert result.source == "ai"
    assert len(fake_llm.calls) == 1 and len(fake_llm.check_calls) == 1
    call = fake_llm.check_calls[0]
    system, user = call["messages"]
    assert system["content"] == llm_quiz.CHECK_PROMPT
    # The questions and every option, numbered - but never the key or the explanation.
    for n in range(3):
        assert f"Question {n + 1}: Sample question number {n}?" in user["content"]
        for i, option in enumerate([f"Right answer {n}", f"Wrong A{n}", f"Wrong B{n}", f"Wrong C{n}"]):
            assert f"{i}. {option}" in user["content"]
        assert f"Because answer {n} is right." not in user["content"]
    assert '"correct"' not in user["content"]
    # Deterministic, at its own reasoning effort.
    assert call["temperature"] == 0
    assert call["reasoning_effort"] == get_settings().groq_check_reasoning_effort == "medium"
    assert 0 < call["timeout"] <= llm_quiz.CHECK_TIMEOUT_SECONDS


def test_the_check_prompt_asks_for_every_correct_option_and_flags_attacks():
    prompt = llm_quiz.CHECK_PROMPT
    assert "EVERY option" in prompt and "If two options both work, list both" in prompt
    assert "teaches how to carry out an attack" in prompt


def test_generation_leaves_time_for_the_check(fake_llm):
    generate_questions(TOPIC, "Web Development")
    assert fake_llm.calls[0]["timeout"] <= llm_quiz.TOTAL_BUDGET_SECONDS - llm_quiz.CHECK_RESERVE_SECONDS


def test_a_retry_only_gets_the_time_that_leaves_room_for_the_check(fake_llm, monkeypatch):
    # The first attempt is invalid and returns at 12 s: 20 s budget - 5 s kept for the check - 12 s = 3 s.
    now = iter([0.0, 0.0, 12.0, 13.0])  # start, attempt 1, attempt 2, after attempt 2
    monkeypatch.setattr(llm_quiz.time, "monotonic", lambda: next(now))
    fake_llm.script = ["not json", VALID]
    result = generate_questions(TOPIC, "Web Development")
    assert result.source == "ai"
    assert fake_llm.calls[1]["timeout"] == pytest.approx(3.0)


def test_no_retry_starts_when_only_the_checks_time_is_left(fake_llm, monkeypatch):
    now = iter([0.0, 0.0, 14.5])  # 20 - 5 - 14.5 leaves half a second: too little to generate
    monkeypatch.setattr(llm_quiz.time, "monotonic", lambda: next(now))
    fake_llm.script = ["not json"]
    result = generate_questions(TOPIC, "Web Development")
    assert result.source == "fallback"
    assert len(fake_llm.calls) == 1


def test_with_the_check_off_ai_questions_are_used_unchecked(fake_llm, monkeypatch):
    monkeypatch.setattr(get_settings(), "quiz_answer_check", False)
    result = generate_questions(TOPIC, "Web Development")
    assert result.source == "ai"
    assert fake_llm.check_calls == []


# --- Verdicts ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("correct", "sound", "passes"),
    [
        ([0], True, True),
        ([0, 0], True, True),  # the same option twice is still one answer
        ([1], True, False),  # the checker disagrees with the key
        ([0, 2], True, False),  # two correct options
        ([], True, False),  # no correct option
        ([0], False, False),  # ambiguous, or an error in the question
    ],
)
def test_a_question_passes_only_when_sound_with_the_key_as_its_only_answer(correct, sound, passes):
    assert AnswerCheck(correct=correct, sound=sound).passes(0) is passes


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        "not json",
        '{"checks": "yes"}',
        check(([0], True), ([0], True)),  # one short
        check(([0], True), ([0], True), ([0], True), ([0], True)),  # one too many
        check(([4], True), ([0], True), ([0], True)),  # no option 4
        json.dumps({"checks": [{"correct": [0], "sound": "true"}] * 3}),  # sound must be a boolean
    ],
)
def test_unusable_check_output_is_rejected(raw):
    with pytest.raises(InvalidQuizOutput):
        parse_check(raw, 3)


def test_a_failed_question_is_replaced_from_the_bank_in_place(fake_llm, caplog):
    fake_llm.check_script = [check(([0], True), ([0, 1], True, "B is also right."), ([0], True))]
    with caplog.at_level(logging.WARNING, logger="adaptlearn"):
        result = generate_questions(TOPIC, "Web Development")
    assert result.source == "mixed"
    texts = [q.question for q in result.questions]
    assert texts == ["Sample question number 0?", BANK[0], "Sample question number 2?"]
    replacement = result.questions[1]
    assert replacement.options[replacement.correct] == FALLBACK_QUESTIONS[TOPIC.id][0]["options"][0]
    assert "question 2 failed the answer check (key 0, checker [0, 1], sound=True): B is also right." in caplog.text


def test_several_failed_questions_get_different_replacements(fake_llm):
    fake_llm.check_script = [check(([1], True), ([0], False), ([0], True))]
    result = generate_questions(TOPIC, "Web Development")
    assert result.source == "mixed"
    assert [q.question for q in result.questions] == [BANK[0], BANK[1], "Sample question number 2?"]


def test_a_bank_question_the_ai_also_asked_is_not_used_twice(fake_llm):
    own = FALLBACK_QUESTIONS[TOPIC.id][0]
    fake_llm.script = [quiz_json(make_question(0), own, make_question(2))]
    fake_llm.check_script = [check(([1], True), ([0], True), ([0], True))]
    result = generate_questions(TOPIC, "Web Development")
    assert [q.question for q in result.questions] == [BANK[1], BANK[0], "Sample question number 2?"]


def test_when_every_question_fails_the_whole_quiz_comes_from_the_bank(fake_llm):
    fake_llm.check_script = [check(([1], True), ([2], True), ([3], True))]
    result = generate_questions(TOPIC, "Web Development")
    assert result.source == "fallback"
    assert [q.question for q in result.questions] == BANK
    assert len(fake_llm.calls) == 1  # a rejected quiz isn't regenerated: the learner is waiting


def test_without_enough_bank_questions_the_quiz_is_unavailable(fake_llm, monkeypatch):
    monkeypatch.setitem(FALLBACK_QUESTIONS, TOPIC.id, [])
    fake_llm.check_script = [check(([0], True), ([1], True), ([0], True))]
    assert generate_questions(TOPIC, "Web Development") is None


@pytest.mark.parametrize(
    "failure",
    [
        lambda: "not json",
        lambda: check(([0], True)),
        lambda: api_status_error(400),
        lambda: api_status_error(429),
        connection_error,
    ],
    ids=["invalid", "incomplete", "400", "429", "unreachable"],
)
def test_a_quiz_that_cannot_be_checked_is_not_served(fake_llm, failure, caplog):
    fake_llm.check_script = [failure()]
    with caplog.at_level(logging.WARNING, logger="adaptlearn"):
        result = generate_questions(TOPIC, "Web Development")
    assert result.source == "fallback"
    assert [q.question for q in result.questions] == BANK
    assert len(fake_llm.calls) == 1 and len(fake_llm.check_calls) == 1  # neither call is retried
    assert "answer check failed" in caplog.text


def test_no_time_left_for_the_check_means_the_bank(fake_llm, monkeypatch):
    now = iter([0.0, 0.0, 19.5])  # start, before generating, after generating
    monkeypatch.setattr(llm_quiz.time, "monotonic", lambda: next(now))
    result = generate_questions(TOPIC, "Web Development")
    assert result.source == "fallback"
    assert fake_llm.check_calls == []


def test_the_check_gets_what_is_left_of_the_budget(fake_llm, monkeypatch):
    now = iter([0.0, 0.0, 15.0])
    monkeypatch.setattr(llm_quiz.time, "monotonic", lambda: next(now))
    generate_questions(TOPIC, "Web Development")
    assert fake_llm.check_calls[0]["timeout"] == pytest.approx(llm_quiz.TOTAL_BUDGET_SECONDS - 15.0)


def test_invalid_generations_are_retried_before_the_single_check(fake_llm):
    fake_llm.script = ["not json", VALID]
    result = generate_questions(TOPIC, "Web Development")
    assert result.source == "ai"
    assert len(fake_llm.calls) == 2 and len(fake_llm.check_calls) == 1


def test_a_mixed_quiz_is_reported_by_the_api(client, make_user, fake_llm):
    _, headers = make_user()
    fake_llm.check_script = [check(([0], True), ([1], True), ([0], True))]
    response = client.get("/api/quiz/generate/git_basics", headers=headers)
    assert response.status_code == 200
    assert response.json()["source"] == "mixed"


# --- Domain rules -------------------------------------------------------------------------

def test_cybersecurity_topics_get_the_defensive_rule():
    topic = TopicInfo("phishing", "Phishing", "Recognising and stopping phishing.", 1, domains=["cybersecurity"])
    prompt = llm_quiz.build_user_prompt(topic, "Cybersecurity")
    assert prompt.endswith("Rule: " + llm_quiz.DOMAIN_RULES["cybersecurity"])
    assert "conceptual and defensive" in prompt and "Never include working exploit code" in prompt


def test_a_shared_topic_gets_the_rule_whichever_domain_it_is_quizzed_from():
    topic = TopicInfo("networking", "Networking", "How networks work.", 1, domains=["cybersecurity", "foundations"])
    assert "Rule: " in llm_quiz.build_user_prompt(topic, "Foundations")


def test_other_topics_get_no_extra_rule():
    assert "Rule:" not in llm_quiz.build_user_prompt(TOPIC, "Web Development")


def test_real_cybersecurity_quizzes_are_sent_with_the_rule(client, make_user, fake_llm):
    # The real curriculum: a Cybersecurity topic, and Security Basics, which Foundations shares with it.
    _, headers = make_user()
    known = {"domain": "foundations", "topic_ids": ["how_the_internet_works"]}
    assert client.post("/api/topics/mark-known", json=known, headers=headers).status_code == 200
    for topic_id in ("sec_principles", "security_basics"):
        assert client.get(f"/api/quiz/generate/{topic_id}", headers=headers).status_code == 200
    assert len(fake_llm.calls) == 2
    for call in fake_llm.calls:
        assert call["messages"][-1]["content"].endswith("Rule: " + llm_quiz.DOMAIN_RULES["cybersecurity"])


# --- Maths ---------------------------------------------------------------------------------

def test_the_prompt_asks_for_latex_between_unambiguous_delimiters():
    prompt = llm_quiz.SYSTEM_PROMPT
    assert "\\( and \\)" in prompt and "\\[ and \\]" in prompt
    assert "Never use $ signs" in prompt


@pytest.mark.parametrize(
    ("broken", "fixed"),
    [
        ("\\( \frac{1}{2} \\)", "\\( \\frac{1}{2} \\)"),  # \f: form feed
        ("\\( \beta \\)", "\\( \\beta \\)"),  # \b: backspace
        ("\\( a \times b \\)", "\\( a \\times b \\)"),  # \t: tab
        ("\\[ \nabla f \\]", "\\[ \\nabla f \\]"),  # \n: line break
        ("\\( \rho \\)", "\\( \\rho \\)"),  # \r: carriage return
    ],
)
def test_latex_commands_eaten_by_json_escapes_are_repaired(broken, fixed):
    assert repair_maths(broken) == fixed


def test_real_line_breaks_and_tabs_outside_maths_are_kept():
    text = "Line one\nLine two\tand a tab \\( x \\)\n\nLast"
    assert repair_maths(text) == text


def test_repaired_maths_survives_parsing():
    raw = '{"questions": [' + ",".join(
        json.dumps(make_question(n)) for n in range(2)
    ) + ', {"question": "What is \\\\( \\frac{1}{4} \\\\) as a decimal?", "options": ["0.25", "0.4", "4", "1.4"],' \
        ' "correct": 0, "explanation": "One divided by four."}]}'
    question = parse_quiz(raw)[2].question
    assert question == "What is \\( \\frac{1}{4} \\) as a decimal?"


@pytest.mark.parametrize(
    ("text", "problem"),
    [
        ("Plain text with $5 and no maths", None),
        ("Inline \\( x^2 \\) and display \\[ y = mx + c \\]", None),
        ("Regex `\\(` in inline code is code", None),
        ("```python\nre.compile(r'\\(')\n```", None),
        ("Opened \\( x", "maths opened with \\( is never closed"),
        ("Closed x \\)", "\\) closes maths that wasn't opened"),
        ("Mismatched \\( x \\]", "\\] closes maths that wasn't opened"),
        ("Nested \\( a \\[ b \\] \\)", "maths opened with \\( isn't closed before \\["),
    ],
)
def test_maths_delimiters_must_pair_up_outside_code(text, problem):
    assert maths_problem(text) == problem


def test_questions_with_unbalanced_maths_are_rejected_so_the_quiz_is_regenerated(fake_llm):
    broken = make_question(0, question="What is \\( x^2 when x = 3?")
    fake_llm.script = [quiz_json(broken, make_question(1), make_question(2)), VALID]
    result = generate_questions(TOPIC, "Web Development")
    assert result.source == "ai"
    assert len(fake_llm.calls) == 2


def test_options_and_explanations_are_checked_too():
    with pytest.raises(ValueError, match="never closed"):
        QuizQuestion(**make_question(0, options=["\\( 1", "2", "3", "4"]))
    with pytest.raises(ValueError, match="never closed"):
        QuizQuestion(**make_question(0, explanation="Because \\[ x"))
