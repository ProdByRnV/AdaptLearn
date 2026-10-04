from functools import lru_cache
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    frontend_url: str = "http://localhost:5173"

    database_url: str = "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/adaptlearn"

    neo4j_uri: str = "bolt://127.0.0.1:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password123"

    jwt_secret_key: str = "replace_me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080

    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"

    quiz_session_ttl_minutes: int = 30

    @field_validator("database_url")
    @classmethod
    def use_psycopg2_driver(cls, value: str) -> str:
        # Managed providers (e.g. Neon) hand out postgres:// or postgresql:// URLs;
        # SQLAlchemy needs the explicit driver name.
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg2://" + value[len(prefix):]
        return value

    @model_validator(mode="after")
    def require_real_secret_in_production(self) -> "Settings":
        if self.is_production and self.jwt_secret_key in ("", "replace_me"):
            raise ValueError("JWT_SECRET_KEY must be set to a real secret in production")
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def cors_origins(self) -> list[str]:
        # FRONTEND_URL may hold several comma-separated origins (e.g. local + Vercel preview).
        return [origin.strip().rstrip("/") for origin in self.frontend_url.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
