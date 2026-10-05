from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from db.postgres import get_db
from schemas.common import ErrorResponse
from schemas.progress import DashboardResponse, ProgressAllResponse
from seed.curriculum import DOMAIN
from services import progress_service
from services.auth_service import CurrentUser
from services.topic_service import UnknownDomainError

router = APIRouter(
    prefix="/progress",
    tags=["progress"],
    responses={401: {"model": ErrorResponse, "description": "Missing, invalid or expired token"}},
)

DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Unknown domain"},
        503: {"model": ErrorResponse, "description": "A database is unavailable"},
    },
)
def dashboard(
    current_user: CurrentUser, db: DbSession, domain: Annotated[str, Query(description="Learning domain")] = DOMAIN
) -> DashboardResponse:
    try:
        result = progress_service.build_dashboard(db, current_user.id, domain)
    except UnknownDomainError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown domain '{domain}'")
    return DashboardResponse.model_validate(result)


@router.get("/all", response_model=ProgressAllResponse)
def all_progress(current_user: CurrentUser, db: DbSession) -> ProgressAllResponse:
    return ProgressAllResponse.model_validate(progress_service.list_progress(db, current_user.id))
