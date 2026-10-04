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

# BKT defaults (PRD 6.4). Kept here so the Python default and the database default never drift apart.
DEFAULT_P_KNOW = 0.10
DEFAULT_P_LEARN = 0.40
DEFAULT_P_SLIP = 0.10
DEFAULT_P_GUESS = 0.20

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
