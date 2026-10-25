import re
import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from db.postgres import Base

# BKT defaults (PRD 6.4) come from the BKT service, so the column defaults, the database
# server defaults and the algorithm always use the same values.
from services.bkt import DEFAULT_P_GUESS, DEFAULT_P_KNOW, DEFAULT_P_LEARN, DEFAULT_P_SLIP
from services.proctoring import CLIENT_EVENT_TYPES, VERDICTS

BCRYPT_HASH_PATTERN = re.compile(r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$")


class TopicStatus(StrEnum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


_STATUS_VALUES = ", ".join(f"'{s.value}'" for s in TopicStatus)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    progress: Mapped[list["TopicProgress"]] = relationship(back_populates="user", passive_deletes=True)
    attempts: Mapped[list["QuizAttempt"]] = relationship(back_populates="user", passive_deletes=True)
    quiz_sessions: Mapped[list["QuizSession"]] = relationship(back_populates="user", passive_deletes=True)

    @validates("email")
    def _normalize_email(self, key: str, value: str) -> str:
        # Stored lowercase so the unique constraint treats Puja@x.com and puja@x.com as the same account.
        return value.strip().lower()

    @validates("hashed_password")
    def _require_bcrypt_hash(self, key: str, value: str) -> str:
        # Last line of defence: a plain-text password can never be written to this column.
        if not BCRYPT_HASH_PATTERN.match(value or ""):
            raise ValueError("hashed_password must be a bcrypt hash, never a plain-text password")
        return value

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


class TopicProgress(Base):
    __tablename__ = "topic_progress"
    __table_args__ = (
        # The unique constraint's index also serves (user_id, topic_id) lookups.
        UniqueConstraint("user_id", "topic_id", name="uq_topic_progress_user_topic"),
        CheckConstraint(f"status IN ({_STATUS_VALUES})", name="ck_topic_progress_status"),
        CheckConstraint(
            "p_know BETWEEN 0 AND 1 AND p_learn BETWEEN 0 AND 1 "
            "AND p_slip BETWEEN 0 AND 1 AND p_guess BETWEEN 0 AND 1",
            name="ck_topic_progress_probabilities",
        ),
        CheckConstraint("attempts >= 0 AND correct >= 0", name="ck_topic_progress_counters"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TopicStatus.LOCKED.value, server_default=TopicStatus.LOCKED.value
    )
    p_know: Mapped[float] = mapped_column(
        Float, nullable=False, default=DEFAULT_P_KNOW, server_default=text(str(DEFAULT_P_KNOW))
    )
    p_learn: Mapped[float] = mapped_column(
        Float, nullable=False, default=DEFAULT_P_LEARN, server_default=text(str(DEFAULT_P_LEARN))
    )
    p_slip: Mapped[float] = mapped_column(
        Float, nullable=False, default=DEFAULT_P_SLIP, server_default=text(str(DEFAULT_P_SLIP))
    )
    p_guess: Mapped[float] = mapped_column(
        Float, nullable=False, default=DEFAULT_P_GUESS, server_default=text(str(DEFAULT_P_GUESS))
    )
    # attempts counts quiz submissions; correct counts individual correct answers.
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    needs_attention: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="progress")

    def __repr__(self) -> str:
        return f"<TopicProgress user={self.user_id} topic={self.topic_id!r} status={self.status} p_know={self.p_know:.2f}>"


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        Index("ix_quiz_attempts_user_created", "user_id", text("created_at DESC")),
        CheckConstraint("score >= 0", name="ck_quiz_attempts_score"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic_id: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # Full question snapshot (including answers) for history - only stored after submission.
    questions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    submitted_answers: Mapped[list[int]] = mapped_column(JSONB, nullable=False)
    p_know_before: Mapped[float] = mapped_column(Float, nullable=False)
    p_know_after: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="attempts")

    def __repr__(self) -> str:
        return f"<QuizAttempt id={self.id} user={self.user_id} topic={self.topic_id!r} score={self.score}>"


class QuizSession(Base):
    """A generated quiz awaiting submission. Holds the answer key, which never leaves the server."""

    __tablename__ = "quiz_sessions"
    __table_args__ = (Index("ix_quiz_sessions_user_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic_id: Mapped[str] = mapped_column(String(100), nullable=False)
    questions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="quiz_sessions")

    def __repr__(self) -> str:
        return f"<QuizSession id={self.id} user={self.user_id} topic={self.topic_id!r}>"


# --- Proctoring (Phase 12.5) -------------------------------------------------------
# New tables rather than new columns, so create_all() adds them to existing databases
# without a migration.

_EVENT_TYPES = ", ".join(f"'{t}'" for t in CLIENT_EVENT_TYPES)
_VERDICTS = ", ".join(f"'{v}'" for v in VERDICTS)


class QuizResponse(Base):
    """One served question within a quiz session: when it was shown, its deadline and the answer."""

    __tablename__ = "quiz_responses"
    __table_args__ = (
        UniqueConstraint("session_id", "question_index", name="uq_quiz_responses_session_question"),
        CheckConstraint("question_index >= 0", name="ck_quiz_responses_index"),
        CheckConstraint("answer IS NULL OR answer BETWEEN 0 AND 3", name="ck_quiz_responses_answer"),
        CheckConstraint("deadline > served_at", name="ck_quiz_responses_deadline"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False)
    question_index: Mapped[int] = mapped_column(Integer, nullable=False)
    served_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    answer: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timed_out: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))

    @property
    def is_open(self) -> bool:
        return self.answered_at is None and not self.timed_out


class ProctoringEvent(Base):
    """An integrity signal reported by the quiz page (layer 2), including heartbeats."""

    __tablename__ = "proctoring_events"
    __table_args__ = (
        Index("ix_proctoring_events_session", "session_id"),
        CheckConstraint(f"event_type IN ({_EVENT_TYPES})", name="ck_proctoring_events_type"),
        CheckConstraint("duration_ms IS NULL OR duration_ms >= 0", name="ck_proctoring_events_duration"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # received_at is the trusted server time; occurred_at is whatever the page claims.
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class QuizIntegrity(Base):
    """The integrity verdict for a quiz session, decided when it is submitted or abandoned."""

    __tablename__ = "quiz_integrity"
    __table_args__ = (
        CheckConstraint(f"verdict IN ({_VERDICTS})", name="ck_quiz_integrity_verdict"),
        CheckConstraint("score IS NULL OR score BETWEEN 0 AND 100", name="ck_quiz_integrity_score"),
        Index("ix_quiz_integrity_attempt", "attempt_id"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quiz_sessions.id", ondelete="CASCADE"), primary_key=True
    )
    attempt_id: Mapped[int | None] = mapped_column(ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verdict: Mapped[str] = mapped_column(String(16), nullable=False)
    counted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reasons: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
