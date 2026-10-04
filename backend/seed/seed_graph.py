"""Write the curriculum to Neo4j.

Idempotent: topics and edges are MERGEd, so running it any number of times leaves exactly
the curriculum in seed/curriculum.py. Topics or edges in the domain that are no longer in
the curriculum are removed, so the graph always mirrors the file.

Runs automatically on backend startup. To run it by hand (e.g. against Neo4j Aura):
    python -m seed.seed_graph
"""

import json
import logging
from dataclasses import asdict, dataclass

from neo4j import ManagedTransaction

from db.neo4j_db import close_driver, get_driver
from seed.curriculum import DOMAIN, PREREQUISITES, TOPICS, Topic, validate_curriculum

logger = logging.getLogger("adaptlearn")

# The uniqueness constraint is backed by an index, so it also serves lookups by id.
SCHEMA_STATEMENTS = (
    "CREATE CONSTRAINT topic_id_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE",
    "CREATE INDEX topic_domain IF NOT EXISTS FOR (t:Topic) ON (t.domain)",
)

UPSERT_TOPICS = """
UNWIND $topics AS topic
MERGE (t:Topic {id: topic.id})
SET t.name = topic.name,
    t.description = topic.description,
    t.difficulty = topic.difficulty,
    t.domain = topic.domain,
    t.resources = topic.resources
"""

REMOVE_STALE_TOPICS = """
MATCH (t:Topic {domain: $domain})
WHERE NOT t.id IN $ids
DETACH DELETE t
"""

UPSERT_EDGES = """
UNWIND $edges AS edge
MATCH (pre:Topic {id: edge.source, domain: $domain})
MATCH (next:Topic {id: edge.target, domain: $domain})
MERGE (pre)-[:PREREQUISITE_OF]->(next)
RETURN count(*) AS matched
"""

REMOVE_STALE_EDGES = """
MATCH (pre:Topic {domain: $domain})-[r:PREREQUISITE_OF]->(next:Topic {domain: $domain})
WHERE NOT [pre.id, next.id] IN $pairs
DELETE r
"""

COUNT_GRAPH = """
MATCH (t:Topic {domain: $domain})
OPTIONAL MATCH (t)-[r:PREREQUISITE_OF]->(:Topic {domain: $domain})
RETURN count(DISTINCT t) AS topics, count(r) AS edges
"""


@dataclass(frozen=True)
class SeedResult:
    domain: str
    topics: int
    edges: int
    topics_created: int
    edges_created: int
    topics_removed: int
    edges_removed: int


def _topic_rows(topics: tuple[Topic, ...], domain: str) -> list[dict]:
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "difficulty": t.difficulty,
            "domain": domain,
            # Neo4j properties can't hold maps, so resources are stored as a JSON string
            # (ARCHITECTURE.md section 6). Parsing happens in one place when topics are read.
            "resources": json.dumps([asdict(r) for r in t.resources]),
        }
        for t in topics
    ]


def _write_curriculum(
    tx: ManagedTransaction, rows: list[dict], edges: tuple[tuple[str, str], ...], domain: str
) -> SeedResult:
    topic_counters = tx.run(UPSERT_TOPICS, topics=rows).consume().counters
    removed_topics = tx.run(REMOVE_STALE_TOPICS, domain=domain, ids=[r["id"] for r in rows]).consume().counters

    edge_result = tx.run(
        UPSERT_EDGES, domain=domain, edges=[{"source": s, "target": t} for s, t in edges]
    )
    matched = edge_result.single()["matched"]
    edge_counters = edge_result.consume().counters
    if matched != len(edges):
        # Rolls back the whole transaction - never leave a half-seeded graph.
        raise RuntimeError(f"Only {matched} of {len(edges)} prerequisite edges matched existing topics")
    removed_edges = tx.run(REMOVE_STALE_EDGES, domain=domain, pairs=[[s, t] for s, t in edges]).consume().counters

    totals = tx.run(COUNT_GRAPH, domain=domain).single()
    return SeedResult(
        domain=domain,
        topics=totals["topics"],
        edges=totals["edges"],
        topics_created=topic_counters.nodes_created,
        edges_created=edge_counters.relationships_created,
        topics_removed=removed_topics.nodes_deleted,
        edges_removed=removed_edges.relationships_deleted,
    )


def seed_curriculum(
    topics: tuple[Topic, ...] = TOPICS,
    edges: tuple[tuple[str, str], ...] = PREREQUISITES,
    domain: str = DOMAIN,
) -> SeedResult:
    validate_curriculum(topics, edges)
    driver = get_driver()
    for statement in SCHEMA_STATEMENTS:
        driver.execute_query(statement)
    with driver.session() as session:
        result = session.execute_write(_write_curriculum, _topic_rows(topics, domain), edges, domain)
    logger.info(
        "Curriculum '%s' seeded: %d topics, %d edges (created %d topics / %d edges, removed %d / %d)",
        result.domain, result.topics, result.edges,
        result.topics_created, result.edges_created, result.topics_removed, result.edges_removed,
    )
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        seed_curriculum()
    finally:
        close_driver()
