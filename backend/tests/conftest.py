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
