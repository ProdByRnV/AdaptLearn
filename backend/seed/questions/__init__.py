"""Curated fallback questions, one module per domain; a topic's questions live with its home domain.

They are used when Groq is unavailable or no API key is configured, and to replace AI questions
that fail the answer check. Each is written as (question, correct answer, three wrong answers,
explanation); the correct answer is listed first only for readability. Options are shuffled every
time a quiz is served, so the stored position reveals nothing.
"""

from typing import Any

Bank = dict[str, list[dict[str, Any]]]


def q(question: str, answer: str, wrong: tuple[str, str, str], explanation: str) -> dict[str, Any]:
    return {"question": question, "options": [answer, *wrong], "correct": 0, "explanation": explanation}
