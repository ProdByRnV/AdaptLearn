"""Curriculum reads from Neo4j, merged with a user's progress from PostgreSQL.

All topic queries go through here so Cypher stays in one place and resources are parsed
from their stored JSON string in exactly one function.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from db import neo4j_db
from models import TopicProgress, TopicStatus
from models.models import DEFAULT_P_KNOW, MASTERY_THRESHOLD
from seed.curriculum import DOMAIN

logger = logging.getLogger("adaptlearn")

# Only fully seeded domains are exposed (PRD US-03: no empty domains).
SUPPORTED_DOMAINS: tuple[str, ...] = (DOMAIN,)

TOPICS_WITH_PREREQUISITES = """
MATCH (t:Topic {domain: $domain})
OPTIONAL MATCH (pre:Topic {domain: $domain})-[:PREREQUISITE_OF]->(t)
WITH t, collect(pre.id) AS prerequisites
RETURN t.id AS id, t.name AS name, t.description AS description,
       t.difficulty AS difficulty, t.resources AS resources, prerequisites
ORDER BY t.difficulty ASC, t.name ASC
"""


class UnknownDomainError(Exception):
    pass


@dataclass(frozen=True)
class TopicInfo:
    id: str
    name: str
    description: str
    difficulty: int
    resources: list[dict[str, str]] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)


def ensure_domain(domain: str) -> None:
    if domain not in SUPPORTED_DOMAINS:
        raise UnknownDomainError(domain)


def parse_resources(raw: Any) -> list[dict[str, str]]:
    """Resources are stored on the node as a JSON string; a corrupt value degrades to no resources."""
    if not raw:
        return []
    try:
        items = json.loads(raw) if isinstance(raw, str) else raw
        return [
            {"title": str(item["title"]), "url": str(item["url"]), "type": str(item["type"])}
            for item in items
        ]
    except (TypeError, ValueError, KeyError) as exc:
        logger.warning("Could not parse topic resources %r: %s", raw, exc)
        return []


def get_topics(domain: str = DOMAIN) -> list[TopicInfo]:
    """All topics in a domain with their prerequisite ids, ordered by difficulty then name."""
    ensure_domain(domain)
    rows = neo4j_db.read(TOPICS_WITH_PREREQUISITES, domain=domain)
    return [
        TopicInfo(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            difficulty=row["difficulty"],
            resources=parse_resources(row["resources"]),
            prerequisites=sorted(row["prerequisites"]),
        )
        for row in rows
    ]


def get_progress_map(db: Session, user_id: int) -> dict[str, TopicProgress]:
    rows = db.scalars(select(TopicProgress).where(TopicProgress.user_id == user_id))
    return {row.topic_id: row for row in rows}


def effective_state(topic: TopicInfo, progress: dict[str, TopicProgress]) -> tuple[str, float]:
    """(status, p_know) for one topic.

    A stored progress row is authoritative. Without one (e.g. before onboarding creates the
    rows), the status is derived from the graph: unlocked when every prerequisite is completed,
    otherwise locked, with the default BKT starting mastery.
    """
    row = progress.get(topic.id)
    if row is not None:
        return row.status, row.p_know
    prerequisites_done = all(
        (pre := progress.get(pre_id)) is not None and pre.status == TopicStatus.COMPLETED
        for pre_id in topic.prerequisites
    )
    status = TopicStatus.UNLOCKED if prerequisites_done else TopicStatus.LOCKED
    return status.value, DEFAULT_P_KNOW


def to_percent(p_know: float) -> float:
    return round(p_know * 100, 1)


def build_graph(db: Session, user_id: int, domain: str = DOMAIN) -> dict[str, Any]:
    topics = get_topics(domain)
    progress = get_progress_map(db, user_id)
    nodes, links = [], []
    for topic in topics:
        status, p_know = effective_state(topic, progress)
        nodes.append(
            {
                "id": topic.id,
                "name": topic.name,
                "description": topic.description,
                "difficulty": topic.difficulty,
                "status": status,
                "mastery": to_percent(p_know),
                "mastered": p_know >= MASTERY_THRESHOLD,
                "prerequisites": topic.prerequisites,
                "resources": topic.resources,
            }
        )
        links.extend({"source": pre_id, "target": topic.id} for pre_id in topic.prerequisites)
    return {"domain": domain, "nodes": nodes, "links": links}
