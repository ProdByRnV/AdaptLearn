"""Shared fixtures.

Tests run against a separate PostgreSQL database (default: "<dev db name>_test", or
TEST_DATABASE_URL if set). It is created if missing and its tables are rebuilt at the
start of every run, so the development database is never touched.
"""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

import models  # noqa: F401  - registers all tables on Base.metadata
from config import get_settings
from db.postgres import Base, get_db
from main import app


def _test_database_url() -> URL:
    override = os.getenv("TEST_DATABASE_URL")
    if override:
        return make_url(override)
    dev_url = make_url(get_settings().database_url)
    return dev_url.set(database=f"{dev_url.database}_test")


def _ensure_database_exists(url: URL) -> None:
    admin_engine = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            exists = conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": url.database})
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        admin_engine.dispose()


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    url = _test_database_url()
    if url.database == make_url(get_settings().database_url).database:
        pytest.exit("Refusing to run tests against the development database", returncode=1)
    _ensure_database_exists(url)
    test_engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture()
def session_factory(engine: Engine) -> Generator[sessionmaker, None, None]:
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    table_names = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"))


@pytest.fixture()
def db(session_factory: sessionmaker) -> Generator[Session, None, None]:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(session_factory: sessionmaker) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    # Not used as a context manager, so the app lifespan (dev DB table creation,
    # Neo4j checks) does not run during tests.
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def no_real_groq(monkeypatch):
    """Tests must never call the real Groq API (cost, rate limits, network flakiness).

    Any test that reaches the LLM without installing a fake fails loudly here.
    """
    from services import llm_quiz

    def refuse(*args, **kwargs):
        raise AssertionError("A test tried to call the real Groq API; install a fake call_groq")

    monkeypatch.setattr(llm_quiz, "call_groq", refuse)


def sample_quiz_json() -> str:
    """A valid 3-question quiz; option 0 ("Right answer N") is correct before shuffling."""
    import json

    return json.dumps(
        {
            "questions": [
                {
                    "question": f"Sample question number {n}?",
                    "options": [f"Right answer {n}", f"Wrong A{n}", f"Wrong B{n}", f"Wrong C{n}"],
                    "correct": 0,
                    "explanation": f"Because answer {n} is right.",
                }
                for n in range(3)
            ]
        }
    )


@pytest.fixture()
def fake_llm(monkeypatch):
    """Script the LLM: each call returns (or raises) the next item in .script, else a valid quiz.

    Records each call's messages and timeout in .calls. Also sets a dummy API key so the
    Groq path (not the no-key fallback) is exercised.
    """
    from config import get_settings
    from services import llm_quiz

    class Fake:
        def __init__(self):
            self.script: list = []
            self.calls: list = []

        def __call__(self, messages, timeout):
            self.calls.append({"messages": messages, "timeout": timeout})
            item = self.script.pop(0) if self.script else sample_quiz_json()
            if isinstance(item, Exception):
                raise item
            return item

    fake = Fake()
    monkeypatch.setattr(llm_quiz, "call_groq", fake)
    monkeypatch.setattr(get_settings(), "groq_api_key", "gsk_test_key")
    return fake


class FakeClock:
    """Controls the time the quiz service sees (deadlines, heartbeats, rate limits)."""

    def __init__(self):
        from datetime import datetime, timezone

        self.now = datetime.now(timezone.utc)

    def __call__(self):
        return self.now

    def advance(self, seconds: float) -> None:
        from datetime import timedelta

        self.now += timedelta(seconds=seconds)


@pytest.fixture()
def clock(monkeypatch) -> FakeClock:
    from services import quiz_service

    fake = FakeClock()
    monkeypatch.setattr(quiz_service, "utc_now", fake)
    return fake


@pytest.fixture()
def quiz_taker(client: TestClient, session_factory: sessionmaker, clock: FakeClock):
    """Take a whole proctored quiz through the API, the way an honest quiz page would.

    pattern: one letter per question - C correct, W wrong, T timed out (no answer before the deadline).
    Each question is answered after `seconds` (default 10), with a heartbeat every 5 seconds.
    `events` (proctoring events) are reported during the first question. After submitting, the clock
    moves on `cooldown_minutes` so repeated quizzes stay under the hourly limit.
    Returns the submit response body.
    """
    from config import get_settings
    from models import QuizSession
    from services.quiz_service import ANSWER_GRACE_SECONDS

    def heartbeat(headers, quiz_id):
        response = client.post(f"/api/quiz/{quiz_id}/events", json={"events": [{"type": "heartbeat"}]}, headers=headers)
        assert response.status_code == 200, response.text

    def wait(headers, quiz_id, seconds, heartbeats):
        elapsed = 0
        while elapsed < seconds:
            step = min(5, seconds - elapsed)
            clock.advance(step)
            elapsed += step
            if heartbeats:
                heartbeat(headers, quiz_id)

    def take(headers, topic_id, pattern, *, seconds=10, heartbeats=True, events=(), cooldown_minutes=13):
        generated = client.get(f"/api/quiz/generate/{topic_id}", headers=headers)
        assert generated.status_code == 200, generated.text
        quiz_id = generated.json()["quiz_id"]
        with session_factory() as s:
            key = [q["correct"] for q in s.get(QuizSession, quiz_id).questions]

        for index, letter in enumerate(pattern):
            served = client.post(f"/api/quiz/{quiz_id}/next", headers=headers)
            assert served.status_code == 200, served.text
            if heartbeats:
                heartbeat(headers, quiz_id)
            if index == 0 and events:
                reported = client.post(f"/api/quiz/{quiz_id}/events", json={"events": list(events)}, headers=headers)
                assert reported.status_code == 200, reported.text
            if letter == "T":
                wait(headers, quiz_id, get_settings().quiz_seconds_per_question + ANSWER_GRACE_SECONDS + 1, heartbeats)
                answer = 0
            else:
                wait(headers, quiz_id, seconds, heartbeats)
                answer = key[index] if letter == "C" else (key[index] + 1) % 4
            ack = client.post(f"/api/quiz/{quiz_id}/answer", json={"question_id": index, "answer": answer}, headers=headers)
            assert ack.status_code == 200, ack.text
            assert ack.json()["timed_out"] is (letter == "T")

        submitted = client.post("/api/quiz/submit", json={"quiz_id": quiz_id}, headers=headers)
        assert submitted.status_code == 200, submitted.text
        clock.advance(cooldown_minutes * 60)
        return submitted.json()

    return take


@pytest.fixture(scope="session")
def curriculum() -> None:
    """Ensure the real web-development curriculum is in Neo4j (skip if Neo4j is down).

    Runs the same idempotent seeder as backend startup; tests only read the curriculum.
    """
    from db import neo4j_db
    from seed.seed_graph import seed_curriculum

    try:
        neo4j_db.check_connection()
    except Exception as exc:
        pytest.skip(f"Neo4j not reachable: {exc}")
    seed_curriculum()


@pytest.fixture()
def make_user(client: TestClient):
    """Register a user through the API. Returns (user_id, auth headers)."""
    counter = 0

    def _make(email: str | None = None) -> tuple[int, dict[str, str]]:
        nonlocal counter
        counter += 1
        email = email or f"learner{counter}@example.com"
        response = client.post(
            "/api/auth/register",
            json={"username": f"Learner {counter}", "email": email, "password": "StrongPassword123"},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        return body["user"]["id"], {"Authorization": f"Bearer {body['access_token']}"}

    return _make
