"""Seeder integration tests against the running Neo4j.

Neo4j Community has a single database, so these tests use their own domain ("pytest-seed")
with "pytest_"-prefixed ids and delete it afterwards. The real web-development curriculum is
never read or modified. Skipped automatically when Neo4j is not reachable.
"""

import json

import pytest

from db import neo4j_db
from seed.curriculum import Resource, Topic
from seed.seed_graph import seed_curriculum

TEST_DOMAIN = "pytest-seed"
RES = (Resource("Docs", "https://example.com/docs", "docs"),)


def _topic(suffix: str, difficulty: int = 1) -> Topic:
    return Topic(f"pytest_{suffix}", f"Topic {suffix.upper()}", f"Description {suffix}", difficulty, RES)


A, B, C, D = _topic("a"), _topic("b", 2), _topic("c", 2), _topic("d", 3)
TOPICS = (A, B, C, D)
EDGES = ((A.id, B.id), (A.id, C.id), (B.id, D.id), (C.id, D.id))


def _cleanup() -> None:
    neo4j_db.write("MATCH (t:Topic {domain: $domain}) DETACH DELETE t", domain=TEST_DOMAIN)


@pytest.fixture(autouse=True)
def isolated_domain():
    try:
        neo4j_db.check_connection()
    except Exception as exc:
        pytest.skip(f"Neo4j not reachable: {exc}")
    _cleanup()
    yield
    _cleanup()


def _counts() -> tuple[int, int]:
    row = neo4j_db.read(
        "MATCH (t:Topic {domain: $d}) OPTIONAL MATCH (t)-[r:PREREQUISITE_OF]->() "
        "RETURN count(DISTINCT t) AS topics, count(r) AS edges",
        d=TEST_DOMAIN,
    )[0]
    return row["topics"], row["edges"]


def test_first_seed_creates_all_topics_and_edges():
    result = seed_curriculum(TOPICS, EDGES, TEST_DOMAIN)
    assert (result.topics, result.edges) == (4, 4)
    assert (result.topics_created, result.edges_created) == (4, 4)
    assert _counts() == (4, 4)


def test_reseeding_is_idempotent():
    seed_curriculum(TOPICS, EDGES, TEST_DOMAIN)
    for _ in range(3):
        result = seed_curriculum(TOPICS, EDGES, TEST_DOMAIN)
        assert (result.topics_created, result.edges_created) == (0, 0)
        assert (result.topics_removed, result.edges_removed) == (0, 0)
    assert _counts() == (4, 4)


def test_edges_point_from_prerequisite_to_dependent():
    seed_curriculum(TOPICS, EDGES, TEST_DOMAIN)
    rows = neo4j_db.read(
        "MATCH (pre:Topic {domain: $d})-[:PREREQUISITE_OF]->(next:Topic {domain: $d}) "
        "RETURN pre.id AS source, next.id AS target",
        d=TEST_DOMAIN,
    )
    assert {(r["source"], r["target"]) for r in rows} == set(EDGES)


def test_topic_properties_and_resources_are_stored():
    seed_curriculum(TOPICS, EDGES, TEST_DOMAIN)
    node = neo4j_db.read("MATCH (t:Topic {id: $id}) RETURN t", id=B.id)[0]["t"]
    assert node["name"] == B.name
    assert node["description"] == B.description
    assert node["difficulty"] == 2
    assert node["domain"] == TEST_DOMAIN
    assert json.loads(node["resources"]) == [{"title": "Docs", "url": "https://example.com/docs", "type": "docs"}]


def test_changed_topic_details_are_updated_in_place():
    seed_curriculum(TOPICS, EDGES, TEST_DOMAIN)
    renamed = Topic(A.id, "Renamed", "New description", 1, RES)
    result = seed_curriculum((renamed, B, C, D), EDGES, TEST_DOMAIN)
    assert result.topics_created == 0
    node = neo4j_db.read("MATCH (t:Topic {id: $id}) RETURN t", id=A.id)[0]["t"]
    assert (node["name"], node["description"]) == ("Renamed", "New description")


def test_removed_topics_and_edges_are_pruned():
    seed_curriculum(TOPICS, EDGES, TEST_DOMAIN)
    result = seed_curriculum((A, B, C), ((A.id, B.id), (A.id, C.id)), TEST_DOMAIN)
    # D and its two incoming edges disappear with DETACH DELETE; no other edge is stale.
    assert result.topics_removed == 1
    assert _counts() == (3, 2)


def test_removed_edge_between_kept_topics_is_pruned():
    seed_curriculum(TOPICS, EDGES, TEST_DOMAIN)
    result = seed_curriculum(TOPICS, EDGES[:-1], TEST_DOMAIN)
    assert result.edges_removed == 1
    assert _counts() == (4, 3)


def test_schema_constraint_and_index_exist():
    seed_curriculum(TOPICS, EDGES, TEST_DOMAIN)
    constraints = {r["name"] for r in neo4j_db.read("SHOW CONSTRAINTS YIELD name RETURN name")}
    indexes = {r["name"] for r in neo4j_db.read("SHOW INDEXES YIELD name RETURN name")}
    assert "topic_id_unique" in constraints
    assert "topic_domain" in indexes
