"""Dashboard aggregation (ARCHITECTURE.md sections 13.10, 13.11 and 16).

Topic metadata comes from one Neo4j query and is joined in memory by topic id, so the
dashboard costs two Neo4j round trips (topics + learning-path frontier) no matter how many
attempts or flagged topics the learner has.

A dashboard belongs to one domain: its stats, attention list and recent quizzes cover that
domain's topics only (a shared topic's quizzes count in every domain that uses it).
"""

from collections.abc import Collection, Mapping
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import QuizAttempt, QuizIntegrity, TopicProgress, TopicStatus
from seed.curriculum import DEFAULT_DOMAIN
from services.bkt import mastery_reached
from services.learning_path import get_learning_path
from services.topic_service import domain_name, effective_state, get_progress_map, get_topics, percent_of, to_percent

RECENT_ATTEMPTS_LIMIT = 5


def recent_attempts(
    db: Session, user_id: int, topic_names: Mapping[str, str], topic_ids: Collection[str] | None = None
) -> list[dict[str, Any]]:
    """The latest quiz attempts, newest first, optionally only for some topics.

    A topic no longer in the curriculum keeps its history under its id.
    """
    query = select(QuizAttempt).where(QuizAttempt.user_id == user_id)
    if topic_ids is not None:
        query = query.where(QuizAttempt.topic_id.in_(list(topic_ids)))
    recent = db.scalars(
        query.order_by(QuizAttempt.created_at.desc(), QuizAttempt.id.desc()).limit(RECENT_ATTEMPTS_LIMIT)
    ).all()
    integrity_by_attempt = {
        record.attempt_id: record
        for record in db.scalars(
            select(QuizIntegrity).where(QuizIntegrity.attempt_id.in_([a.id for a in recent]))
        )
    }
    return [
        {
            "id": attempt.id,
            "topic_id": attempt.topic_id,
            "topic_name": topic_names.get(attempt.topic_id, attempt.topic_id),
            "score": attempt.score,
            "total": len(attempt.questions),
            "passed": attempt.passed,
            "mastery_before": to_percent(attempt.p_know_before),
            "mastery_after": to_percent(attempt.p_know_after),
            "created_at": attempt.created_at,
            # Attempts from before proctoring (Phase 12.5) have no integrity record and always counted.
            "counted": integrity_by_attempt[attempt.id].counted if attempt.id in integrity_by_attempt else True,
            "integrity_verdict": integrity_by_attempt[attempt.id].verdict if attempt.id in integrity_by_attempt else None,
            "integrity_score": integrity_by_attempt[attempt.id].score if attempt.id in integrity_by_attempt else None,
        }
        for attempt in recent
    ]


def build_dashboard(db: Session, user_id: int, domain: str = DEFAULT_DOMAIN) -> dict[str, Any]:
    topics = get_topics(domain)  # Neo4j query 1 (also validates the domain)
    path = get_learning_path(db, user_id, domain)  # Neo4j query 2; syncs unlocked statuses first
    topic_by_id = {t.id: t for t in topics}

    progress = get_progress_map(db, user_id)
    rows = [row for topic_id, row in progress.items() if topic_id in topic_by_id]
    completed = sum(1 for row in rows if row.status == TopicStatus.COMPLETED)
    in_domain = (QuizAttempt.user_id == user_id, QuizAttempt.topic_id.in_(list(topic_by_id)))
    total_attempts = db.scalar(select(func.count()).select_from(QuizAttempt).where(*in_domain))
    flagged_attempts = db.scalar(
        select(func.count())
        .select_from(QuizIntegrity)
        .join(QuizAttempt, QuizAttempt.id == QuizIntegrity.attempt_id)
        .where(*in_domain, QuizIntegrity.counted.is_(False))
    )

    stats = {
        "total_topics": len(topics),
        "completed_topics": completed,
        "in_progress_topics": sum(1 for row in rows if row.status == TopicStatus.IN_PROGRESS),
        "mastered_topics": sum(1 for row in rows if mastery_reached(row.p_know)),
        # Average over the learner's initialised topics (ARCHITECTURE.md 16); 0 before onboarding.
        "average_mastery": round(sum(row.p_know for row in rows) / len(rows) * 100, 1) if rows else 0.0,
        "total_attempts": total_attempts,
        "flagged_attempts": flagged_attempts,
        "progress_percent": percent_of(completed, len(topics)),
    }

    needs_attention = [
        {
            "id": topic.id,
            "name": topic.name,
            "difficulty": topic.difficulty,
            "mastery": to_percent(progress[topic.id].p_know),
            "attempts": progress[topic.id].attempts,
            "resources": topic.resources,
        }
        for topic in topics
        if topic.id in progress and progress[topic.id].needs_attention
    ]

    mastery = []
    for topic in topics:
        status, p_know = effective_state(topic, progress)
        mastery.append(
            {
                "id": topic.id,
                "name": topic.name,
                "difficulty": topic.difficulty,
                "status": status,
                "mastery": to_percent(p_know),
                "mastered": mastery_reached(p_know),
            }
        )

    return {
        "domain": domain,
        "domain_name": domain_name(domain),
        "onboarded": path["onboarded"],
        "curriculum_complete": path["curriculum_complete"],
        "stats": stats,
        "recommended": path["recommended"],
        "needs_attention": needs_attention,
        "recent_attempts": recent_attempts(db, user_id, {t.id: t.name for t in topics}, list(topic_by_id)),
        "mastery": mastery,
    }


def list_progress(db: Session, user_id: int) -> dict[str, Any]:
    rows = db.scalars(
        select(TopicProgress).where(TopicProgress.user_id == user_id).order_by(TopicProgress.topic_id)
    ).all()
    return {
        "topics": [
            {
                "topic_id": row.topic_id,
                "status": row.status,
                "p_know": row.p_know,
                "attempts": row.attempts,
                "correct": row.correct,
                "needs_attention": row.needs_attention,
            }
            for row in rows
        ]
    }
