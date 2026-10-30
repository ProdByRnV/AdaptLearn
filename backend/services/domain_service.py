"""The domain catalogue and the home page across joined domains (Phase 23).

Both read the curriculum once (every topic with its domains) and the learner's frontier once, so
each costs two Neo4j round trips however many domains there are. Status is global per topic, so
a domain's numbers already include what the learner completed through other domains: that is
the head start shown in the catalogue and used for suggestions.
"""

from typing import Any

from sqlalchemy.orm import Session

from models import DomainEnrolment, TopicProgress, TopicStatus
from services import topic_service
from services.enrolment_service import get_enrolments
from services.learning_path import get_frontier, recommendations, sync_statuses
from services.progress_service import recent_attempts
from services.topic_service import TopicInfo, get_all_topics, get_progress_map, percent_of

SUGGESTION_LIMIT = 3


def _snapshot(db: Session, user_id: int) -> tuple[list[TopicInfo], list[TopicInfo], dict[str, TopicProgress]]:
    """(every topic, the learner's frontier, their progress). Writes nothing before any progress exists."""
    if get_progress_map(db, user_id):
        frontier = sync_statuses(db, user_id)
        db.commit()
    else:
        frontier = get_frontier([])
    return get_all_topics(), frontier, get_progress_map(db, user_id)


def _status(topic_id: str, progress: dict[str, TopicProgress]) -> str | None:
    row = progress.get(topic_id)
    return row.status if row is not None else None


def _summary(
    domain: str,
    topics: list[TopicInfo],
    frontier: list[TopicInfo],
    progress: dict[str, TopicProgress],
    enrolment: DomainEnrolment | None,
) -> dict[str, Any]:
    info = topic_service.DOMAIN_BY_ID[domain]
    members = [t for t in topics if domain in t.domains]
    available = [t for t in frontier if domain in t.domains]
    known = [t for t in members if _status(t.id, progress) == TopicStatus.COMPLETED]
    # Topics opened by what the learner has already completed, as opposed to starting topics.
    ready = [t for t in available if t.prerequisites]
    joined = enrolment is not None
    return {
        "id": domain,
        "name": info.name,
        "description": info.description,
        "total_topics": len(members),
        "completed_topics": len(known),
        "in_progress_topics": sum(1 for t in members if _status(t.id, progress) == TopicStatus.IN_PROGRESS),
        "available_topics": len(available),
        "progress_percent": percent_of(len(known), len(members)),
        "curriculum_complete": bool(members) and len(known) == len(members),
        "joined": joined,
        "joined_at": enrolment.joined_at if joined else None,
        "onboarded": joined and enrolment.onboarded_at is not None,
        "known_topics": [{"id": t.id, "name": t.name} for t in known],
        "ready_topics": [{"id": t.id, "name": t.name} for t in ready],
        "suggested": not joined and bool(known or ready),
    }


def _summaries(db: Session, user_id: int) -> tuple[list[dict[str, Any]], list[TopicInfo], list[TopicInfo], dict[str, TopicProgress]]:
    topics, frontier, progress = _snapshot(db, user_id)
    enrolments = get_enrolments(db, user_id)
    summaries = [
        _summary(domain, topics, frontier, progress, enrolments.get(domain))
        for domain in topic_service.SUPPORTED_DOMAINS
    ]
    return summaries, topics, frontier, progress


def build_catalogue(db: Session, user_id: int) -> dict[str, Any]:
    """Every domain in curriculum order, with its size and the learner's standing there."""
    summaries, *_ = _summaries(db, user_id)
    return {"domains": summaries}


def suggestions(summaries: list[dict[str, Any]], limit: int = SUGGESTION_LIMIT) -> list[dict[str, Any]]:
    """Domains not joined yet that the learner is already partly ready for, biggest head start first."""
    suggested = [s for s in summaries if s["suggested"]]
    head_start = {s["id"]: (len(s["known_topics"]) + len(s["ready_topics"])) / s["total_topics"] for s in suggested}
    return sorted(suggested, key=lambda s: -head_start[s["id"]])[:limit]  # stable: ties keep curriculum order


def build_home(db: Session, user_id: int) -> dict[str, Any]:
    """Progress in every joined domain, what to learn next across them, suggestions and recent quizzes.

    Up next (overall and per domain) comes only from domains the learner has onboarded in; a topic
    shared by several of them appears once, listing each. Joined domains are in the order joined.
    """
    summaries, topics, frontier, progress = _summaries(db, user_id)
    joined = sorted((s for s in summaries if s["joined"]), key=lambda s: s["joined_at"])
    onboarded = [s["id"] for s in joined if s["onboarded"]]

    domains = []
    for summary in joined:
        # Before onboarding, the domain's next topic could be one the learner already knows.
        available = [t for t in frontier if summary["id"] in t.domains] if summary["onboarded"] else []
        first = recommendations(available, progress, limit=1)
        domains.append({**summary, "up_next": first[0] if first else None})

    candidates = [t for t in frontier if set(t.domains) & set(onboarded)]
    domains_of = {t.id: [d for d in onboarded if d in t.domains] for t in candidates}
    up_next = [{**rec, "domains": domains_of[rec["id"]]} for rec in recommendations(candidates, progress)]

    return {
        "domains": domains,
        "up_next": up_next,
        "suggestions": suggestions(summaries),
        "recent_attempts": recent_attempts(db, user_id, {t.id: t.name for t in topics}),
    }
