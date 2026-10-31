import re
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StringConstraints, field_validator, model_validator

from schemas.topics import RecommendedTopic, ResourceOut, StatusValue
from services.proctoring import CLIENT_EVENT_TYPES

QUESTIONS_PER_QUIZ = 3
OPTIONS_PER_QUESTION = 4

NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


def normalise(text: str) -> str:
    """Lowercase with single spaces: how questions and options are compared for duplicates."""
    return " ".join(text.lower().split())


_LETTER_ONLY = re.compile(r"^\(?[A-D][).:]?$", re.IGNORECASE)


def _unescape_code(text: str) -> str:
    """Models sometimes double-escape the line breaks in a code block, sending a literal backslash-n.
    Text with a code fence but no real line break can only mean that."""
    if "```" in text and "\n" not in text and "\\n" in text:
        return text.replace("\\n", "\n")
    return text


_FENCED_BLOCK = re.compile(r"\n?```[\w+-]*[^\S\n]*\n?(.*?)\n?```", re.DOTALL)
_COMMENT_LINE = re.compile(r"^\s*(#|//|--|/\*|\*|<!--)")


def _drop_placeholder_blocks(text: str) -> str:
    """Models sometimes append an empty block or one holding only a comment such as "# your answer".
    A block with nothing but blank and comment lines shows the learner nothing to reason about."""

    def keep_or_drop(match: re.Match) -> str:
        lines = [line for line in match.group(1).splitlines() if line.strip()]
        return "" if all(_COMMENT_LINE.match(line) for line in lines) else match.group(0)

    return _FENCED_BLOCK.sub(keep_or_drop, text).strip()


# Maths is written in LaTeX between \( and \) inside a sentence, or \[ and \] on its own line.
# Delimiters inside code (fenced blocks and `inline code`) are code, not maths.
_CODE = re.compile(r"```.*?```|`[^`\n]+`", re.DOTALL)
_MATH_SPAN = re.compile(r"\\\(.*?\\\)|\\\[.*?\\\]", re.DOTALL)
_MATH_DELIMITER = re.compile(r"\\[()\[\]]")
_CLOSER = {"\\(": "\\)", "\\[": "\\]"}
# JSON turns a LaTeX command written with a single backslash into a control character: \frac and
# \beta arrive as a form feed or backspace plus "rac"/"eta"; \times, \nabla and \rho as a tab, line
# break or carriage return plus letters.
_LOST_BACKSLASH = {"\t": "\\t", "\n": "\\n", "\r": "\\r"}


def repair_maths(text: str) -> str:
    """Give LaTeX commands back the backslash JSON turned into a control character. Form feeds and
    backspaces never belong in quiz text; a tab, line break or carriage return followed directly by
    a letter inside maths can only be a command."""
    text = text.replace("\f", "\\f").replace("\b", "\\b")

    def fix(span: re.Match) -> str:
        return re.sub(r"[\t\n\r](?=[A-Za-z])", lambda m: _LOST_BACKSLASH[m.group(0)], span.group(0))

    return _MATH_SPAN.sub(fix, text)


def maths_problem(text: str) -> str | None:
    """Why the maths delimiters outside code don't pair up (\\( closed by \\), \\[ by \\], none
    nested), or None when they do."""
    opened = None
    for token in _MATH_DELIMITER.findall(_CODE.sub("", text)):
        if token in _CLOSER:
            if opened:
                return f"maths opened with {opened} isn't closed before {token}"
            opened = token
        elif opened and _CLOSER[opened] == token:
            opened = None
        else:
            return f"{token} closes maths that wasn't opened"
    return f"maths opened with {opened} is never closed" if opened else None


def _repaired_maths(text: str) -> str:
    text = repair_maths(text)
    problem = maths_problem(text)
    if problem:
        raise ValueError(problem)
    return text


# --- Internal: quiz content with answers (LLM output, fallback bank, quiz_sessions) ---

class QuizQuestion(BaseModel):
    """One question including its answer key. Never sent to the browser before submission."""

    question: NonEmpty
    options: list[NonEmpty] = Field(min_length=OPTIONS_PER_QUESTION, max_length=OPTIONS_PER_QUESTION)
    # StrictInt: reject "1", 1.0 and True - an LLM returning those is a malformed answer key.
    correct: StrictInt = Field(ge=0, le=OPTIONS_PER_QUESTION - 1)
    explanation: NonEmpty

    @field_validator("question", "explanation")
    @classmethod
    def repair_code_blocks(cls, text: str) -> str:
        repaired = _drop_placeholder_blocks(_unescape_code(text))
        if not repaired:
            raise ValueError("must contain text, not only an empty code block")
        return _repaired_maths(repaired)

    @field_validator("options")
    @classmethod
    def options_are_distinct(cls, options: list[str]) -> list[str]:
        if len({normalise(o) for o in options}) != len(options):
            raise ValueError("options must be distinct")
        # ["D", "A", "B", "C"] points at choices written into the question, which clash with the
        # letters the quiz page shows next to each option.
        if all(_LETTER_ONLY.match(o) for o in options):
            raise ValueError("options must be answers, not letters referring to the question")
        return [_repaired_maths(_unescape_code(o)) for o in options]


class QuizContent(BaseModel):
    questions: list[QuizQuestion] = Field(min_length=QUESTIONS_PER_QUIZ, max_length=QUESTIONS_PER_QUIZ)

    @model_validator(mode="after")
    def questions_are_distinct(self) -> "QuizContent":
        if len({normalise(q.question) for q in self.questions}) != len(self.questions):
            raise ValueError("questions must be distinct")
        return self


# --- API: what the browser receives ------------------------------------------------
# Questions are served one at a time (proctoring, Phase 12.5), so no response before
# submission ever contains more than one question, and none contains an answer.

class QuizTopicOut(BaseModel):
    id: str
    name: str


class ProctoringRule(BaseModel):
    code: str
    penalty: int
    message: str


class ProctoringInfo(BaseModel):
    verified_threshold: int = Field(description="Attempts scoring at least this much count; lower scores are flagged")
    heartbeat_interval_seconds: int = Field(description="How often the quiz page must send a heartbeat event")
    rules: list[ProctoringRule]


class QuizInfo(BaseModel):
    quiz_id: UUID
    topic: QuizTopicOut
    total_questions: int
    answered_questions: int = Field(description="Questions already answered or timed out")
    seconds_per_question: int
    expires_in_seconds: int
    source: Literal["ai", "fallback", "mixed"] | None = Field(
        default=None,
        description=(
            "'ai' (LLM, every question passed the answer check), 'fallback' (curated bank) or 'mixed' (AI "
            "questions, those that failed the answer check replaced from the bank); only reported when the "
            "quiz is generated"
        ),
    )
    proctoring: ProctoringInfo


class ActiveQuizResponse(BaseModel):
    active: QuizInfo | None = Field(description="The learner's unfinished quiz, or null")


class QuizQuestionOut(BaseModel):
    question_id: int
    number: int = Field(description="1-based position in the quiz")
    total: int
    question: str
    options: list[str]
    deadline: datetime
    seconds_remaining: int


AnswerIndex = Annotated[StrictInt, Field(ge=0, le=OPTIONS_PER_QUESTION - 1)]


class AnswerRequest(BaseModel):
    question_id: Annotated[StrictInt, Field(ge=0, le=QUESTIONS_PER_QUIZ - 1)]
    answer: AnswerIndex


class AnswerAck(BaseModel):
    question_id: int
    accepted: bool = Field(description="False when the deadline had passed; the question then counts as wrong")
    timed_out: bool
    remaining_questions: int


class ProctoringEventIn(BaseModel):
    type: Literal[CLIENT_EVENT_TYPES]  # type: ignore[valid-type]
    occurred_at: datetime | None = Field(default=None, description="When the page saw it (informational)")
    duration_ms: Annotated[int, Field(ge=0, le=24 * 3600 * 1000)] | None = None
    details: dict[str, Any] | None = None


class EventsRequest(BaseModel):
    events: list[ProctoringEventIn] = Field(min_length=1, max_length=100)


class EventsAck(BaseModel):
    accepted: int
    ignored: int = Field(description="Events dropped because the per-quiz limit was reached")


# --- Submission ---------------------------------------------------------------------

class QuizSubmitRequest(BaseModel):
    # Answers are recorded one by one via /answer; an old-style "answers" list is rejected.
    model_config = ConfigDict(extra="forbid")

    quiz_id: UUID


class AnswerFeedback(BaseModel):
    question: str
    options: list[str]
    selected: int | None = Field(description="null when the question was not answered in time")
    correct: int
    is_correct: bool
    timed_out: bool
    explanation: str


class IntegrityOut(BaseModel):
    score: int
    verdict: Literal["verified", "flagged"]
    counted: bool = Field(description="Whether this attempt changed mastery and progress")
    reasons: list[dict[str, Any]]


class QuizSubmitResponse(BaseModel):
    topic_id: str
    score: int
    total: int
    passed: bool
    p_know_before: float
    p_know_after: float
    mastered: bool
    status: StatusValue
    needs_attention: bool
    feedback: list[AnswerFeedback]
    recommended_resources: list[ResourceOut] = Field(
        description="Learning resources for this topic, included when the quiz was failed or the topic needs attention"
    )
    newly_unlocked: list[str] = Field(description="Topic ids this submission unlocked")
    next_topics: list[RecommendedTopic] = Field(description="Next topics to learn (at most 3)")
    integrity: IntegrityOut
