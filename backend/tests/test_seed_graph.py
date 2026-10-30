"""Seeder integration tests against the running Neo4j.

Neo4j Community has a single database, so these tests seed their own catalog ("pytest-seed")
with "pytest-" domains and "pytest_" topic ids, and delete it afterwards. The real curriculum
is never modified (one test checks exactly that). Skipped automatically when Neo4j is not reachable.
"""

import json

import pytest

from db import neo4j_db
from seed.curriculum import CATALOG, TOPICS as REAL_TOPICS, Domain, Resource, Topic
from seed.seed_graph import seed_curriculum

TEST_CATALOG = "pytest-seed"
RES = (Resource("Docs", "https://example.com/docs", "docs"),)


def _topic(suffix: str, difficulty: int = 1) -> Topic:
    return Topic(f"pytest_{suffix}", f"Topic {suffix.upper()}", f"Description {suffix}", difficulty, RES)


A, B, C, D, E = _topic("a"), _topic("b", 2), _topic("c", 2), _topic("d", 3), _topic("e", 2)
ONE_EDGES = ((A.id, B.id), (A.id, C.id), (B.id, D.id), (C.id, D.id))
ONE = Domain("pytest-one", "Pytest One", "First test domain", (A, B, C, D), ONE_EDGES)
# Two defines E, which needs B from One first, and shares A.
TWO = Domain("pytest-two", "Pytest Two", "Second test domain", (E,), ((B.id, E.id),), shared=(A.id,))
DOMAINS = (ONE, TWO)
ALL_EDGES = set(ONE_EDGES) | {(B.id, E.id)}


def seed(domains=DOMAINS):
    return seed_curriculum(domains, TEST_CATALOG)


def _cleanup() -> None:
    neo4j_db.write("MATCH (n {catalog: $c}) DETACH DELETE n", c=TEST_CATALOG)
    neo4j_db.write("MATCH (t:Topic) WHERE t.id STARTS WITH 'pytest_' DETACH DELETE t")
    neo4j_db.write("MATCH (d:Domain) WHERE d.id STARTS WITH 'pytest-' DETACH DELETE d")


@pytest.fixture(autouse=True)
def isolated_catalog():
    try:
        neo4j_db.check_connection()
    except Exception as exc:
        pytest.skip(f"Neo4j not reachable: {exc}")
    _cleanup()
    yield
    _cleanup()


def _counts() -> dict[str, int]:
    return neo4j_db.read(
        "CALL () { MATCH (d:Domain {catalog: $c}) RETURN count(d) AS domains } "
        "CALL () { MATCH (t:Topic {catalog: $c}) RETURN count(t) AS topics } "
        "CALL () { MATCH (:Topic {catalog: $c})-[m:IN_DOMAIN]->() RETURN count(m) AS memberships } "
        "CALL () { MATCH (:Topic {catalog: $c})-[e:PREREQUISITE_OF]->() RETURN count(e) AS edges } "
        "RETURN domains, topics, memberships, edges",
        c=TEST_CATALOG,
    )[0]


def _members(domain_id: str) -> set[str]:
    rows = neo4j_db.read("MATCH (t:Topic)-[:IN_DOMAIN]->(:Domain {id: $d}) RETURN t.id AS id", d=domain_id)
    return {r["id"] for r in rows}


def test_first_seed_creates_domains_topics_memberships_and_edges():
    result = seed()
    assert (result.domains, result.topics, result.memberships, result.edges) == (2, 5, 6, 5)
    assert (result.topics_created, result.edges_created) == (5, 5)
    assert _counts() == {"domains": 2, "topics": 5, "memberships": 6, "edges": 5}


def test_a_shared_topic_is_one_node_in_both_domains():
    seed()
    assert _members("pytest-one") == {A.id, B.id, C.id, D.id}
    assert _members("pytest-two") == {E.id, A.id}
    rows = neo4j_db.read("MATCH (t:Topic {id: $id}) RETURN count(t) AS n", id=A.id)
    assert rows[0]["n"] == 1


def test_reseeding_is_idempotent():
    seed()
    for _ in range(3):
        result = seed()
        assert (result.topics_created, result.edges_created) == (0, 0)
        assert (result.topics_removed, result.edges_removed) == (0, 0)
    assert _counts() == {"domains": 2, "topics": 5, "memberships": 6, "edges": 5}


def test_edges_point_from_prerequisite_to_dependent_including_across_domains():
    seed()
    rows = neo4j_db.read(
        "MATCH (pre:Topic {catalog: $c})-[:PREREQUISITE_OF]->(next:Topic {catalog: $c}) "
        "RETURN pre.id AS source, next.id AS target",
        c=TEST_CATALOG,
    )
    assert {(r["source"], r["target"]) for r in rows} == ALL_EDGES


def test_domain_and_topic_properties_are_stored():
    seed()
    domain = neo4j_db.read("MATCH (d:Domain {id: 'pytest-two'}) RETURN d")[0]["d"]
    assert (domain["name"], domain["description"], domain["catalog"]) == ("Pytest Two", "Second test domain", TEST_CATALOG)
    node = neo4j_db.read("MATCH (t:Topic {id: $id}) RETURN t", id=E.id)[0]["t"]
    assert node["name"] == E.name
    assert node["description"] == E.description
    assert node["difficulty"] == 2
    assert node["home_domain"] == "pytest-two"
    assert node["catalog"] == TEST_CATALOG
    assert "domain" not in node
    assert json.loads(node["resources"]) == [{"title": "Docs", "url": "https://example.com/docs", "type": "docs"}]


def test_changed_topic_and_domain_details_are_updated_in_place():
    seed()
    renamed = Topic(A.id, "Renamed", "New description", 1, RES)
    one = Domain(ONE.id, "Renamed domain", ONE.description, (renamed, B, C, D), ONE_EDGES)
    result = seed((one, TWO))
    assert result.topics_created == 0
    node = neo4j_db.read("MATCH (t:Topic {id: $id}) RETURN t", id=A.id)[0]["t"]
    assert (node["name"], node["description"]) == ("Renamed", "New description")
    assert neo4j_db.read("MATCH (d:Domain {id: $id}) RETURN d.name AS n", id=ONE.id)[0]["n"] == "Renamed domain"


def test_removed_topics_and_edges_are_pruned():
    seed()
    one = Domain(ONE.id, ONE.name, ONE.description, (A, B, C), ((A.id, B.id), (A.id, C.id)))
    result = seed((one, TWO))
    # D, its two incoming edges and its membership disappear with DETACH DELETE.
    assert result.topics_removed == 1
    assert _counts() == {"domains": 2, "topics": 4, "memberships": 5, "edges": 3}


def test_removed_edge_between_kept_topics_is_pruned():
    seed()
    result = seed((ONE, Domain(TWO.id, TWO.name, TWO.description, (E,), (), shared=(A.id,))))
    assert result.edges_removed == 1
    assert _counts()["edges"] == 4


def test_unsharing_a_topic_removes_only_that_membership():
    seed()
    seed((ONE, Domain(TWO.id, TWO.name, TWO.description, (E,), ((B.id, E.id),))))
    assert _members("pytest-two") == {E.id}
    assert A.id in _members("pytest-one")
    assert _counts()["topics"] == 5


def test_a_topic_can_move_to_another_home_domain_and_keep_its_node():
    seed()
    # A moves from One to Two; One now shares it.
    one = Domain(ONE.id, ONE.name, ONE.description, (B, C, D), ONE_EDGES, shared=(A.id,))
    two = Domain(TWO.id, TWO.name, TWO.description, (A, E), ((B.id, E.id),))
    result = seed((one, two))
    assert (result.topics_created, result.topics_removed) == (0, 0)
    node = neo4j_db.read("MATCH (t:Topic {id: $id}) RETURN t", id=A.id)[0]["t"]
    assert node["home_domain"] == "pytest-two"
    assert A.id in _members("pytest-one") and A.id in _members("pytest-two")


def test_removed_domain_is_pruned():
    seed()
    result = seed((ONE,))
    assert result.domains == 1
    assert neo4j_db.read("MATCH (d:Domain {id: $id}) RETURN count(d) AS n", id=TWO.id)[0]["n"] == 0
    assert _counts() == {"domains": 1, "topics": 4, "memberships": 4, "edges": 4}


def test_legacy_domain_property_is_removed():
    # Before Phase 22 each topic stored its single domain as a property.
    neo4j_db.write("CREATE (:Topic {id: $id, domain: 'legacy'})", id=A.id)
    seed()
    node = neo4j_db.read("MATCH (t:Topic {id: $id}) RETURN t", id=A.id)[0]["t"]
    assert "domain" not in node and node["catalog"] == TEST_CATALOG


def test_real_curriculum_is_never_touched():
    real = seed_curriculum()  # the real curriculum, as backend startup seeds it
    seed()
    seed((ONE,))  # prunes One's catalog only
    after = neo4j_db.read(
        "MATCH (t:Topic {catalog: $c}) OPTIONAL MATCH (t)-[m:IN_DOMAIN]->() "
        "RETURN count(DISTINCT t) AS topics, count(m) AS memberships",
        c=CATALOG,
    )[0]
    assert after["topics"] == len(REAL_TOPICS) == real.topics
    assert after["memberships"] == real.memberships


def test_half_matched_memberships_roll_back_everything():
    # A shared id that isn't defined anywhere in this catalog (bypassing validation) must abort the
    # whole write, leaving nothing behind.
    from seed import seed_graph

    broken = Domain(TWO.id, TWO.name, TWO.description, (E,), ((B.id, E.id),), shared=(A.id, "pytest_missing"))
    with neo4j_db.get_driver().session() as session, pytest.raises(RuntimeError, match="memberships"):
        session.execute_write(seed_graph._write_curriculum, (ONE, broken), TEST_CATALOG)
    assert _counts() == {"domains": 0, "topics": 0, "memberships": 0, "edges": 0}


def test_half_matched_edges_roll_back_everything():
    from seed import seed_graph

    broken = Domain(TWO.id, TWO.name, TWO.description, (E,), (("pytest_missing", E.id),), shared=(A.id,))
    with neo4j_db.get_driver().session() as session, pytest.raises(RuntimeError, match="prerequisite edges"):
        session.execute_write(seed_graph._write_curriculum, (ONE, broken), TEST_CATALOG)
    assert _counts() == {"domains": 0, "topics": 0, "memberships": 0, "edges": 0}


def test_schema_constraints_exist_and_old_index_is_gone():
    seed()
    constraints = {r["name"] for r in neo4j_db.read("SHOW CONSTRAINTS YIELD name RETURN name")}
    indexes = {r["name"] for r in neo4j_db.read("SHOW INDEXES YIELD name RETURN name")}
    assert {"topic_id_unique", "domain_id_unique"} <= constraints
    assert "topic_domain" not in indexes
