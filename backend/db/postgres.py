from collections.abc import Generator

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 5},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_connection() -> None:
    """Raise if PostgreSQL is unreachable."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


# Learners from before domain enrolment (Phase 23) were onboarded into the only domain there was
# when they had any progress rows; they keep that, joined and onboarded from their first row's date.
BACKFILL_ENROLMENTS = text("""
INSERT INTO domain_enrolments (user_id, domain_id, joined_at, onboarded_at)
SELECT user_id, :domain, MIN(created_at), MIN(created_at) FROM topic_progress GROUP BY user_id
ON CONFLICT (user_id, domain_id) DO NOTHING
""")


def init_db(bind: Engine | None = None) -> None:
    """Create any missing tables. Existing tables are left untouched (no migrations).

    The one exception: when the domain_enrolments table is first created, existing learners are
    enrolled in the default domain in the same transaction, so the backfill runs exactly once.
    """
    import models  # noqa: F401  - importing registers every model on Base.metadata
    from seed.curriculum import DEFAULT_DOMAIN

    with (bind or engine).begin() as conn:
        had_enrolments = inspect(conn).has_table(models.DomainEnrolment.__tablename__)
        Base.metadata.create_all(bind=conn)
        if not had_enrolments:
            conn.execute(BACKFILL_ENROLMENTS, {"domain": DEFAULT_DOMAIN})
