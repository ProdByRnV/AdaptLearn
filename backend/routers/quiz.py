from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from db.postgres import get_db
from schemas.common import ErrorResponse
from schemas.quiz import GeneratedQuizResponse, QuizSubmitRequest, QuizSubmitResponse
from services import quiz_service
from services.auth_service import CurrentUser
from services.quiz_service import (
    QuizAlreadySubmittedError,
    QuizExpiredError,
    QuizNotFoundError,
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


@router.get(
    "/generate/{topic_id}",
    response_model=GeneratedQuizResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Topic is still locked"},
        404: {"model": ErrorResponse, "description": "Topic not found"},
        503: {"model": ErrorResponse, "description": "Quiz generation failed and no fallback is available"},
    },
)
def generate_quiz(
    topic_id: Annotated[str, Path(min_length=1, max_length=100)],
    current_user: CurrentUser,
    db: DbSession,
) -> GeneratedQuizResponse:
    try:
        quiz = quiz_service.create_quiz(db, current_user.id, topic_id)
    except TopicNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Topic '{topic_id}' not found")
    except TopicLockedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Topic is still locked. Complete its prerequisites first.",
        )
    except QuizUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Quiz generation is temporarily unavailable. Please try again shortly.",
        )
    return GeneratedQuizResponse.model_validate(quiz)


@router.post(
    "/submit",
    response_model=QuizSubmitResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Quiz not found (or not yours)"},
        409: {"model": ErrorResponse, "description": "Quiz already submitted"},
        410: {"model": ErrorResponse, "description": "Quiz session expired"},
        503: {"model": ErrorResponse, "description": "A database is unavailable; nothing was saved"},
    },
)
def submit_quiz(payload: QuizSubmitRequest, current_user: CurrentUser, db: DbSession) -> QuizSubmitResponse:
    try:
        result = quiz_service.submit_quiz(db, current_user.id, payload.quiz_id, payload.answers)
    except QuizNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    except QuizAlreadySubmittedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This quiz has already been submitted")
    except QuizExpiredError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="This quiz has expired. Start a new quiz for this topic."
        )
    return QuizSubmitResponse.model_validate(result)
