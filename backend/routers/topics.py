from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from db.postgres import get_db
from schemas.common import ErrorResponse
from schemas.topics import (
    GraphResponse,
    LearningPathResponse,
    MarkKnownRequest,
    MarkKnownResponse,
    TopicOut,
    TopicsResponse,
)
from seed.curriculum import DOMAIN
from services import learning_path, topic_service
from services.auth_service import CurrentUser
from services.learning_path import UnknownTopicsError
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


@router.get("/learning-path", response_model=LearningPathResponse)
def get_learning_path(current_user: CurrentUser, db: DbSession, domain: DomainParam = DOMAIN) -> LearningPathResponse:
    try:
        result = learning_path.get_learning_path(db, current_user.id, domain)
    except UnknownDomainError:
        raise _unknown_domain(domain)
    return LearningPathResponse.model_validate(result)


@router.post(
    "/mark-known",
    response_model=MarkKnownResponse,
    responses={400: {"model": ErrorResponse, "description": "One or more topic ids do not exist"}},
)
def mark_known(payload: MarkKnownRequest, current_user: CurrentUser, db: DbSession) -> MarkKnownResponse:
    try:
        result = learning_path.mark_known(db, current_user.id, payload.domain, payload.topic_ids)
    except UnknownDomainError:
        raise _unknown_domain(payload.domain)
    except UnknownTopicsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown topic ids: {', '.join(exc.topic_ids)}"
        )
    return MarkKnownResponse.model_validate(result)
