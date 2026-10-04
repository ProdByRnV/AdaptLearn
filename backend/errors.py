"""Exception handlers that keep every error response in the shape {"detail": "<message>"}."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from neo4j.exceptions import AuthError, ServiceUnavailable, SessionExpired
from sqlalchemy.exc import InterfaceError, OperationalError

logger = logging.getLogger("adaptlearn")

DB_UNAVAILABLE = "Database is temporarily unavailable. Please try again shortly."
GRAPH_UNAVAILABLE = "Curriculum service is temporarily unavailable. Please try again shortly."
INTERNAL_ERROR = "Something went wrong on our side. Please try again."


def _field_name(loc: tuple) -> str:
    # Drop the location prefix ("body", "query", ...) so messages read "email: ..." not "body.email: ...".
    parts = [str(part) for part in loc if part not in ("body", "query", "path", "header", "cookie")]
    return ".".join(parts) or "request"


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [{"field": _field_name(err["loc"]), "message": err["msg"]} for err in exc.errors()]
    detail = "; ".join(f"{e['field']}: {e['message']}" for e in errors) or "Invalid request"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": detail, "errors": errors},
    )


async def postgres_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("PostgreSQL unavailable during %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": DB_UNAVAILABLE})


async def neo4j_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Neo4j unavailable during %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": GRAPH_UNAVAILABLE})


async def catch_unhandled_errors(request: Request, call_next):
    # Registered as middleware (inside CORS) rather than as an Exception handler, so even
    # 500 responses carry CORS headers and the browser sees the real error.
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Unhandled error during %s %s", request.method, request.url.path)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": INTERNAL_ERROR})


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(OperationalError, postgres_unavailable_handler)
    app.add_exception_handler(InterfaceError, postgres_unavailable_handler)
    for exc_class in (ServiceUnavailable, SessionExpired, AuthError):
        app.add_exception_handler(exc_class, neo4j_unavailable_handler)
