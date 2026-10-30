"""Curriculum reads from Neo4j, merged with a user's progress from PostgreSQL.

All topic queries go through here so Cypher stays in one place and resources are parsed
from their stored JSON string in exactly one function.

Topics form one shared pool. A domain is a collection of topics, and a topic's prerequisites may
belong to other domains, so reads are scoped by domain membership but prerequisites never are.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from db import neo4j_db
from models import TopicProgress, TopicStatus
from services.bkt import DEFAULT_P_KNOW, mastery_reached
from seed.curriculum import DEFAULT_DOMAIN, DOMAIN_BY_ID

logger = logging.getLogger("adaptlearn")

# Only fully seeded domains are exposed (PRD US-03: no empty domains). Reads only ever see topics
# that belong to one of these, so other seeded catalogs (the tests') stay invisible.
SUPPORTED_DOMAINS: tuple[str, ...] = tuple(DOMAIN_BY_ID)

# Shared projection: a topic, its prerequisites (from any domain) and the supported domains using it.
_TOPIC_FIELDS = """
OPTIONAL MATCH (pre:Topic)-[:PREREQUISITE_OF]->(t)
WITH t, collect(pre {.id, .name, .home_domain}) AS prereqs
RETURN t.id AS id, t.name AS name, t.description AS description,
       t.difficulty AS difficulty, t.resources AS resources, t.home_domain AS home_domain,
       [(t)-[:IN_DOMAIN]->(m:Domain) WHERE m.id IN $domains | m.id] AS domains, prereqs
ORDER BY t.difficulty ASC, t.name ASC
"""

DOMAIN_TOPICS = """
MATCH (t:Topic)-[:IN_DOMAIN]->(:Domain {id: $domain})
""" + _TOPIC_FIELDS

ALL_TOPICS = """
MATCH (t:Topic)
WHERE EXISTS { (t)-[:IN_DOMAIN]->(d:Domain) WHERE d.id IN $domains }
""" + _TOPIC_FIELDS

TOPIC_BY_ID = """
MATCH (t:Topic {id: $id})
WHERE EXISTS { (t)-[:IN_DOMAIN]->(d:Domain) WHERE d.id IN $domains }
""" + _TOPIC_FIELDS


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
    prerequisite_names: list[str] = field(default_factory=list)
    home_domain: str = DEFAULT_DOMAIN
    domains: list[str] = field(default_factory=list)  # every supported domain that uses this topic
    prerequisite_domains: list[str] = field(default_factory=list)  # home domain of each prerequisite


def ensure_domain(domain: str) -> None:
    if domain not in SUPPORTED_DOMAINS:
        raise UnknownDomainError(domain)


def domain_name(domain: str) -> str:
    return DOMAIN_BY_ID[domain].name if domain in DOMAIN_BY_ID else domain


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


def topic_from_row(row: Any) -> TopicInfo:
    prereqs = sorted(row["prereqs"], key=lambda p: p["id"])
    return TopicInfo(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        difficulty=row["difficulty"],
        resources=parse_resources(row["resources"]),
        prerequisites=[p["id"] for p in prereqs],
        prerequisite_names=[p["name"] for p in prereqs],
        home_domain=row["home_domain"],
        domains=sorted(row["domains"]),
        prerequisite_domains=[p["home_domain"] for p in prereqs],
    )


def get_topics(domain: str = DEFAULT_DOMAIN) -> list[TopicInfo]:
    """All topics in a domain with their prerequisite ids (from any domain), ordered by difficulty then name."""
    ensure_domain(domain)
    rows = neo4j_db.read(DOMAIN_TOPICS, domain=domain, domains=list(SUPPORTED_DOMAINS))
    return [topic_from_row(row) for row in rows]


def get_all_topics() -> list[TopicInfo]:
    """Every topic in any supported domain (each once, with all its domains), easiest first."""
    rows = neo4j_db.read(ALL_TOPICS, domains=list(SUPPORTED_DOMAINS))
    return [topic_from_row(row) for row in rows]


def get_topic(topic_id: str) -> TopicInfo | None:
    """One topic from the shared pool, whichever domains it belongs to."""
    rows = neo4j_db.read(TOPIC_BY_ID, id=topic_id, domains=list(SUPPORTED_DOMAINS))
    return topic_from_row(rows[0]) if rows else None


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


def percent_of(part: int, whole: int) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def build_graph(db: Session, user_id: int, domain: str = DEFAULT_DOMAIN) -> dict[str, Any]:
    """The domain's topics and the links between them.

    Prerequisites from other domains aren't drawn as links (their topics aren't nodes of this
    graph); they are listed per node in external_prerequisites instead.
    """
    nodes, links = _graph(get_topics(domain), get_progress_map(db, user_id))
    return {
        "domain": domain, "domain_name": domain_name(domain), "domains": domain_refs(), "nodes": nodes, "links": links,
    }


def build_map(db: Session, user_id: int) -> dict[str, Any]:
    """Every topic in every domain, each once, with every prerequisite as a link (the whole map)."""
    nodes, links = _graph(get_all_topics(), get_progress_map(db, user_id))
    return {"domains": domain_refs(), "nodes": nodes, "links": links}


def domain_refs() -> list[dict[str, str]]:
    """Every supported domain's id and name, in curriculum order."""
    return [{"id": d, "name": domain_name(d)} for d in SUPPORTED_DOMAINS]


def _graph(topics: list[TopicInfo], progress: dict[str, TopicProgress]) -> tuple[list[dict], list[dict]]:
    """Nodes with the learner's status, and links between topics that are both in `topics`."""
    in_domain = {t.id for t in topics}
    nodes, links = [], []
    for topic in topics:
        status, p_know = effective_state(topic, progress)
        internal = [pre_id for pre_id in topic.prerequisites if pre_id in in_domain]
        external = [
            {
                "id": pre_id,
                "name": name,
                "domain": pre_domain,
                "domain_name": domain_name(pre_domain),
                "completed": (row := progress.get(pre_id)) is not None and row.status == TopicStatus.COMPLETED,
            }
            for pre_id, name, pre_domain in zip(
                topic.prerequisites, topic.prerequisite_names, topic.prerequisite_domains, strict=True
            )
            if pre_id not in in_domain
        ]
        nodes.append(
            {
                "id": topic.id,
                "name": topic.name,
                "description": topic.description,
                "difficulty": topic.difficulty,
                "status": status,
                "mastery": to_percent(p_know),
                "mastered": mastery_reached(p_know),
                "prerequisites": internal,
                "external_prerequisites": external,
                "domains": topic.domains,
                "home_domain": topic.home_domain,
                "resources": topic.resources,
            }
        )
        links.extend({"source": pre_id, "target": topic.id} for pre_id in internal)
    return nodes, links
