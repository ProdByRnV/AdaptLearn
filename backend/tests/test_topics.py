"""Topics API tests.

These read the real web-development curriculum from Neo4j (read-only). The module fixture
runs the idempotent seeder first, which is exactly what backend startup does, so the tests
don't depend on the server having been started. Progress rows go to the PostgreSQL test DB.
Skipped automatically when Neo4j is not reachable.
"""

import pytest
from neo4j.exceptions import ServiceUnavailable

from db import neo4j_db
from models import TopicProgress
from seed.curriculum import PREREQUISITES, TOPICS
from seed.seed_graph import seed_curriculum
from services import topic_service
from services.topic_service import parse_resources

ROOTS = {"html_basics", "javascript_fundamentals", "git_basics", "sql_basics"}
SPEC_NODE_FIELDS = {"id", "name", "description", "difficulty", "status", "mastery", "resources"}


@pytest.fixture(scope="module", autouse=True)
def seeded_curriculum():
    try:
        neo4j_db.check_connection()
    except Exception as exc:
        pytest.skip(f"Neo4j not reachable: {exc}")
    seed_curriculum()


def _add_progress(db, user_id, topic_id, status, p_know=0.10):
    db.add(TopicProgress(user_id=user_id, topic_id=topic_id, status=status, p_know=p_know))
    db.commit()


def _nodes_by_id(response):
    return {node["id"]: node for node in response.json()["nodes"]}


# --- Auth & domain -------------------------------------------------------------

@pytest.mark.parametrize("path", ["/api/topics/all", "/api/topics/graph"])
def test_requires_authentication(client, path):
    response = client.get(path)
    assert response.status_code == 401


@pytest.mark.parametrize("path", ["/api/topics/all", "/api/topics/graph"])
def test_unknown_domain_returns_404(client, make_user, path):
    _, headers = make_user()
    response = client.get(path, params={"domain": "underwater-basket-weaving"}, headers=headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Unknown domain 'underwater-basket-weaving'"}


# --- GET /api/topics/all -------------------------------------------------------

def test_all_returns_the_30_topics_in_spec_shape(client, make_user):
    _, headers = make_user()
    response = client.get("/api/topics/all", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["domain"] == "web-development"
    assert len(body["topics"]) == 30
    assert {t["id"] for t in body["topics"]} == {t.id for t in TOPICS}
    for topic in body["topics"]:
        assert set(topic) == {"id", "name", "description", "difficulty", "resources"}
        assert 1 <= len(topic["resources"]) <= 3
        for resource in topic["resources"]:
            assert set(resource) == {"title", "url", "type"}


def test_all_is_ordered_by_difficulty_then_name(client, make_user):
    _, headers = make_user()
    topics = client.get("/api/topics/all", headers=headers).json()["topics"]
    keys = [(t["difficulty"], t["name"]) for t in topics]
    assert keys == sorted(keys)
    assert topics[0]["name"] == "CSS Basics"


def test_all_resources_match_the_curriculum_file(client, make_user):
    _, headers = make_user()
    topics = {t["id"]: t for t in client.get("/api/topics/all", headers=headers).json()["topics"]}
    for source in TOPICS:
        expected = [{"title": r.title, "url": r.url, "type": r.type} for r in source.resources]
        assert topics[source.id]["resources"] == expected


# --- GET /api/topics/graph -----------------------------------------------------

def test_graph_has_30_nodes_and_37_links_in_spec_shape(client, make_user):
    _, headers = make_user()
    response = client.get("/api/topics/graph", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body["nodes"]) == 30
    assert len(body["links"]) == 37
    for node in body["nodes"]:
        # Spec fields (ARCHITECTURE 13.7) plus mastered + prerequisites for the UI.
        assert set(node) == SPEC_NODE_FIELDS | {"mastered", "prerequisites"}
    for link in body["links"]:
        assert set(link) == {"source", "target"}


def test_graph_links_point_from_prerequisite_to_dependent(client, make_user):
    _, headers = make_user()
    links = client.get("/api/topics/graph", headers=headers).json()["links"]
    assert {(link["source"], link["target"]) for link in links} == set(PREREQUISITES)


def test_graph_node_prerequisites_match_links(client, make_user):
    _, headers = make_user()
    body = client.get("/api/topics/graph", headers=headers).json()
    for node in body["nodes"]:
        expected = sorted(link["source"] for link in body["links"] if link["target"] == node["id"])
        assert node["prerequisites"] == expected


def test_new_user_sees_roots_unlocked_and_everything_else_locked(client, make_user):
    _, headers = make_user()
    nodes = _nodes_by_id(client.get("/api/topics/graph", headers=headers))

    for topic_id, node in nodes.items():
        expected = "unlocked" if topic_id in ROOTS else "locked"
        assert node["status"] == expected, topic_id
        assert node["mastery"] == 10.0
        assert node["mastered"] is False


def test_stored_progress_drives_status_and_mastery(client, make_user, db):
    user_id, headers = make_user()
    _add_progress(db, user_id, "html_basics", "completed", p_know=0.95)
    _add_progress(db, user_id, "css_basics", "in_progress", p_know=0.4321)
    _add_progress(db, user_id, "javascript_fundamentals", "completed", p_know=0.78)

    nodes = _nodes_by_id(client.get("/api/topics/graph", headers=headers))

    assert (nodes["html_basics"]["status"], nodes["html_basics"]["mastery"]) == ("completed", 95.0)
    assert nodes["html_basics"]["mastered"] is True
    assert (nodes["css_basics"]["status"], nodes["css_basics"]["mastery"]) == ("in_progress", 43.2)
    assert nodes["css_basics"]["mastered"] is False
    # Completed but below 0.95: completed, not mastered (PRD 6.1).
    assert nodes["javascript_fundamentals"]["status"] == "completed"
    assert nodes["javascript_fundamentals"]["mastered"] is False


def test_topics_without_rows_unlock_once_prerequisites_are_completed(client, make_user, db):
    user_id, headers = make_user()
    _add_progress(db, user_id, "html_basics", "completed", p_know=0.95)

    nodes = _nodes_by_id(client.get("/api/topics/graph", headers=headers))

    assert nodes["semantic_html"]["status"] == "unlocked"   # only needs html_basics
    assert nodes["css_basics"]["status"] == "unlocked"       # only needs html_basics
    assert nodes["react_fundamentals"]["status"] == "locked"  # still needs JS + CSS


def test_progress_is_scoped_to_the_current_user(client, make_user, db):
    alice_id, _ = make_user("alice@example.com")
    _, bob_headers = make_user("bob@example.com")
    _add_progress(db, alice_id, "html_basics", "completed", p_know=0.95)

    nodes = _nodes_by_id(client.get("/api/topics/graph", headers=bob_headers))

    assert nodes["html_basics"]["status"] == "unlocked"
    assert nodes["html_basics"]["mastery"] == 10.0


def test_neo4j_outage_returns_503(client, make_user, monkeypatch):
    _, headers = make_user()

    def down(*args, **kwargs):
        raise ServiceUnavailable("Neo4j is down")

    monkeypatch.setattr(topic_service.neo4j_db, "read", down)
    response = client.get("/api/topics/graph", headers=headers)
    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]


# --- Resource parsing -----------------------------------------------------------

def test_parse_resources_handles_json_string():
    raw = '[{"title": "MDN", "url": "https://developer.mozilla.org", "type": "docs"}]'
    assert parse_resources(raw) == [{"title": "MDN", "url": "https://developer.mozilla.org", "type": "docs"}]


@pytest.mark.parametrize("raw", [None, "", "not json", '[{"title": "missing url"}]', "42"])
def test_parse_resources_degrades_to_empty_list(raw):
    assert parse_resources(raw) == []