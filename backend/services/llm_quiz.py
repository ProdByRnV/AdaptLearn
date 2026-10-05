"""Quiz question generation with Groq, validation, retries and a curated fallback.

Flow (ARCHITECTURE.md section 14):
  Groq response -> strip accidental code fences -> json.loads -> Pydantic schema
  -> business validation -> accept, or retry (max 2 retries) -> fallback question bank
"""

import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Literal

from groq import APIConnectionError, APIStatusError, APITimeoutError, Groq
from pydantic import ValidationError

from config import get_settings
from schemas.quiz import QUESTIONS_PER_QUIZ, QuizContent, QuizQuestion
from seed.fallback_questions import FALLBACK_QUESTIONS
from services.topic_service import TopicInfo

logger = logging.getLogger("adaptlearn")

MAX_RETRIES = 2  # after the initial attempt
REQUEST_TIMEOUT_SECONDS = 10.0
# Stop retrying once this much time has passed, so the browser (15s timeout) still gets
# a quiz from the fallback bank instead of an error.
TOTAL_BUDGET_SECONDS = 12.0
TEMPERATURE = 0.7
MAX_COMPLETION_TOKENS = 1500

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
Questions should test understanding, not obscure trivia, and match the stated difficulty."""

DIFFICULTY_LABELS = {1: "beginner", 2: "early intermediate", 3: "intermediate", 4: "advanced"}

_CODE_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL | re.IGNORECASE)


class InvalidQuizOutput(ValueError):
    pass


@dataclass(frozen=True)
class GeneratedQuestions:
    questions: list[QuizQuestion]
    source: Literal["ai", "fallback"]


def build_user_prompt(topic: TopicInfo, domain_name: str) -> str:
    level = DIFFICULTY_LABELS.get(topic.difficulty, "intermediate")
    return (
        f"Domain: {domain_name}\n"
        f"Topic: {topic.name}\n"
        f"Description: {topic.description}\n"
        f"Difficulty: {topic.difficulty} of 4 ({level})"
    )


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


def call_groq(messages: list[dict[str, str]], timeout: float) -> str | None:
    """One chat completion in JSON mode. Separate function so tests can replace it."""
    settings = get_settings()
    client = Groq(api_key=settings.groq_api_key, timeout=timeout, max_retries=0)
    extra: dict[str, Any] = {}
    if settings.groq_reasoning_effort:
        extra["reasoning_effort"] = settings.groq_reasoning_effort
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        temperature=TEMPERATURE,
        max_completion_tokens=MAX_COMPLETION_TOKENS,
        response_format={"type": "json_object"},
        **extra,
    )
    return response.choices[0].message.content


def fallback_questions(topic_id: str) -> list[QuizQuestion] | None:
    items = FALLBACK_QUESTIONS.get(topic_id)
    if not items:
        return None
    return QuizContent.model_validate({"questions": items[:QUESTIONS_PER_QUIZ]}).questions


def generate_questions(topic: TopicInfo, domain_name: str) -> GeneratedQuestions | None:
    """3 validated questions for a topic: from Groq when possible, otherwise the fallback bank.

    Invalid output is retried up to MAX_RETRIES times. Connection problems, timeouts, auth
    errors and rate limits go straight to the fallback (retrying an unreachable or refusing
    service would only make the learner wait). Returns None only when neither source has questions.
    """
    settings = get_settings()
    if settings.groq_api_key.strip():
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(topic, domain_name)},
        ]
        started = time.monotonic()
        for attempt in range(1, MAX_RETRIES + 2):
            remaining = TOTAL_BUDGET_SECONDS - (time.monotonic() - started)
            if remaining <= 1:
                logger.warning("Quiz generation for %s out of time after %d attempt(s)", topic.id, attempt - 1)
                break
            try:
                raw = call_groq(messages, timeout=min(REQUEST_TIMEOUT_SECONDS, remaining))
                questions = parse_quiz(raw)
                logger.info("Quiz for %s generated by %s on attempt %d", topic.id, settings.groq_model, attempt)
                return GeneratedQuestions(questions, "ai")
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
