"""Quiz question generation with Groq, validation, retries and a curated fallback.

Flow (ARCHITECTURE.md section 14, plus the answer check of Phase 25):
  Groq response -> strip accidental code fences -> json.loads -> Pydantic schema
  -> business validation -> accept, or retry (max 2 retries) -> fallback question bank
  An accepted quiz then goes through the answer check: a second call answers every question
  independently, and a question whose key it disagrees with (or that has more than one defensible
  answer) is replaced from the fallback bank. A quiz that can't be checked uses the fallback bank.
"""

import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Annotated, Any, Literal

from groq import APIConnectionError, APIStatusError, APITimeoutError, Groq
from pydantic import BaseModel, Field, StrictBool, StrictInt, ValidationError

from config import get_settings
from schemas.quiz import OPTIONS_PER_QUESTION, QUESTIONS_PER_QUIZ, QuizContent, QuizQuestion, normalise
from seed.fallback_questions import FALLBACK_QUESTIONS
from services.topic_service import TopicInfo

logger = logging.getLogger("adaptlearn")

MAX_RETRIES = 2  # after the initial attempt
REQUEST_TIMEOUT_SECONDS = 10.0
# Stop retrying once this much time has passed, so the browser (25s timeout for this request)
# still gets a quiz from the fallback bank instead of an error.
TOTAL_BUDGET_SECONDS = 20.0
TEMPERATURE = 0.7
MAX_COMPLETION_TOKENS = 1500
# The answer check: kept back from the budget while generating, so a quiz that arrives can be checked.
CHECK_RESERVE_SECONDS = 5.0
CHECK_TIMEOUT_SECONDS = 8.0
CHECK_MAX_COMPLETION_TOKENS = 3000

SYSTEM_PROMPT = f"""You are a quiz generator for an adaptive learning platform.
Return ONLY valid JSON. Do not use markdown fences or prose outside JSON.
Generate exactly {QUESTIONS_PER_QUIZ} multiple-choice questions for the topic provided.
Return an object of the form:
{{"questions": [{{"question": "...", "options": ["...", "...", "...", "..."], "correct": 0, "explanation": "..."}}]}}
Each question must contain:
- question: string
- options: exactly 4 distinct strings, with exactly one correct option and plausible wrong options
- correct: integer 0-3, the index of the correct option
- explanation: concise string explaining why the correct option is right
Do not use "All of the above" or "None of the above".
Exactly one option may be correct. Every other option must be clearly wrong for the question as
asked - never a different but equally valid way to get the same result. The correct option must
satisfy every condition stated in the question.
Questions should test understanding, not obscure trivia, and match the stated difficulty.
Prefer applied questions - a short scenario or code snippet the learner must reason about - over
definitions that could be looked up in seconds.
Put a code snippet in a fenced block inside the question, tagged with its real language (for example
```python, ```bash, ```sql, ```html, ```javascript; ```text for program output or logs), with line
breaks between its lines; use single backticks for short inline code. Only include a code block the
learner needs to read to answer; never add an empty or placeholder block (such as "# your answer").
Each option must be a complete answer on its own. Never write options that refer to choices listed
in the question (such as "A" or "option B"): the app labels the options itself.
When a question needs mathematical notation, write it in LaTeX between \\( and \\) inside a sentence, or
between \\[ and \\] for a formula on its own line (escape the backslashes in JSON). Never use $ signs
around maths. Don't use LaTeX for code or for plain numbers."""

# Extra rules for topics in particular domains, added to the request for any topic in that domain.
DOMAIN_RULES: dict[str, str] = {
    "cybersecurity": (
        "This is a cybersecurity topic. Keep every question conceptual and defensive: how attacks and "
        "weaknesses work at a high level, how to recognise them, and how to prevent, detect and respond "
        "to them. Never include working exploit code, payloads, malware, step-by-step instructions for "
        "attacking or getting into systems without permission, or ways to evade security controls."
    ),
}

CHECK_PROMPT = """You check multiple-choice quiz questions before learners see them. Answer every question yourself,
independently and carefully: read it literally, and use the real behaviour of the tools and concepts involved
(exact output, ordering, defaults, edge cases).
Return ONLY JSON: {"checks": [{"correct": [0], "sound": true, "reason": "..."}]}, one entry per question, in order.
- correct: the index (0-3) of EVERY option an expert would accept as a correct answer to the question as asked.
  If two options both work, list both. If none is correct, return an empty list.
- sound: false if the question is ambiguous, relies on an unstated assumption that changes the answer, contains a
  factual error, cannot be answered from what it says, or teaches how to carry out an attack (working exploit,
  payload or step-by-step intrusion) rather than how attacks work or how to defend; otherwise true.
- reason: one short sentence."""

DIFFICULTY_LABELS = {1: "beginner", 2: "early intermediate", 3: "intermediate", 4: "advanced"}

_CODE_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL | re.IGNORECASE)


class InvalidQuizOutput(ValueError):
    pass


@dataclass(frozen=True)
class GeneratedQuestions:
    questions: list[QuizQuestion]
    # "mixed": AI questions, with those that failed the answer check replaced from the fallback bank.
    source: Literal["ai", "fallback", "mixed"]


def build_user_prompt(topic: TopicInfo, domain_name: str) -> str:
    level = DIFFICULTY_LABELS.get(topic.difficulty, "intermediate")
    prompt = (
        f"Domain: {domain_name}\n"
        f"Topic: {topic.name}\n"
        f"Description: {topic.description}\n"
        f"Difficulty: {topic.difficulty} of 4 ({level})"
    )
    rules = [DOMAIN_RULES[d] for d in sorted(set(topic.domains)) if d in DOMAIN_RULES]
    return prompt + "".join(f"\nRule: {rule}" for rule in rules)


def parse_quiz(raw: str | None) -> list[QuizQuestion]:
    """Validate raw model output. Raises InvalidQuizOutput with a reason if it can't be used."""
    if not raw or not raw.strip():
        raise InvalidQuizOutput("empty response")
    match = _CODE_FENCE.match(raw)
    text = match.group(1) if match else raw
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidQuizOutput(f"not valid JSON: {exc}") from exc
    try:
        return QuizContent.model_validate(data).questions
    except ValidationError as exc:
        reasons = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()[:5])
        raise InvalidQuizOutput(f"schema validation failed: {reasons}") from exc


def call_groq(
    messages: list[dict[str, str]],
    timeout: float,
    *,
    temperature: float = TEMPERATURE,
    reasoning_effort: str | None = None,
    max_completion_tokens: int = MAX_COMPLETION_TOKENS,
) -> str | None:
    """One chat completion in JSON mode. Separate function so tests can replace it.

    `reasoning_effort` defaults to GROQ_REASONING_EFFORT; empty means don't send one.
    """
    settings = get_settings()
    client = Groq(api_key=settings.groq_api_key, timeout=timeout, max_retries=0)
    effort = settings.groq_reasoning_effort if reasoning_effort is None else reasoning_effort
    extra: dict[str, Any] = {"reasoning_effort": effort} if effort else {}
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        temperature=temperature,
        max_completion_tokens=max_completion_tokens,
        response_format={"type": "json_object"},
        **extra,
    )
    return response.choices[0].message.content


# --- The answer check -------------------------------------------------------------------

OptionIndex = Annotated[StrictInt, Field(ge=0, le=OPTIONS_PER_QUESTION - 1)]


class AnswerCheck(BaseModel):
    """The checker's own answer to one question."""

    correct: list[OptionIndex] = Field(max_length=OPTIONS_PER_QUESTION)
    sound: StrictBool
    reason: str = ""

    def passes(self, key: int) -> bool:
        """True when the question is sound and the key is its only correct option."""
        return self.sound and sorted(set(self.correct)) == [key]


class _CheckResponse(BaseModel):
    checks: list[AnswerCheck]


def build_check_prompt(questions: list[QuizQuestion]) -> str:
    """The questions and options, numbered, without the answer key or explanations."""
    return "\n\n".join(
        f"Question {n}: {q.question}\n" + "\n".join(f"{i}. {option}" for i, option in enumerate(q.options))
        for n, q in enumerate(questions, start=1)
    )


def parse_check(raw: str | None, count: int) -> list[AnswerCheck]:
    """Validate the checker's output. Raises InvalidQuizOutput if it can't be used."""
    if not raw or not raw.strip():
        raise InvalidQuizOutput("empty answer check")
    try:
        checks = _CheckResponse.model_validate(json.loads(raw)).checks
    except (json.JSONDecodeError, ValidationError) as exc:
        raise InvalidQuizOutput(f"answer check unusable: {exc}") from exc
    if len(checks) != count:
        raise InvalidQuizOutput(f"answer check covered {len(checks)} of {count} questions")
    return checks


def check_answers(questions: list[QuizQuestion], timeout: float) -> list[AnswerCheck]:
    """Ask the model to answer each question independently. Raises on any failure."""
    messages = [
        {"role": "system", "content": CHECK_PROMPT},
        {"role": "user", "content": build_check_prompt(questions)},
    ]
    raw = call_groq(
        messages,
        timeout=timeout,
        temperature=0,
        reasoning_effort=get_settings().groq_check_reasoning_effort,
        max_completion_tokens=CHECK_MAX_COMPLETION_TOKENS,
    )
    return parse_check(raw, len(questions))


def apply_check(topic_id: str, questions: list[QuizQuestion], checks: list[AnswerCheck]) -> GeneratedQuestions | None:
    """Keep the questions that passed and replace the rest from the fallback bank, in place."""
    failed = [i for i, (q, c) in enumerate(zip(questions, checks, strict=True)) if not c.passes(q.correct)]
    for i in failed:
        logger.warning(
            "Quiz for %s: question %d failed the answer check (key %d, checker %s, sound=%s): %s",
            topic_id, i + 1, questions[i].correct, sorted(checks[i].correct), checks[i].sound, checks[i].reason,
        )
    if not failed:
        return GeneratedQuestions(questions, "ai")
    if len(failed) == len(questions):
        return None
    taken = {normalise(q.question) for q in questions}
    bank = [q for q in all_fallback_questions(topic_id) if normalise(q.question) not in taken]
    if len(bank) < len(failed):
        return None
    mixed = list(questions)
    for i, replacement in zip(failed, bank, strict=False):
        mixed[i] = replacement
    return GeneratedQuestions(mixed, "mixed")


def fallback_questions(topic_id: str) -> list[QuizQuestion] | None:
    items = FALLBACK_QUESTIONS.get(topic_id)
    if not items:
        return None
    return QuizContent.model_validate({"questions": items[:QUESTIONS_PER_QUIZ]}).questions


def all_fallback_questions(topic_id: str) -> list[QuizQuestion]:
    """Every curated question for a topic (replacements for AI questions that fail the check)."""
    return [QuizQuestion.model_validate(item) for item in FALLBACK_QUESTIONS.get(topic_id, [])]


def _checked(topic_id: str, questions: list[QuizQuestion], left: float) -> GeneratedQuestions | None:
    """The quiz after the answer check, or None to use the fallback bank (no time to check, the
    check failed, or every question was rejected). A check that fails is not retried: the learner
    is already waiting, and unchecked questions are never served."""
    if left <= 1:
        logger.warning("Quiz for %s: no time left for the answer check; using fallback", topic_id)
        return None
    try:
        checks = check_answers(questions, min(CHECK_TIMEOUT_SECONDS, left))
    except (InvalidQuizOutput, APIStatusError, APIConnectionError, APITimeoutError) as exc:
        logger.warning("Quiz for %s: answer check failed (%s); using fallback", topic_id, exc)
        return None
    checked = apply_check(topic_id, questions, checks)
    if checked is None:
        logger.warning("Quiz for %s: too many questions failed the answer check; using fallback", topic_id)
    return checked


def generate_questions(topic: TopicInfo, domain_name: str) -> GeneratedQuestions | None:
    """3 validated questions for a topic: from Groq when possible, otherwise the fallback bank.

    Invalid output is retried up to MAX_RETRIES times. Connection problems, timeouts, auth
    errors and rate limits go straight to the fallback (retrying an unreachable or refusing
    service would only make the learner wait). With the answer check on, a generated quiz is
    checked before it is used (see apply_check), and one that can't be checked is not used.
    Returns None only when neither source has questions.
    """
    settings = get_settings()
    if settings.groq_api_key.strip():
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(topic, domain_name)},
        ]
        reserve = CHECK_RESERVE_SECONDS if settings.quiz_answer_check else 0.0
        started = time.monotonic()
        for attempt in range(1, MAX_RETRIES + 2):
            remaining = TOTAL_BUDGET_SECONDS - reserve - (time.monotonic() - started)
            if remaining <= 1:
                logger.warning("Quiz generation for %s out of time after %d attempt(s)", topic.id, attempt - 1)
                break
            try:
                raw = call_groq(messages, timeout=min(REQUEST_TIMEOUT_SECONDS, remaining))
                questions = parse_quiz(raw)
                logger.info("Quiz for %s generated by %s on attempt %d", topic.id, settings.groq_model, attempt)
                if not settings.quiz_answer_check:
                    return GeneratedQuestions(questions, "ai")
                checked = _checked(topic.id, questions, TOTAL_BUDGET_SECONDS - (time.monotonic() - started))
                if checked is not None:
                    return checked
                break
            except InvalidQuizOutput as exc:
                logger.warning("Quiz for %s: attempt %d invalid (%s)", topic.id, attempt, exc)
            except APIStatusError as exc:
                if exc.status_code == 400:
                    # JSON mode reports output that failed JSON validation as a 400 - retry it.
                    logger.warning("Quiz for %s: attempt %d rejected by Groq (%s)", topic.id, attempt, exc)
                    continue
                logger.warning("Quiz for %s: Groq returned HTTP %s; using fallback", topic.id, exc.status_code)
                break
            except (APIConnectionError, APITimeoutError) as exc:
                logger.warning("Quiz for %s: Groq unreachable (%s); using fallback", topic.id, type(exc).__name__)
                break
    else:
        logger.info("GROQ_API_KEY not set; using fallback questions for %s", topic.id)

    questions = fallback_questions(topic.id)
    if questions is None:
        logger.error("No fallback questions for %s", topic.id)
        return None
    return GeneratedQuestions(questions, "fallback")
