from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from db.postgres import get_db
from schemas.common import ErrorResponse
from schemas.quiz import (
    ActiveQuizResponse,
    AnswerAck,
    AnswerRequest,
    EventsAck,
    EventsRequest,
    QuizInfo,
    QuizQuestionOut,
    QuizSubmitRequest,
    QuizSubmitResponse,
)
from services import quiz_service
from services.auth_service import CurrentUser
from services.quiz_service import (
    QuestionNotOpenError,
    QuizAlreadySubmittedError,
    QuizCompleteError,
    QuizExpiredError,
    QuizNotFoundError,
    QuizRateLimitedError,
    QuizUnavailableError,
    TopicLockedError,
    TopicNotFoundError,
)

router = APIRouter(
    prefix="/quiz",
    tags=["quiz"],
    responses={401: {"model": ErrorResponse, "description": "Missing, invalid or expired token"}},
)

DbSession = Annotated[Session, Depends(get_db)]
QuizId = Annotated[UUID, Path(description="The quiz_id returned by /quiz/generate")]

# Errors shared by every endpoint that works on an existing quiz.
_SESSION_ERRORS = {
    404: {"model": ErrorResponse, "description": "Quiz not found (or not yours)"},
    409: {"model": ErrorResponse, "description": "Quiz already submitted"},
    410: {"model": ErrorResponse, "description": "Quiz session expired"},
}


def _session_error(exc: Exception) -> HTTPException:
    if isinstance(exc, QuizNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    if isinstance(exc, QuizAlreadySubmittedError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This quiz has already been submitted")
    if isinstance(exc, QuizExpiredError):
        return HTTPException(
            status_code=status.HTTP_410_GONE, detail="This quiz has expired. Start a new quiz for this topic."
        )
    raise exc


SESSION_EXCEPTIONS = (QuizNotFoundError, QuizAlreadySubmittedError, QuizExpiredError)


@router.get(
    "/generate/{topic_id}",
    response_model=QuizInfo,
    responses={
        403: {"model": ErrorResponse, "description": "Topic is still locked"},
        404: {"model": ErrorResponse, "description": "Topic not found"},
        429: {"model": ErrorResponse, "description": "Too many quizzes started in the last hour (see Retry-After)"},
        503: {"model": ErrorResponse, "description": "Quiz generation failed and no fallback is available"},
    },
)
def generate_quiz(
    topic_id: Annotated[str, Path(min_length=1, max_length=100)],
    current_user: CurrentUser,
    db: DbSession,
) -> QuizInfo:
    """Create a proctored quiz. Returns no questions: fetch them one at a time with /next.
    Starting a quiz abandons any unfinished one, which then never counts."""
    try:
        quiz = quiz_service.create_quiz(db, current_user.id, topic_id)
    except TopicNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Topic '{topic_id}' not found")
    except TopicLockedError as exc:
        detail = "Topic is still locked. Complete its prerequisites first"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{detail}: {', '.join(exc.missing)}." if exc.missing else f"{detail}.",
        )
    except QuizRateLimitedError as exc:
        minutes = max(1, round(exc.retry_after_seconds / 60))
        what = "for this topic" if exc.scope == "topic" else "overall"
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many quizzes started {what} in the last hour. Try again in about {minutes} minute(s).",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        )
    except QuizUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Quiz generation is temporarily unavailable. Please try again shortly.",
        )
    return QuizInfo.model_validate(quiz)


@router.get("/active", response_model=ActiveQuizResponse)
def active_quiz(current_user: CurrentUser, db: DbSession) -> ActiveQuizResponse:
    """The learner's unfinished quiz, so the page can resume it after a reload."""
    return ActiveQuizResponse(active=quiz_service.get_active_quiz(db, current_user.id))


@router.post(
    "/{quiz_id}/next",
    response_model=QuizQuestionOut,
    responses={**_SESSION_ERRORS, 409: {"model": ErrorResponse, "description": "Already submitted, or every question is done"}},
)
def next_question(quiz_id: QuizId, current_user: CurrentUser, db: DbSession) -> QuizQuestionOut:
    """Serve the current question and start its timer. Calling again returns the same question with
    the remaining time; earlier questions can't be reopened."""
    try:
        question = quiz_service.next_question(db, current_user.id, quiz_id)
    except SESSION_EXCEPTIONS as exc:
        raise _session_error(exc)
    except QuizCompleteError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="All questions have been answered. Submit the quiz."
        )
    return QuizQuestionOut.model_validate(question)


@router.post(
    "/{quiz_id}/answer",
    response_model=AnswerAck,
    responses={**_SESSION_ERRORS, 409: {"model": ErrorResponse, "description": "Already submitted, or question not open"}},
)
def answer_question(quiz_id: QuizId, payload: AnswerRequest, current_user: CurrentUser, db: DbSession) -> AnswerAck:
    """Lock in the answer to the current question. After its deadline the answer is refused and
    the question counts as wrong."""
    try:
        ack = quiz_service.record_answer(db, current_user.id, quiz_id, payload.question_id, payload.answer)
    except SESSION_EXCEPTIONS as exc:
        raise _session_error(exc)
    except QuestionNotOpenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That question is not open: it hasn't been served yet, or it was already answered or timed out.",
        )
    return AnswerAck.model_validate(ack)


@router.post("/{quiz_id}/events", response_model=EventsAck, responses=_SESSION_ERRORS)
def report_events(quiz_id: QuizId, payload: EventsRequest, current_user: CurrentUser, db: DbSession) -> EventsAck:
    """Proctoring signals from the quiz page: heartbeats every few seconds, plus tab switches,
    fullscreen exits, copy/paste attempts and similar."""
    try:
        ack = quiz_service.record_events(
            db, current_user.id, quiz_id, [event.model_dump() for event in payload.events]
        )
    except SESSION_EXCEPTIONS as exc:
        raise _session_error(exc)
    return EventsAck.model_validate(ack)


@router.post(
    "/submit",
    response_model=QuizSubmitResponse,
    responses={**_SESSION_ERRORS, 503: {"model": ErrorResponse, "description": "A database is unavailable; nothing was saved"}},
)
def submit_quiz(payload: QuizSubmitRequest, current_user: CurrentUser, db: DbSession) -> QuizSubmitResponse:
    """Score the quiz and judge its integrity. A verified attempt updates mastery and progress; a
    flagged one is recorded but changes nothing."""
    try:
        result = quiz_service.submit_quiz(db, current_user.id, payload.quiz_id)
    except SESSION_EXCEPTIONS as exc:
        raise _session_error(exc)
    return QuizSubmitResponse.model_validate(result)
