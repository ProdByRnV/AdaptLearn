"""Prerequisite-aware learning path: the learnable frontier, status syncing and onboarding.

Graph questions (which topics are learnable, which topics a topic depends on) are answered
by Neo4j; per-user state lives in PostgreSQL topic_progress rows.
"""

import logging
from collections.abc import Iterable
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from db import neo4j_db
from models import TopicProgress, TopicStatus
from services.bkt import DEFAULT_P_KNOW, MASTERY_THRESHOLD
from services.topic_service import TopicInfo, ensure_domain, get_progress_map, get_topics, parse_resources, to_percent

logger = logging.getLogger("adaptlearn")

RECOMMENDATION_LIMIT = 3

# ARCHITECTURE.md 9.3 without LIMIT: the full frontier is needed to unlock every eligible
# topic (decision 1). Recommendations take the first three of this ordered list.
FRONTIER = """
MATCH (t:Topic {domain: $domain})
WHERE NOT t.id IN $completed_ids
OPTIONAL MATCH (pre:Topic {domain: $domain})-[:PREREQUISITE_OF]->(t)
WITH t, collect(pre {.id, .name}) AS prereqs
WHERE ALL(p IN prereqs WHERE p.id IN $completed_ids)
RETURN t.id AS id, t.name AS name, t.description AS description,
       t.difficulty AS difficulty, t.resources AS resources, prereqs
ORDER BY t.difficulty ASC, t.name ASC
"""

# Every topic that must come before any of $ids, however many steps back.
ANCESTORS = """
MATCH (pre:Topic {domain: $domain})-[:PREREQUISITE_OF*1..]->(t:Topic {domain: $domain})
WHERE t.id IN $ids
RETURN DISTINCT pre.id AS id
"""

KNOWN_TOPIC_P_KNOW = MASTERY_THRESHOLD  # ARCHITECTURE.md section 10: known topics start at 0.95


class UnknownTopicsError(Exception):
    def __init__(self, topic_ids: list[str]):
        super().__init__(", ".join(topic_ids))
        self.topic_ids = topic_ids


def get_frontier(domain: str, completed_ids: Iterable[str]) -> list[TopicInfo]:
    """Topics that are not completed and whose prerequisites are all completed, easiest first."""
    rows = neo4j_db.read(FRONTIER, domain=domain, completed_ids=sorted(set(completed_ids)))
    topics = []
    for row in rows:
        prereqs = sorted(row["prereqs"], key=lambda p: p["id"])
        topics.append(
            TopicInfo(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                difficulty=row["difficulty"],
                resources=parse_resources(row["resources"]),
                prerequisites=[p["id"] for p in prereqs],
                prerequisite_names=[p["name"] for p in prereqs],
            )
        )
    return topics


def get_ancestors(domain: str, topic_ids: Iterable[str]) -> set[str]:
    ids = sorted(set(topic_ids))
    if not ids:
        return set()
    return {row["id"] for row in neo4j_db.read(ANCESTORS, domain=domain, ids=ids)}


def ensure_progress_rows(db: Session, user_id: int, topic_ids: Iterable[str]) -> None:
    """Create any missing topic_progress rows with BKT defaults. Safe under concurrent calls."""
    values = [{"user_id": user_id, "topic_id": topic_id} for topic_id in sorted(set(topic_ids))]
    if values:
        db.execute(
            insert(TopicProgress).values(values).on_conflict_do_nothing(index_elements=["user_id", "topic_id"])
        )


def sync_statuses(db: Session, user_id: int, domain: str) -> list[TopicInfo]:
    """Unlock every topic on the user's frontier and lock the rest of the not-yet-started topics.

    Completed and in-progress rows are never changed here, so a completed topic is never relocked.
    Frontier topics without a row (e.g. a topic added to the curriculum after onboarding) get one.
    Returns the frontier. Does not commit.
    """
    progress = get_progress_map(db, user_id)
    completed = [tid for tid, row in progress.items() if row.status == TopicStatus.COMPLETED]
    frontier = get_frontier(domain, completed)
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

    Before onboarding (no progress rows) nothing is written: the starting frontier is returned with
    onboarded=False so the client can send the learner to onboarding first. Otherwise statuses are
    synced so any topic that has become learnable is stored as unlocked.
    """
    ensure_domain(domain)
    progress = get_progress_map(db, user_id)
    if not progress:
        frontier = get_frontier(domain, [])
        return {
            "domain": domain,
            "onboarded": False,
            "curriculum_complete": False,
            "recommended": recommendations(frontier, {}),
        }

    frontier = sync_statuses(db, user_id, domain)
    db.commit()
    progress = get_progress_map(db, user_id)
    return {
        "domain": domain,
        "onboarded": True,
        # In an acyclic prerequisite graph the frontier is only empty once every topic is completed.
        "curriculum_complete": not frontier,
        "recommended": recommendations(frontier, progress),
    }


def mark_known(db: Session, user_id: int, domain: str, topic_ids: list[str]) -> dict[str, Any]:
    """Onboarding: initialise the user's progress and mark the topics they already know.

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

    added_prerequisites = get_ancestors(domain, selected) - selected
    known = selected | added_prerequisites

    ensure_progress_rows(db, user_id, all_ids)
    progress = get_progress_map(db, user_id)
    for topic_id in known:
        row = progress[topic_id]
        row.status = TopicStatus.COMPLETED.value
        row.p_know = max(row.p_know, KNOWN_TOPIC_P_KNOW)
        row.needs_attention = False

    frontier = sync_statuses(db, user_id, domain)
    db.commit()
    logger.info("Onboarding saved for user id=%s: %d known topics", user_id, len(known))

    return {
        "message": "Onboarding saved",
        "known_count": len(known),
        "added_prerequisites": sorted(added_prerequisites),
        "recommended": recommendations(frontier, progress),
    }
