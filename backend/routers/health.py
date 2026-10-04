import logging
from collections.abc import Callable

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from db import neo4j_db, postgres
from schemas.health import HealthResponse, ServiceStatus

logger = logging.getLogger("adaptlearn")

router = APIRouter(tags=["health"])


def _probe(name: str, check: Callable[[], None]) -> ServiceStatus:
    try:
        check()
        return "ok"
    except Exception as exc:
        logger.warning("Health check: %s unavailable: %s", name, exc)
        return "unavailable"


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={503: {"model": HealthResponse, "description": "A database is unreachable"}},
)
def health() -> JSONResponse:
    result = HealthResponse(
        status="ok",
        api="ok",
        postgres=_probe("PostgreSQL", postgres.check_connection),
        neo4j=_probe("Neo4j", neo4j_db.check_connection),
    )
    if result.postgres != "ok" or result.neo4j != "ok":
        result.status = "degraded"
        result.detail = "One or more services are unavailable"
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=result.model_dump())
    return JSONResponse(status_code=status.HTTP_200_OK, content=result.model_dump(exclude_none=True))
