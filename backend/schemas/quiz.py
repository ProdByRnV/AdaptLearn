from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StringConstraints, field_validator, model_validator

from schemas.topics import RecommendedTopic, ResourceOut, StatusValue
from services.proctoring import CLIENT_EVENT_TYPES

QUESTIONS_PER_QUIZ = 3
OPTIONS_PER_QUESTION = 4

NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


def _normalise(text: str) -> str:
    return " ".join(text.lower().split())


# --- Internal: quiz content with answers (LLM output, fallback bank, quiz_sessions) ---

class QuizQuestion(BaseModel):
    """One question including its answer key. Never sent to the browser before submission."""

    question: NonEmpty
    options: list[NonEmpty] = Field(min_length=OPTIONS_PER_QUESTION, max_length=OPTIONS_PER_QUESTION)
    # StrictInt: reject "1", 1.0 and True - an LLM returning those is a malformed answer key.
    correct: StrictInt = Field(ge=0, le=OPTIONS_PER_QUESTION - 1)
    explanation: NonEmpty

    @field_validator("options")
    @classmethod
    def options_are_distinct(cls, options: list[str]) -> list[str]:
        if len({_normalise(o) for o in options}) != len(options):
            raise ValueError("options must be distinct")
        return options


class QuizContent(BaseModel):
    questions: list[QuizQuestion] = Field(min_length=QUESTIONS_PER_QUIZ, max_length=QUESTIONS_PER_QUIZ)

    @model_validator(mode="after")
    def questions_are_distinct(self) -> "QuizContent":
        if len({_normalise(q.question) for q in self.questions}) != len(self.questions):
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
    source: Literal["ai", "fallback"] | None = Field(
        default=None,
        description="'ai' (LLM) or 'fallback' (curated bank); only reported when the quiz is generated",
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
