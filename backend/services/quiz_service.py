"""Quiz sessions: generation (this phase) and submission (Phase 11).

The full questions, including the answer key, are stored server-side in quiz_sessions.
The browser only ever receives question text and options (ARCHITECTURE.md section 15).
"""

import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from config import get_settings
from models import QuizSession, TopicStatus
from schemas.quiz import QuizQuestion
from seed.curriculum import DOMAIN, DOMAIN_NAME
from services.learning_path import ensure_progress_rows, sync_statuses
from services.llm_quiz import generate_questions
from services.topic_service import get_progress_map, get_topics

logger = logging.getLogger("adaptlearn")

_rng = random.SystemRandom()


class TopicNotFoundError(Exception):
    pass


class TopicLockedError(Exception):
    pass


class QuizUnavailableError(Exception):
    pass


def shuffle_options(question: QuizQuestion) -> dict[str, Any]:
    """Shuffle the options and remap the answer index, so the stored position reveals nothing
    and any position bias in LLM output disappears."""
    order = list(range(len(question.options)))
    _rng.shuffle(order)
    return {
        "question": question.question,
        "options": [question.options[i] for i in order],
        "correct": order.index(question.correct),
        "explanation": question.explanation,
    }


def create_quiz(db: Session, user_id: int, topic_id: str, domain: str = DOMAIN) -> dict[str, Any]:
    topics = get_topics(domain)
    topic = next((t for t in topics if t.id == topic_id), None)
    if topic is None:
        raise TopicNotFoundError(topic_id)

    progress = get_progress_map(db, user_id)
    if topic_id not in progress:
        # No progress yet (quiz requested before onboarding) or a topic added after onboarding:
        # initialise rows exactly as onboarding with nothing known would.
        ensure_progress_rows(db, user_id, [t.id for t in topics])
        sync_statuses(db, user_id, domain)
        progress = get_progress_map(db, user_id)
    row = progress[topic_id]
    if row.status == TopicStatus.LOCKED:
        raise TopicLockedError(topic_id)

    generated = generate_questions(topic, DOMAIN_NAME)
    if generated is None:
        raise QuizUnavailableError(topic_id)

    ttl_minutes = get_settings().quiz_session_ttl_minutes
    session = QuizSession(
        user_id=user_id,
        topic_id=topic_id,
        questions=[shuffle_options(q) for q in generated.questions],
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes),
    )
    db.add(session)
    if row.status == TopicStatus.UNLOCKED:
        row.status = TopicStatus.IN_PROGRESS.value  # decision 2
    db.commit()
    logger.info("Quiz %s created for user id=%s topic=%s (%s)", session.id, user_id, topic_id, generated.source)

    return {
        "quiz_id": session.id,
        "topic": {"id": topic.id, "name": topic.name},
        # Sanitised: no answer index and no explanation until submission.
        "questions": [
            {"id": index, "question": q["question"], "options": q["options"]}
            for index, q in enumerate(session.questions)
        ],
        "expires_in_seconds": ttl_minutes * 60,
        "source": generated.source,
    }
