from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from db.postgres import get_db
from schemas.common import ErrorResponse
from schemas.topics import GraphResponse, TopicOut, TopicsResponse
from seed.curriculum import DOMAIN
from services import topic_service
from services.auth_service import CurrentUser
from services.topic_service import UnknownDomainError

router = APIRouter(
    prefix="/topics",
    tags=["topics"],
    responses={
        401: {"model": ErrorResponse, "description": "Missing, invalid or expired token"},
        404: {"model": ErrorResponse, "description": "Unknown domain"},
        503: {"model": ErrorResponse, "description": "Curriculum service unavailable"},
    },
)

DbSession = Annotated[Session, Depends(get_db)]
DomainParam = Annotated[str, Query(description="Learning domain")]


def _unknown_domain(domain: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown domain '{domain}'")


@router.get("/all", response_model=TopicsResponse)
def all_topics(current_user: CurrentUser, domain: DomainParam = DOMAIN) -> TopicsResponse:
    try:
        topics = topic_service.get_topics(domain)
    except UnknownDomainError:
        raise _unknown_domain(domain)
    return TopicsResponse(
        domain=domain,
        topics=[
            TopicOut(id=t.id, name=t.name, description=t.description, difficulty=t.difficulty, resources=t.resources)
            for t in topics
        ],
    )


@router.get("/graph", response_model=GraphResponse)
def topic_graph(current_user: CurrentUser, db: DbSession, domain: DomainParam = DOMAIN) -> GraphResponse:
    try:
        graph = topic_service.build_graph(db, current_user.id, domain)
    except UnknownDomainError:
        raise _unknown_domain(domain)
    return GraphResponse.model_validate(graph)
