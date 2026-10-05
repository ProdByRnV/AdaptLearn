"""Onboarding (POST /api/topics/mark-known) and learning-path frontier tests.

Expected results are computed here in plain Python from seed/curriculum.py and compared
with what the Neo4j queries return, so the Cypher is checked against an independent model.
"""

import pytest
from sqlalchemy import select

from models import TopicProgress
from seed.curriculum import DOMAIN, PREREQUISITES, TOPICS
from services.learning_path import get_ancestors, get_frontier

pytestmark = pytest.mark.usefixtures("curriculum")

ALL_IDS = {t.id for t in TOPICS}
ROOTS = {"html_basics", "javascript_fundamentals", "git_basics", "sql_basics"}
NAMES = {t.id: t.name for t in TOPICS}


# --- Independent reference model -------------------------------------------------

def expected_ancestors(ids: set[str]) -> set[str]:
    parents: dict[str, set[str]] = {}
    for source, target in PREREQUISITES:
        parents.setdefault(target, set()).add(source)
    found, stack = set(), list(ids)
    while stack:
        for parent in parents.get(stack.pop(), ()):
            if parent not in found:
                found.add(parent)
                stack.append(parent)
    return found


def expected_frontier(completed: set[str]) -> list[str]:
    parents = {t.id: {s for s, d in PREREQUISITES if d == t.id} for t in TOPICS}
    eligible = [t for t in TOPICS if t.id not in completed and parents[t.id] <= completed]
    return [t.id for t in sorted(eligible, key=lambda t: (t.difficulty, t.name))]


# --- Helpers ----------------------------------------------------------------------

def mark_known(client, headers, topic_ids, domain=None):
    body = {"topic_ids": topic_ids}
    if domain is not None:
        body["domain"] = domain
    return client.post("/api/topics/mark-known", json=body, headers=headers)


def rows_for(db, user_id) -> dict[str, TopicProgress]:
    db.expire_all()
    return {r.topic_id: r for r in db.scalars(select(TopicProgress).where(TopicProgress.user_id == user_id))}


def ids_with_status(rows, status) -> set[str]:
    return {tid for tid, r in rows.items() if r.status == status}


# --- Neo4j queries vs the reference model ---------------------------------------

@pytest.mark.parametrize(
    "selected",
    [set(), {"html_basics"}, {"react_fundamentals"}, {"deployment_basics"}, {"postgresql_basics", "es_modules"}],
)
def test_ancestor_query_matches_reference(selected):
    assert get_ancestors(DOMAIN, selected) == expected_ancestors(selected)


@pytest.mark.parametrize(
    "completed",
    [
        set(),
        {"html_basics", "css_basics"},
        {"javascript_fundamentals", "functions_scope"},
        {"git_basics", "javascript_fundamentals", "nodejs_basics"},
        ALL_IDS - {"deployment_basics"},
        ALL_IDS,
    ],
)
def test_frontier_query_matches_reference(completed):
    assert [t.id for t in get_frontier(DOMAIN, completed)] == expected_frontier(completed)


# --- POST /api/topics/mark-known --------------------------------------------------

def test_requires_authentication(client):
    assert mark_known(client, {}, []).status_code == 401


def test_no_known_topics(client, make_user, db):
    user_id, headers = make_user()
    response = mark_known(client, headers, [])

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Onboarding saved"
    assert body["known_count"] == 0
    assert body["added_prerequisites"] == []
    assert [t["id"] for t in body["recommended"]] == ["git_basics", "html_basics", "javascript_fundamentals"]

    rows = rows_for(db, user_id)
    assert set(rows) == ALL_IDS
    assert ids_with_status(rows, "unlocked") == ROOTS
    assert ids_with_status(rows, "locked") == ALL_IDS - ROOTS
    assert {r.p_know for r in rows.values()} == {0.10}


def test_recommended_items_have_card_fields(client, make_user):
    _, headers = make_user()
    recommended = mark_known(client, headers, ["html_basics"]).json()["recommended"]
    # Four difficulty-1 topics are now open; alphabetically CSS, Git, JavaScript make the top 3.
    assert [t["id"] for t in recommended] == ["css_basics", "git_basics", "javascript_fundamentals"]
    css = recommended[0]
    assert css == {
        "id": "css_basics",
        "name": "CSS Basics",
        "description": css["description"],
        "difficulty": 1,
        "status": "unlocked",
        "mastery": 10.0,
        "prerequisites": ["html_basics"],
        "prerequisite_names": ["HTML Basics"],
    }
    assert css["description"]


def test_some_known_topics(client, make_user, db):
    user_id, headers = make_user()
    body = mark_known(client, headers, ["html_basics", "css_basics"]).json()

    assert body["known_count"] == 2
    assert body["added_prerequisites"] == []
    rows = rows_for(db, user_id)
    completed = {"html_basics", "css_basics"}
    assert ids_with_status(rows, "completed") == completed
    assert all(rows[t].p_know == 0.95 for t in completed)
    assert ids_with_status(rows, "unlocked") == set(expected_frontier(completed))
    assert "react_fundamentals" in ids_with_status(rows, "locked")  # still needs JavaScript
    assert [t["id"] for t in body["recommended"]] == expected_frontier(completed)[:3]


def test_known_topic_implies_its_prerequisites(client, make_user, db):
    user_id, headers = make_user()
    body = mark_known(client, headers, ["react_fundamentals"]).json()

    assert body["added_prerequisites"] == ["css_basics", "html_basics", "javascript_fundamentals"]
    assert body["known_count"] == 4
    rows = rows_for(db, user_id)
    assert ids_with_status(rows, "completed") == {"react_fundamentals", "css_basics", "html_basics", "javascript_fundamentals"}
    assert rows["props_state"].status == "unlocked"


def test_deep_topic_completes_its_whole_prerequisite_chain(client, make_user, db):
    user_id, headers = make_user()
    body = mark_known(client, headers, ["deployment_basics"]).json()

    completed = {"deployment_basics"} | expected_ancestors({"deployment_basics"})
    assert body["known_count"] == len(completed)
    rows = rows_for(db, user_id)
    assert ids_with_status(rows, "completed") == completed
    assert ids_with_status(rows, "unlocked") == set(expected_frontier(completed))


def test_all_topics_known(client, make_user, db):
    user_id, headers = make_user()
    body = mark_known(client, headers, sorted(ALL_IDS)).json()

    assert body["known_count"] == 30
    assert body["recommended"] == []
    rows = rows_for(db, user_id)
    assert ids_with_status(rows, "completed") == ALL_IDS
    assert all(r.p_know == 0.95 for r in rows.values())


def test_invalid_topic_ids_rejected_without_writing_anything(client, make_user, db):
    user_id, headers = make_user()
    response = mark_known(client, headers, ["html_basics", "zzz_unknown", "nope"])

    assert response.status_code == 400
    assert response.json() == {"detail": "Unknown topic ids: nope, zzz_unknown"}
    assert rows_for(db, user_id) == {}


def test_unknown_domain_rejected(client, make_user):
    _, headers = make_user()
    response = mark_known(client, headers, [], domain="cooking")
    assert response.status_code == 404


def test_duplicate_ids_are_counted_once(client, make_user):
    _, headers = make_user()
    assert mark_known(client, headers, ["html_basics", "html_basics"]).json()["known_count"] == 1


def test_empty_body_is_allowed(client, make_user):
    _, headers = make_user()
    response = client.post("/api/topics/mark-known", json={}, headers=headers)
    assert response.status_code == 200
    assert response.json()["known_count"] == 0


def test_too_many_ids_rejected(client, make_user):
    _, headers = make_user()
    response = mark_known(client, headers, [f"t{i}" for i in range(101)])
    assert response.status_code == 422


def test_different_selections_give_different_frontiers(client, make_user, db):
    """Phase 7 exit gate."""
    beginner_id, beginner = make_user("beginner@example.com")
    frontend_id, frontend = make_user("frontend@example.com")
    backend_id, backend = make_user("backend@example.com")

    starts = {
        "beginner": mark_known(client, beginner, []).json()["recommended"],
        "frontend": mark_known(client, frontend, ["react_hooks"]).json()["recommended"],
        "backend": mark_known(client, backend, ["express_basics", "sql_basics"]).json()["recommended"],
    }
    recommended_ids = {who: tuple(t["id"] for t in recs) for who, recs in starts.items()}
    assert len(set(recommended_ids.values())) == 3

    unlocked = {
        who: ids_with_status(rows_for(db, uid), "unlocked")
        for who, uid in (("beginner", beginner_id), ("frontend", frontend_id), ("backend", backend_id))
    }
    assert unlocked["beginner"] == ROOTS
    assert "react_router" in unlocked["frontend"]
    assert "rest_api_design" in unlocked["backend"]
    assert len({frozenset(s) for s in unlocked.values()}) == 3


def test_graph_reflects_onboarding(client, make_user):
    _, headers = make_user()
    mark_known(client, headers, ["html_basics"])
    nodes = {n["id"]: n for n in client.get("/api/topics/graph", headers=headers).json()["nodes"]}

    assert (nodes["html_basics"]["status"], nodes["html_basics"]["mastery"]) == ("completed", 95.0)
    assert nodes["html_basics"]["mastered"] is True
    assert nodes["css_basics"]["status"] == "unlocked"
    assert nodes["flexbox"]["status"] == "locked"


def test_repeat_onboarding_only_adds_knowledge(client, make_user, db):
    user_id, headers = make_user()
    mark_known(client, headers, ["html_basics"])

    # Simulate learning since onboarding: higher mastery on HTML, CSS started.
    rows = rows_for(db, user_id)
    rows["html_basics"].p_know = 0.99
    rows["css_basics"].status = "in_progress"
    rows["css_basics"].p_know = 0.5
    db.commit()

    mark_known(client, headers, [])
    rows = rows_for(db, user_id)
    assert (rows["html_basics"].status, rows["html_basics"].p_know) == ("completed", 0.99)
    assert (rows["css_basics"].status, rows["css_basics"].p_know) == ("in_progress", 0.5)

    mark_known(client, headers, ["css_basics"])
    rows = rows_for(db, user_id)
    assert (rows["css_basics"].status, rows["css_basics"].p_know) == ("completed", 0.95)
    assert rows["html_basics"].p_know == 0.99  # never lowered
    assert rows["flexbox"].status == "unlocked"
    assert len(rows) == 30


def test_marking_known_clears_needs_attention(client, make_user, db):
    user_id, headers = make_user()
    mark_known(client, headers, [])
    rows = rows_for(db, user_id)
    rows["git_basics"].needs_attention = True
    db.commit()

    mark_known(client, headers, ["git_basics"])
    assert rows_for(db, user_id)["git_basics"].needs_attention is False


def test_onboarding_one_user_never_touches_another(client, make_user, db):
    alice_id, alice = make_user("alice@example.com")
    _, bob = make_user("bob@example.com")
    mark_known(client, alice, ["html_basics"])
    before = {tid: (r.status, r.p_know) for tid, r in rows_for(db, alice_id).items()}

    mark_known(client, bob, sorted(ALL_IDS))

    after = {tid: (r.status, r.p_know) for tid, r in rows_for(db, alice_id).items()}
    assert after == before
