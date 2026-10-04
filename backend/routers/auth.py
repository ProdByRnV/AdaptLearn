from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.postgres import get_db
from schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserOut
from schemas.common import ErrorResponse
from services import auth_service
from services.auth_service import CurrentUser, EmailAlreadyRegisteredError

router = APIRouter(prefix="/auth", tags=["auth"])

DbSession = Annotated[Session, Depends(get_db)]


def _auth_response(user) -> AuthResponse:
    return AuthResponse(access_token=auth_service.create_access_token(user.id), user=UserOut.model_validate(user))


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=AuthResponse,
    responses={409: {"model": ErrorResponse, "description": "Email already registered"}},
)
def register(payload: RegisterRequest, db: DbSession) -> AuthResponse:
    try:
        user = auth_service.register_user(db, payload)
    except EmailAlreadyRegisteredError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")
    return _auth_response(user)


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={401: {"model": ErrorResponse, "description": "Incorrect email or password"}},
)
def login(payload: LoginRequest, db: DbSession) -> AuthResponse:
    user = auth_service.authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=auth_service.INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _auth_response(user)


@router.get(
    "/me",
    response_model=UserOut,
    responses={401: {"model": ErrorResponse, "description": "Missing, invalid or expired token"}},
)
def me(current_user: CurrentUser) -> UserOut:
    return UserOut.model_validate(current_user)
