"""Paths that only run when something goes wrong or at the edges of deployment (Phase 20): the
health check, the 503/500 handlers, startup with a database down, deployment settings, and the
exact request sent to Groq (never made for real in tests)."""

import asyncio
from types import SimpleNamespace

import pytest
from neo4j.exceptions import ServiceUnavailable
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

import main
from config import Settings, get_settings
from errors import DB_UNAVAILABLE, INTERNAL_ERROR
from routers import health
from services import llm_quiz, topic_service
from services.llm_quiz import call_groq as real_call_groq  # bound before the autouse fixture replaces it

FRONTEND = get_settings().cors_origins[0]


def _down(message):
    def check():
        raise ConnectionError(message)

    return check


# --- /api/health -------------------------------------------------------------------------

def test_health_ok_when_both_databases_answer(client, monkeypatch):
    monkeypatch.setattr(health.postgres, "check_connection", lambda: None)
    monkeypatch.setattr(health.neo4j_db, "check_connection", lambda: None)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "api": "ok", "postgres": "ok", "neo4j": "ok"}


@pytest.mark.parametrize(
    ("postgres_up", "neo4j_up"),
    [(False, True), (True, False), (False, False)],
    ids=["postgres-down", "neo4j-down", "both-down"],
)
def test_health_reports_which_database_is_down(client, monkeypatch, postgres_up, neo4j_up):
    monkeypatch.setattr(health.postgres, "check_connection", (lambda: None) if postgres_up else _down("refused"))
    monkeypatch.setattr(health.neo4j_db, "check_connection", (lambda: None) if neo4j_up else _down("refused"))
    response = client.get("/api/health")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["api"] == "ok"
    assert body["postgres"] == ("ok" if postgres_up else "unavailable")
    assert body["neo4j"] == ("ok" if neo4j_up else "unavailable")
    assert body["detail"] == "One or more services are unavailable"
    assert "refused" not in response.text  # the cause is logged, not sent


# --- Error handlers ------------------------------------------------------------------------

def test_postgres_failure_becomes_503_with_the_standard_message(client, make_user, monkeypatch):
    _, headers = make_user()

    def lost(*args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    monkeypatch.setattr(topic_service, "build_graph", lost)
    response = client.get("/api/topics/graph", headers={**headers, "Origin": FRONTEND})
    assert response.status_code == 503
    assert response.json() == {"detail": DB_UNAVAILABLE}
    assert response.headers["access-control-allow-origin"] == FRONTEND


def test_neo4j_failure_becomes_503(client, make_user, monkeypatch):
    _, headers = make_user()

    def down(*args, **kwargs):
        raise ServiceUnavailable("Neo4j is down")

    monkeypatch.setattr(topic_service, "get_topics", down)
    response = client.get("/api/topics/all", headers=headers)
    assert response.status_code == 503
    assert "Curriculum service is temporarily unavailable" in response.json()["detail"]


def test_unexpected_errors_become_a_generic_500_with_cors(client, make_user, monkeypatch):
    _, headers = make_user()

    def bug(*args, **kwargs):
        raise RuntimeError("secret internals: password=hunter2")

    monkeypatch.setattr(topic_service, "build_graph", bug)
    response = client.get("/api/topics/graph", headers={**headers, "Origin": FRONTEND})
    assert response.status_code == 500
    assert response.json() == {"detail": INTERNAL_ERROR}
    assert "hunter2" not in response.text and "Traceback" not in response.text
    # Without CORS headers the browser would hide the response and show a network error instead.
    assert response.headers["access-control-allow-origin"] == FRONTEND


# --- Startup -----------------------------------------------------------------------------

def _run_lifespan():
    async def run():
        async with main.lifespan(main.app):
            pass

    asyncio.run(run())


def test_startup_creates_tables_and_seeds_when_databases_are_up(monkeypatch):
    calls = []
    monkeypatch.setattr(main.postgres, "check_connection", lambda: calls.append("pg check"))
    monkeypatch.setattr(main.postgres, "init_db", lambda: calls.append("pg tables"))
    monkeypatch.setattr(main.neo4j_db, "check_connection", lambda: calls.append("neo4j check"))
    monkeypatch.setattr(main, "seed_curriculum", lambda: calls.append("seed"))
    monkeypatch.setattr(main.neo4j_db, "close_driver", lambda: calls.append("close"))
    monkeypatch.setattr(main.postgres.engine, "dispose", lambda: calls.append("dispose"))
    _run_lifespan()
    assert calls == ["pg check", "pg tables", "neo4j check", "seed", "close", "dispose"]


def test_startup_survives_both_databases_being_down(monkeypatch, caplog):
    # The app must still boot, so /api/health can explain what is wrong.
    calls = []
    monkeypatch.setattr(main.postgres, "check_connection", _down("pg refused"))
    monkeypatch.setattr(main.postgres, "init_db", lambda: calls.append("pg tables"))
    monkeypatch.setattr(main.neo4j_db, "check_connection", _down("neo4j refused"))
    monkeypatch.setattr(main, "seed_curriculum", lambda: calls.append("seed"))
    monkeypatch.setattr(main.neo4j_db, "close_driver", lambda: None)
    monkeypatch.setattr(main.postgres.engine, "dispose", lambda: None)
    with caplog.at_level("WARNING", logger="adaptlearn"):
        _run_lifespan()
    assert calls == []
    assert "PostgreSQL is not ready at startup" in caplog.text
    assert "Neo4j is not ready at startup" in caplog.text


# --- Deployment settings -------------------------------------------------------------------

@pytest.mark.parametrize("prefix", ["postgres://", "postgresql://"])
def test_managed_database_urls_get_the_psycopg2_driver(prefix):
    # Neon and similar providers hand out postgres:// URLs.
    settings = Settings(_env_file=None, database_url=f"{prefix}user:pw@db.example.com/app")
    assert settings.database_url == "postgresql+psycopg2://user:pw@db.example.com/app"


@pytest.mark.parametrize("secret", ["", "replace_me"])
def test_production_refuses_a_placeholder_jwt_secret(secret):
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY must be set"):
        Settings(_env_file=None, app_env="production", jwt_secret_key=secret)


def test_production_accepts_a_real_secret_and_development_the_placeholder():
    assert Settings(_env_file=None, app_env="production", jwt_secret_key="a-long-random-secret").is_production
    assert not Settings(_env_file=None, jwt_secret_key="replace_me").is_production


def test_several_frontend_origins_can_be_allowed():
    settings = Settings(_env_file=None, frontend_url="https://app.example.com/, http://localhost:5173")
    assert settings.cors_origins == ["https://app.example.com", "http://localhost:5173"]


# --- The Groq request ----------------------------------------------------------------------

class FakeGroq:
    """Records how the client is built and what is asked of it."""

    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        FakeGroq.instances.append(self)

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"questions": []}'))])


@pytest.fixture()
def fake_groq(monkeypatch):
    FakeGroq.instances.clear()
    monkeypatch.setattr(llm_quiz, "Groq", FakeGroq)
    return FakeGroq


def test_groq_request_uses_json_mode_one_attempt_and_the_given_timeout(fake_groq, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr(settings, "groq_model", "test-model")
    monkeypatch.setattr(settings, "groq_reasoning_effort", "low")
    messages = [{"role": "user", "content": "hi"}]
    assert real_call_groq(messages, timeout=7.5) == '{"questions": []}'
    (client,) = fake_groq.instances
    # The service handles retries itself (within a time budget), so the SDK must not add its own.
    assert client.kwargs == {"api_key": "test-key", "timeout": 7.5, "max_retries": 0}
    (request,) = client.requests
    assert request["model"] == "test-model"
    assert request["messages"] == messages
    assert request["response_format"] == {"type": "json_object"}
    assert request["temperature"] == llm_quiz.TEMPERATURE
    assert request["max_completion_tokens"] == llm_quiz.MAX_COMPLETION_TOKENS
    assert request["reasoning_effort"] == "low"


def test_reasoning_effort_is_left_out_when_not_configured(fake_groq, monkeypatch):
    monkeypatch.setattr(get_settings(), "groq_reasoning_effort", "")
    real_call_groq([{"role": "user", "content": "hi"}], timeout=5)
    assert "reasoning_effort" not in fake_groq.instances[0].requests[0]
