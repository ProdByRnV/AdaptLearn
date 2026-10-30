"""Write the curriculum to Neo4j.

Graph model: (:Domain), (:Topic)-[:IN_DOMAIN]->(:Domain) for every domain that uses a topic, and
(:Topic)-[:PREREQUISITE_OF]->(:Topic) edges that may cross domains.

Idempotent: domains, topics, memberships and edges are MERGEd, so running it any number of times
leaves exactly the curriculum in seed/curriculum.py. Anything tagged with the same catalog that is
no longer in the curriculum is removed, so the graph always mirrors the files. Other catalogs (the
tests use their own) are never touched.

Runs automatically on backend startup. To run it by hand (e.g. against Neo4j Aura):
    python -m seed.seed_graph
"""

import json
import logging
from dataclasses import asdict, dataclass

from neo4j import ManagedTransaction

from db.neo4j_db import close_driver, get_driver
from seed.curriculum import CATALOG, DOMAINS, Domain, validate_curriculum

logger = logging.getLogger("adaptlearn")

# Uniqueness constraints are backed by indexes, so they also serve lookups by id. The per-topic
# domain index belonged to the single-domain model (before Phase 22) and is dropped.
SCHEMA_STATEMENTS = (
    "CREATE CONSTRAINT topic_id_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE",
    "CREATE CONSTRAINT domain_id_unique IF NOT EXISTS FOR (d:Domain) REQUIRE d.id IS UNIQUE",
    "DROP INDEX topic_domain IF EXISTS",
)

UPSERT_DOMAINS = """
UNWIND $domains AS domain
MERGE (d:Domain {id: domain.id})
SET d.name = domain.name, d.description = domain.description, d.catalog = $catalog
"""

UPSERT_TOPICS = """
UNWIND $topics AS topic
MERGE (t:Topic {id: topic.id})
SET t.name = topic.name,
    t.description = topic.description,
    t.difficulty = topic.difficulty,
    t.home_domain = topic.home_domain,
    t.resources = topic.resources,
    t.catalog = $catalog
REMOVE t.domain
"""

REMOVE_STALE_TOPICS = """
MATCH (t:Topic {catalog: $catalog})
WHERE NOT t.id IN $ids
DETACH DELETE t
"""

REMOVE_STALE_DOMAINS = """
MATCH (d:Domain {catalog: $catalog})
WHERE NOT d.id IN $ids
DETACH DELETE d
"""

UPSERT_MEMBERSHIPS = """
UNWIND $memberships AS m
MATCH (t:Topic {id: m.topic, catalog: $catalog})
MATCH (d:Domain {id: m.domain, catalog: $catalog})
MERGE (t)-[:IN_DOMAIN]->(d)
RETURN count(*) AS matched
"""

REMOVE_STALE_MEMBERSHIPS = """
MATCH (t:Topic {catalog: $catalog})-[r:IN_DOMAIN]->(d:Domain {catalog: $catalog})
WHERE NOT [t.id, d.id] IN $pairs
DELETE r
"""

UPSERT_EDGES = """
UNWIND $edges AS edge
MATCH (pre:Topic {id: edge.source, catalog: $catalog})
MATCH (next:Topic {id: edge.target, catalog: $catalog})
MERGE (pre)-[:PREREQUISITE_OF]->(next)
RETURN count(*) AS matched
"""

REMOVE_STALE_EDGES = """
MATCH (pre:Topic {catalog: $catalog})-[r:PREREQUISITE_OF]->(next:Topic {catalog: $catalog})
WHERE NOT [pre.id, next.id] IN $pairs
DELETE r
"""

COUNT_GRAPH = """
CALL () { MATCH (d:Domain {catalog: $catalog}) RETURN count(d) AS domains }
CALL () { MATCH (t:Topic {catalog: $catalog}) RETURN count(t) AS topics }
CALL () { MATCH (:Topic {catalog: $catalog})-[m:IN_DOMAIN]->(:Domain {catalog: $catalog}) RETURN count(m) AS memberships }
CALL () { MATCH (:Topic {catalog: $catalog})-[e:PREREQUISITE_OF]->(:Topic {catalog: $catalog}) RETURN count(e) AS edges }
RETURN domains, topics, memberships, edges
"""


@dataclass(frozen=True)
class SeedResult:
    catalog: str
    domains: int
    topics: int
    memberships: int
    edges: int
    topics_created: int
    edges_created: int
    topics_removed: int
    edges_removed: int


def _topic_rows(domains: tuple[Domain, ...]) -> list[dict]:
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "difficulty": t.difficulty,
            "home_domain": d.id,
            # Neo4j properties can't hold maps, so resources are stored as a JSON string
            # (ARCHITECTURE.md section 6). Parsing happens in one place when topics are read.
            "resources": json.dumps([asdict(r) for r in t.resources]),
        }
        for d in domains
        for t in d.topics
    ]


def _write_curriculum(tx: ManagedTransaction, domains: tuple[Domain, ...], catalog: str) -> SeedResult:
    topics = _topic_rows(domains)
    memberships = [{"topic": topic_id, "domain": d.id} for d in domains for topic_id in d.topic_ids]
    edges = [{"source": s, "target": t} for d in domains for s, t in d.prerequisites]

    tx.run(UPSERT_DOMAINS, domains=[{"id": d.id, "name": d.name, "description": d.description} for d in domains],
           catalog=catalog).consume()
    topic_counters = tx.run(UPSERT_TOPICS, topics=topics, catalog=catalog).consume().counters
    removed_topics = tx.run(REMOVE_STALE_TOPICS, ids=[t["id"] for t in topics], catalog=catalog).consume().counters
    tx.run(REMOVE_STALE_DOMAINS, ids=[d.id for d in domains], catalog=catalog).consume()

    # Every MERGE below must match its nodes; otherwise the whole transaction rolls back, so a
    # half-seeded graph is never left behind.
    matched = tx.run(UPSERT_MEMBERSHIPS, memberships=memberships, catalog=catalog).single()["matched"]
    if matched != len(memberships):
        raise RuntimeError(f"Only {matched} of {len(memberships)} domain memberships matched existing nodes")
    tx.run(REMOVE_STALE_MEMBERSHIPS, pairs=[[m["topic"], m["domain"]] for m in memberships], catalog=catalog).consume()

    edge_result = tx.run(UPSERT_EDGES, edges=edges, catalog=catalog)
    matched = edge_result.single()["matched"]
    edge_counters = edge_result.consume().counters
    if matched != len(edges):
        raise RuntimeError(f"Only {matched} of {len(edges)} prerequisite edges matched existing topics")
    removed_edges = tx.run(REMOVE_STALE_EDGES, pairs=[[e["source"], e["target"]] for e in edges],
                           catalog=catalog).consume().counters

    totals = tx.run(COUNT_GRAPH, catalog=catalog).single()
    return SeedResult(
        catalog=catalog,
        domains=totals["domains"],
        topics=totals["topics"],
        memberships=totals["memberships"],
        edges=totals["edges"],
        topics_created=topic_counters.nodes_created,
        edges_created=edge_counters.relationships_created,
        topics_removed=removed_topics.nodes_deleted,
        edges_removed=removed_edges.relationships_deleted,
    )


def seed_curriculum(domains: tuple[Domain, ...] = DOMAINS, catalog: str = CATALOG) -> SeedResult:
    validate_curriculum(domains)
    driver = get_driver()
    for statement in SCHEMA_STATEMENTS:
        driver.execute_query(statement)
    with driver.session() as session:
        result = session.execute_write(_write_curriculum, domains, catalog)
    logger.info(
        "Curriculum '%s' seeded: %d domains, %d topics, %d memberships, %d edges "
        "(created %d topics / %d edges, removed %d / %d)",
        result.catalog, result.domains, result.topics, result.memberships, result.edges,
        result.topics_created, result.edges_created, result.topics_removed, result.edges_removed,
    )
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        seed_curriculum()
    finally:
        close_driver()
