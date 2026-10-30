from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.orm import Session

from db.postgres import get_db
from schemas.common import ErrorResponse
from schemas.domains import CatalogueResponse, EnrolmentResponse, HomeResponse
from services import domain_service, enrolment_service
from services.auth_service import CurrentUser
from services.topic_service import UnknownDomainError, domain_name

router = APIRouter(
    tags=["domains"],
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid or expired token"},
        503: {"model": ErrorResponse, "description": "A database is unavailable"},
    },
)

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/domains", response_model=CatalogueResponse)
def catalogue(current_user: CurrentUser, db: DbSession) -> CatalogueResponse:
    """Every domain with its size, whether the learner joined it and what they already know there."""
    return CatalogueResponse.model_validate(domain_service.build_catalogue(db, current_user.id))


@router.post(
    "/domains/{domain_id}/join",
    response_model=EnrolmentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        200: {"model": EnrolmentResponse, "description": "Already joined; nothing changed"},
        404: {"model": ErrorResponse, "description": "Unknown domain"},
    },
)
def join(
    domain_id: Annotated[str, Path(min_length=1, max_length=100)],
    current_user: CurrentUser,
    db: DbSession,
    response: Response,
) -> EnrolmentResponse:
    """Join a domain. Onboarding (POST /topics/mark-known) then records what the learner already knows."""
    try:
        enrolment, joined_now = enrolment_service.join_domain(db, current_user.id, domain_id)
    except UnknownDomainError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown domain '{domain_id}'")
    if not joined_now:
        response.status_code = status.HTTP_200_OK
    return EnrolmentResponse(
        domain=domain_id,
        domain_name=domain_name(domain_id),
        joined_at=enrolment.joined_at,
        onboarded=enrolment.onboarded_at is not None,
    )


@router.get("/home", response_model=HomeResponse)
def home(current_user: CurrentUser, db: DbSession) -> HomeResponse:
    """Progress in each joined domain, up next across them, domain suggestions and recent quizzes."""
    return HomeResponse.model_validate(domain_service.build_home(db, current_user.id))
