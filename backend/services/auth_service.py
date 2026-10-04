import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import get_settings
from db.postgres import get_db
from models import User
from schemas.auth import MAX_PASSWORD_BYTES, RegisterRequest

logger = logging.getLogger("adaptlearn")

INVALID_CREDENTIALS = "Incorrect email or password"
NOT_AUTHENTICATED = "Not authenticated"
INVALID_TOKEN = "Invalid authentication token"
TOKEN_EXPIRED = "Session expired. Please log in again."

# Checked against when the email is unknown, so a failed login takes the same time
# whether or not the account exists (prevents probing for registered emails).
_DUMMY_HASH = bcrypt.hashpw(b"adaptlearn-timing-equaliser", bcrypt.gensalt()).decode()

bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Paste the `access_token` returned by /api/auth/register or /api/auth/login.",
)


class EmailAlreadyRegisteredError(Exception):
    pass


# --- Passwords ---------------------------------------------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    encoded = password.encode("utf-8")
    if len(encoded) > MAX_PASSWORD_BYTES:
        return False
    try:
        return bcrypt.checkpw(encoded, hashed_password.encode("utf-8"))
    except ValueError:
        return False


# --- Tokens ------------------------------------------------------------------

def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {"sub": str(user_id), "iat": now, "exp": expires}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int:
    """Return the user id in a valid token. Raises jwt.ExpiredSignatureError / jwt.InvalidTokenError."""
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["sub", "exp", "iat"]},
    )
    try:
        return int(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise jwt.InvalidTokenError("Token subject is not a user id") from exc


# --- Users -------------------------------------------------------------------

def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == normalize_email(email)))


def register_user(db: Session, data: RegisterRequest) -> User:
    if get_user_by_email(db, data.email) is not None:
        raise EmailAlreadyRegisteredError
    user = User(username=data.username, email=data.email, hashed_password=hash_password(data.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        # Two registrations for the same email at the same moment: the unique constraint decides.
        db.rollback()
        raise EmailAlreadyRegisteredError from exc
    db.refresh(user)
    logger.info("Registered user id=%s", user.id)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user is None:
        verify_password(password, _DUMMY_HASH)
        return None
    return user if verify_password(password, user.hashed_password) else None


# --- Dependency --------------------------------------------------------------

def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized(NOT_AUTHENTICATED)
    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise _unauthorized(TOKEN_EXPIRED)
    except jwt.InvalidTokenError:
        raise _unauthorized(INVALID_TOKEN)
    user = db.get(User, user_id)
    if user is None:
        # Valid signature but the account no longer exists.
        raise _unauthorized(INVALID_TOKEN)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
