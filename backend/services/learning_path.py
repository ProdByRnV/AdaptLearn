"""Prerequisite-aware learning path: the learnable frontier, status syncing and onboarding.

Graph questions (which topics are learnable, which topics a topic depends on) are answered
by Neo4j; per-user state lives in PostgreSQL topic_progress rows.

Topic status belongs to the topic, not to a domain: the frontier is computed over the whole
shared pool (a prerequisite in another domain counts), and each domain view filters it.
"""

import logging
from collections.abc import Iterable
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from db import neo4j_db
from models import TopicProgress, TopicStatus
from services.bkt import DEFAULT_P_KNOW, MASTERY_THRESHOLD
from services import enrolment_service, topic_service
from services.topic_service import TopicInfo, ensure_domain, get_progress_map, get_topics, to_percent, topic_from_row

logger = logging.getLogger("adaptlearn")

RECOMMENDATION_LIMIT = 3

# ARCHITECTURE.md 9.3 without LIMIT, over every supported domain: the full frontier is needed to
# unlock every eligible topic (decision 1). Recommendations take the first three of a domain's slice.
FRONTIER = """
MATCH (t:Topic)-[:IN_DOMAIN]->(d:Domain)
WHERE d.id IN $domains AND NOT t.id IN $completed_ids
WITH DISTINCT t
OPTIONAL MATCH (pre:Topic)-[:PREREQUISITE_OF]->(t)
WITH t, collect(pre {.id, .name, .home_domain}) AS prereqs
WHERE ALL(p IN prereqs WHERE p.id IN $completed_ids)
RETURN t.id AS id, t.name AS name, t.description AS description,
       t.difficulty AS difficulty, t.resources AS resources, t.home_domain AS home_domain,
       [(t)-[:IN_DOMAIN]->(m:Domain) WHERE m.id IN $domains | m.id] AS domains, prereqs
ORDER BY t.difficulty ASC, t.name ASC
"""

# Every topic that must come before any of $ids, however many steps back, in any domain.
ANCESTORS = """
MATCH (pre:Topic)-[:PREREQUISITE_OF*1..]->(t:Topic)
WHERE t.id IN $ids
RETURN DISTINCT pre.id AS id
"""

KNOWN_TOPIC_P_KNOW = MASTERY_THRESHOLD  # ARCHITECTURE.md section 10: known topics start at 0.95


class UnknownTopicsError(Exception):
    def __init__(self, topic_ids: list[str]):
        super().__init__(", ".join(topic_ids))
        self.topic_ids = topic_ids


def get_frontier(completed_ids: Iterable[str]) -> list[TopicInfo]:
    """Topics in any domain that are not completed and whose prerequisites are all completed, easiest first."""
    rows = neo4j_db.read(FRONTIER, domains=list(topic_service.SUPPORTED_DOMAINS), completed_ids=sorted(set(completed_ids)))
    return [topic_from_row(row) for row in rows]


def in_domain(frontier: list[TopicInfo], domain: str) -> list[TopicInfo]:
    """The part of the frontier that belongs to one domain, in the same order."""
    return [t for t in frontier if domain in t.domains]


def get_ancestors(topic_ids: Iterable[str]) -> set[str]:
    ids = sorted(set(topic_ids))
    if not ids:
        return set()
    return {row["id"] for row in neo4j_db.read(ANCESTORS, ids=ids)}


def ensure_progress_rows(db: Session, user_id: int, topic_ids: Iterable[str]) -> None:
    """Create any missing topic_progress rows with BKT defaults. Safe under concurrent calls."""
    values = [{"user_id": user_id, "topic_id": topic_id} for topic_id in sorted(set(topic_ids))]
    if values:
        db.execute(
            insert(TopicProgress).values(values).on_conflict_do_nothing(index_elements=["user_id", "topic_id"])
        )


def sync_statuses(db: Session, user_id: int) -> list[TopicInfo]:
    """Unlock every topic on the user's frontier and lock the rest of the not-yet-started topics.

    Works across all domains at once: a topic's status doesn't depend on which domain is being
    viewed. Completed and in-progress rows are never changed here, so a completed topic is never
    relocked. Frontier topics without a row (e.g. a topic added to the curriculum after onboarding)
    get one. Returns the whole frontier. Does not commit.
    """
    progress = get_progress_map(db, user_id)
    completed = [tid for tid, row in progress.items() if row.status == TopicStatus.COMPLETED]
    frontier = get_frontier(completed)
    frontier_ids = {t.id for t in frontier}
    missing = frontier_ids - progress.keys()
    if missing:
        ensure_progress_rows(db, user_id, missing)
        progress = get_progress_map(db, user_id)
    for topic_id, row in progress.items():
        if row.status in (TopicStatus.LOCKED, TopicStatus.UNLOCKED):
            row.status = (TopicStatus.UNLOCKED if topic_id in frontier_ids else TopicStatus.LOCKED).value
    return frontier


def recommendations(
    frontier: list[TopicInfo], progress: dict[str, TopicProgress], limit: int = RECOMMENDATION_LIMIT
) -> list[dict[str, Any]]:
    result = []
    for topic in frontier[:limit]:
        row = progress.get(topic.id)
        status = row.status if row is not None else TopicStatus.UNLOCKED.value
        p_know = row.p_know if row is not None else DEFAULT_P_KNOW
        result.append(
            {
                "id": topic.id,
                "name": topic.name,
                "description": topic.description,
                "difficulty": topic.difficulty,
                "status": status,
                "mastery": to_percent(p_know),
                "prerequisites": topic.prerequisites,
                "prerequisite_names": topic.prerequisite_names,
            }
        )
    return result


def get_learning_path(db: Session, user_id: int, domain: str) -> dict[str, Any]:
    """The next topics to learn (at most 3), easiest first.

    onboarded is per domain: False until the learner has been through this domain's onboarding, so
    the client can send them there first. A learner with no progress at all gets the starting
    frontier and nothing is written; otherwise statuses are synced so any topic that has become
    learnable is stored as unlocked (progress from other domains already counts here).
    """
    ensure_domain(domain)
    onboarded = enrolment_service.is_onboarded(db, user_id, domain)
    progress = get_progress_map(db, user_id)
    if not progress:
        frontier = in_domain(get_frontier([]), domain)
        return {
            "domain": domain,
            "onboarded": onboarded,
            "curriculum_complete": False,
            "recommended": recommendations(frontier, {}),
        }

    frontier = in_domain(sync_statuses(db, user_id), domain)
    db.commit()
    progress = get_progress_map(db, user_id)
    return {
        "domain": domain,
        "onboarded": onboarded,
        "curriculum_complete": domain_complete(frontier, domain, progress),
        "recommended": recommendations(frontier, progress),
    }


def domain_complete(domain_frontier: list[TopicInfo], domain: str, progress: dict[str, TopicProgress]) -> bool:
    """True when every topic in the domain is completed.

    Within one domain an empty frontier isn't enough: a topic can still be locked behind a
    prerequisite from another domain. Only then are the domain's topics read to check.
    """
    if domain_frontier:
        return False
    return all(
        (row := progress.get(t.id)) is not None and row.status == TopicStatus.COMPLETED
        for t in get_topics(domain)
    )


def mark_known(db: Session, user_id: int, domain: str, topic_ids: list[str]) -> dict[str, Any]:
    """Onboarding for one domain: join it, initialise progress and mark the topics already known.

    Known topics and all of their prerequisites become completed with p_know of at least 0.95
    (decision 3: a known topic implies its prerequisites are known). Calling it again only adds
    knowledge: nothing is relocked and existing mastery is never lowered.
    """
    ensure_domain(domain)
    all_ids = {t.id for t in get_topics(domain)}
    selected = set(topic_ids)
    unknown = sorted(selected - all_ids)
    if unknown:
        raise UnknownTopicsError(unknown)

    # Prerequisites may come from other domains; they become known too (decision 3).
    added_prerequisites = get_ancestors(selected) - selected
    known = selected | added_prerequisites

    ensure_progress_rows(db, user_id, all_ids | known)
    progress = get_progress_map(db, user_id)
    for topic_id in known:
        row = progress[topic_id]
        row.status = TopicStatus.COMPLETED.value
        row.p_know = max(row.p_know, KNOWN_TOPIC_P_KNOW)
        row.needs_attention = False

    frontier = in_domain(sync_statuses(db, user_id), domain)
    enrolment_service.mark_onboarded(db, user_id, domain)
    db.commit()
    logger.info("Onboarding saved for user id=%s in %s: %d known topics", user_id, domain, len(known))

    return {
        "message": "Onboarding saved",
        "known_count": len(known),
        "added_prerequisites": sorted(added_prerequisites),
        "recommended": recommendations(frontier, progress),
    }
