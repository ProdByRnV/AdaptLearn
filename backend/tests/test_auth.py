from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import select, text

from config import get_settings
from models import User
from services.auth_service import (
    INVALID_CREDENTIALS,
    INVALID_TOKEN,
    NOT_AUTHENTICATED,
    TOKEN_EXPIRED,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

PASSWORD = "StrongPassword123"


def register(client, username="Puja", email="puja@example.com", password=PASSWORD):
    return client.post("/api/auth/register", json={"username": username, "email": email, "password": password})


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# --- Password hashing ---------------------------------------------------------

def test_hash_is_bcrypt_and_not_plaintext():
    hashed = hash_password(PASSWORD)
    assert hashed.startswith("$2b$")
    assert PASSWORD not in hashed


def test_password_verifies():
    assert verify_password(PASSWORD, hash_password(PASSWORD)) is True


def test_wrong_password_does_not_verify():
    assert verify_password("WrongPassword123", hash_password(PASSWORD)) is False


def test_same_password_gets_different_salts():
    assert hash_password(PASSWORD) != hash_password(PASSWORD)


def test_over_72_byte_password_never_verifies():
    assert verify_password("x" * 73, hash_password("x" * 72)) is False


# --- Register ----------------------------------------------------------------

def test_register_success(client, db):
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["username"] == "Puja"
    assert body["user"]["email"] == "puja@example.com"
    assert set(body["user"]) == {"id", "username", "email"}

    stored = db.scalar(select(User).where(User.email == "puja@example.com"))
    assert stored is not None
    assert stored.hashed_password != PASSWORD
    assert verify_password(PASSWORD, stored.hashed_password)


def test_register_token_works_for_me(client):
    token = register(client).json()["access_token"]
    response = client.get("/api/auth/me", headers=bearer(token))
    assert response.status_code == 200
    assert response.json()["email"] == "puja@example.com"


def test_register_normalises_email_and_username(client):
    response = register(client, username="  Puja  ", email="Puja@Example.COM")
    assert response.status_code == 201
    assert response.json()["user"]["email"] == "puja@example.com"
    assert response.json()["user"]["username"] == "Puja"


def test_duplicate_email_rejected(client):
    assert register(client).status_code == 201
    response = register(client, username="Someone else")
    assert response.status_code == 409
    assert response.json() == {"detail": "An account with this email already exists"}


def test_duplicate_email_rejected_case_insensitively(client):
    assert register(client).status_code == 201
    assert register(client, email="PUJA@example.com").status_code == 409


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"email": "puja@example.com", "password": PASSWORD}, "username"),
        ({"username": "   ", "email": "puja@example.com", "password": PASSWORD}, "username"),
        ({"username": "x" * 81, "email": "puja@example.com", "password": PASSWORD}, "username"),
        ({"username": "Puja", "email": "not-an-email", "password": PASSWORD}, "email"),
        ({"username": "Puja", "password": PASSWORD}, "email"),
        ({"username": "Puja", "email": "puja@example.com"}, "password"),
        ({"username": "Puja", "email": "puja@example.com", "password": "short"}, "password"),
        ({"username": "Puja", "email": "puja@example.com", "password": "x" * 73}, "password"),
    ],
)
def test_register_validation_errors(client, payload, field):
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert isinstance(body["detail"], str) and field in body["detail"]
    assert any(error["field"] == field for error in body["errors"])


def test_register_password_too_long_message(client):
    response = register(client, password="é" * 37)  # 74 bytes, only 37 characters
    assert response.status_code == 422
    assert "at most 72 bytes" in response.json()["detail"]


# --- Login -------------------------------------------------------------------

def test_login_success(client):
    register(client)
    response = client.post("/api/auth/login", json={"email": "puja@example.com", "password": PASSWORD})
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "puja@example.com"
    assert client.get("/api/auth/me", headers=bearer(body["access_token"])).status_code == 200


def test_login_email_is_case_insensitive(client):
    register(client)
    response = client.post("/api/auth/login", json={"email": "PUJA@Example.com", "password": PASSWORD})
    assert response.status_code == 200


def test_wrong_password_rejected(client):
    register(client)
    response = client.post("/api/auth/login", json={"email": "puja@example.com", "password": "WrongPassword123"})
    assert response.status_code == 401
    assert response.json() == {"detail": INVALID_CREDENTIALS}


def test_unknown_email_gets_same_error_as_wrong_password(client):
    response = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": PASSWORD})
    assert response.status_code == 401
    assert response.json() == {"detail": INVALID_CREDENTIALS}


def test_login_validation_error(client):
    response = client.post("/api/auth/login", json={"email": "puja@example.com"})
    assert response.status_code == 422


# --- Protected route (/me) ---------------------------------------------------

def test_me_without_token_returns_401(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json() == {"detail": NOT_AUTHENTICATED}
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_with_non_bearer_scheme_returns_401(client):
    token = register(client).json()["access_token"]
    response = client.get("/api/auth/me", headers={"Authorization": f"Basic {token}"})
    assert response.status_code == 401


def test_invalid_token_rejected(client):
    response = client.get("/api/auth/me", headers=bearer("not.a.jwt"))
    assert response.status_code == 401
    assert response.json() == {"detail": INVALID_TOKEN}


def test_expired_token_rejected(client):
    user_id = register(client).json()["user"]["id"]
    expired = create_access_token(user_id, expires_delta=timedelta(seconds=-1))
    response = client.get("/api/auth/me", headers=bearer(expired))
    assert response.status_code == 401
    assert response.json() == {"detail": TOKEN_EXPIRED}


def test_token_signed_with_wrong_secret_rejected(client):
    user_id = register(client).json()["user"]["id"]
    now = datetime.now(timezone.utc)
    forged = jwt.encode(
        {"sub": str(user_id), "iat": now, "exp": now + timedelta(hours=1)}, "x" * 64, algorithm="HS256"
    )
    response = client.get("/api/auth/me", headers=bearer(forged))
    assert response.status_code == 401
    assert response.json() == {"detail": INVALID_TOKEN}


def test_unsigned_token_rejected(client):
    user_id = register(client).json()["user"]["id"]
    now = datetime.now(timezone.utc)
    unsigned = jwt.encode({"sub": str(user_id), "iat": now, "exp": now + timedelta(hours=1)}, None, algorithm="none")
    assert client.get("/api/auth/me", headers=bearer(unsigned)).status_code == 401


def test_token_without_expiry_rejected(client):
    user_id = register(client).json()["user"]["id"]
    settings = get_settings()
    no_exp = jwt.encode({"sub": str(user_id), "iat": datetime.now(timezone.utc)}, settings.jwt_secret_key,
                        algorithm=settings.jwt_algorithm)
    assert client.get("/api/auth/me", headers=bearer(no_exp)).status_code == 401


def test_token_for_deleted_user_rejected(client, db):
    body = register(client).json()
    db.execute(text("DELETE FROM users WHERE id = :id"), {"id": body["user"]["id"]})
    db.commit()
    response = client.get("/api/auth/me", headers=bearer(body["access_token"]))
    assert response.status_code == 401
    assert response.json() == {"detail": INVALID_TOKEN}


# --- Token contents ----------------------------------------------------------

def test_token_contains_user_id_and_configured_expiry():
    token = create_access_token(42)
    assert decode_access_token(token) == 42
    claims = jwt.decode(token, options={"verify_signature": False})
    lifetime = claims["exp"] - claims["iat"]
    assert lifetime == get_settings().access_token_expire_minutes * 60
