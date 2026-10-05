"""GET /api/topics/learning-path tests (ARCHITECTURE.md section 23, "Learning path")."""

import pytest
from sqlalchemy import delete, select

from models import TopicProgress
from seed.curriculum import TOPICS

pytestmark = pytest.mark.usefixtures("curriculum")

ALL_IDS = {t.id for t in TOPICS}
# Everything that (directly or indirectly) depends on SQL Basics.
SQL_DEPENDENTS = {"sql_basics", "postgresql_basics", "testing_basics", "deployment_basics"}


def learning_path(client, headers, **params):
    return client.get("/api/topics/learning-path", headers=headers, params=params)


def onboard(client, headers, topic_ids):
    response = client.post("/api/topics/mark-known", json={"topic_ids": sorted(topic_ids)}, headers=headers)
    assert response.status_code == 200, response.text


def rows_for(db, user_id) -> dict[str, TopicProgress]:
    db.expire_all()
    return {r.topic_id: r for r in db.scalars(select(TopicProgress).where(TopicProgress.user_id == user_id))}


def set_row(db, user_id, topic_id, **fields):
    row = rows_for(db, user_id)[topic_id]
    for key, value in fields.items():
        setattr(row, key, value)
    db.commit()


def ids_of(body) -> list[str]:
    return [t["id"] for t in body["recommended"]]


def ids(response) -> list[str]:
    return ids_of(response.json())


# --- Access ---------------------------------------------------------------------

def test_requires_authentication(client):
    assert client.get("/api/topics/learning-path").status_code == 401


def test_unknown_domain_returns_404(client, make_user):
    _, headers = make_user()
    assert learning_path(client, headers, domain="astrology").status_code == 404


# --- Before onboarding ------------------------------------------------------------

def test_before_onboarding_returns_starting_topics_without_writing(client, make_user, db):
    user_id, headers = make_user()
    response = learning_path(client, headers)

    assert response.status_code == 200
    body = response.json()
    assert body["onboarded"] is False
    assert body["curriculum_complete"] is False
    assert ids(response) == ["git_basics", "html_basics", "javascript_fundamentals"]
    assert all(t["status"] == "unlocked" and t["mastery"] == 10.0 for t in body["recommended"])
    assert rows_for(db, user_id) == {}  # a GET never creates progress before onboarding


# --- Roadmap Phase 8 tests ---------------------------------------------------------

def test_topic_with_unmet_prerequisite_is_excluded(client, make_user):
    _, headers = make_user()
    onboard(client, headers, ALL_IDS - SQL_DEPENDENTS)

    response = learning_path(client, headers)

    # PostgreSQL Basics is not completed but still needs SQL Basics, so only SQL Basics is learnable.
    assert ids(response) == ["sql_basics"]


def test_topic_with_all_prerequisites_completed_is_included_and_unlocked(client, make_user, db):
    user_id, headers = make_user()
    onboard(client, headers, ALL_IDS - SQL_DEPENDENTS)
    assert rows_for(db, user_id)["postgresql_basics"].status == "locked"

    # SQL Basics gets completed outside onboarding (as a passed quiz will do in Phase 11).
    set_row(db, user_id, "sql_basics", status="completed", p_know=0.9)
    response = learning_path(client, headers)

    assert ids(response) == ["postgresql_basics"]
    pg = response.json()["recommended"][0]
    assert pg["prerequisites"] == ["rest_api_design", "sql_basics"]
    assert pg["prerequisite_names"] == ["REST API Design", "SQL Basics"]
    # "Sync newly unlocked statuses": the stored row was unlocked by the GET.
    assert rows_for(db, user_id)["postgresql_basics"].status == "unlocked"


def test_completed_topics_are_excluded(client, make_user):
    _, headers = make_user()
    onboard(client, headers, {"html_basics", "git_basics"})

    recommended = ids(learning_path(client, headers))

    assert "html_basics" not in recommended
    assert "git_basics" not in recommended
    assert recommended == ["css_basics", "javascript_fundamentals", "semantic_html"]


def test_at_most_three_topics_returned(client, make_user):
    _, headers = make_user()
    onboard(client, headers, [])  # 4 roots are learnable
    assert len(ids(learning_path(client, headers))) == 3

    onboard(client, headers, {"html_basics", "javascript_fundamentals", "git_basics", "sql_basics"})
    assert len(ids(learning_path(client, headers))) == 3  # many more are learnable now


def test_ordered_by_difficulty_then_name(client, make_user):
    _, headers = make_user()
    onboard(client, headers, {"html_basics", "javascript_fundamentals", "git_basics", "sql_basics"})

    recommended = learning_path(client, headers).json()["recommended"]

    keys = [(t["difficulty"], t["name"]) for t in recommended]
    assert keys == sorted(keys)
    assert [t["id"] for t in recommended] == ["css_basics", "semantic_html", "arrays_objects"]


# --- Statuses ---------------------------------------------------------------------

def test_in_progress_topic_is_recommended_as_in_progress(client, make_user, db):
    user_id, headers = make_user()
    onboard(client, headers, [])
    set_row(db, user_id, "html_basics", status="in_progress", p_know=0.42)

    recommended = {t["id"]: t for t in learning_path(client, headers).json()["recommended"]}

    assert recommended["html_basics"]["status"] == "in_progress"
    assert recommended["html_basics"]["mastery"] == 42.0
    assert rows_for(db, user_id)["html_basics"].status == "in_progress"  # sync left it alone


def test_sync_never_relocks_completed_or_in_progress_topics(client, make_user, db):
    user_id, headers = make_user()
    onboard(client, headers, {"html_basics"})
    # CSS started; Flexbox completed even though CSS isn't (e.g. a passed quiz) - neither may be reset.
    set_row(db, user_id, "css_basics", status="in_progress")
    set_row(db, user_id, "flexbox", status="completed", p_know=0.97)

    learning_path(client, headers)

    rows = rows_for(db, user_id)
    assert rows["css_basics"].status == "in_progress"
    assert (rows["flexbox"].status, rows["flexbox"].p_know) == ("completed", 0.97)


def test_stale_locked_row_is_repaired(client, make_user, db):
    user_id, headers = make_user()
    onboard(client, headers, {"html_basics"})
    set_row(db, user_id, "semantic_html", status="locked")  # wrong: its only prerequisite is done
    set_row(db, user_id, "react_fundamentals", status="unlocked")  # wrong: needs CSS and JS

    learning_path(client, headers)

    rows = rows_for(db, user_id)
    assert rows["semantic_html"].status == "unlocked"
    assert rows["react_fundamentals"].status == "locked"


def test_missing_row_for_learnable_topic_is_recreated(client, make_user, db):
    user_id, headers = make_user()
    onboard(client, headers, [])
    db.execute(delete(TopicProgress).where(TopicProgress.user_id == user_id, TopicProgress.topic_id == "git_basics"))
    db.commit()

    learning_path(client, headers)

    row = rows_for(db, user_id).get("git_basics")
    assert row is not None
    assert (row.status, row.p_know) == ("unlocked", 0.10)


# --- Completion and determinism ----------------------------------------------------

def test_curriculum_complete(client, make_user):
    _, headers = make_user()
    onboard(client, headers, ALL_IDS)

    body = learning_path(client, headers).json()

    assert body["onboarded"] is True
    assert body["curriculum_complete"] is True
    assert body["recommended"] == []


def test_not_complete_while_any_topic_remains(client, make_user):
    _, headers = make_user()
    onboard(client, headers, ALL_IDS - {"deployment_basics"})

    body = learning_path(client, headers).json()

    assert body["curriculum_complete"] is False
    assert ids_of(body) == ["deployment_basics"]


def test_stable_and_deterministic_for_the_same_state(client, make_user):
    """Phase 8 exit gate."""
    _, alice = make_user("alice@example.com")
    _, bob = make_user("bob@example.com")
    known = {"html_basics", "css_basics", "javascript_fundamentals", "functions_scope"}
    onboard(client, alice, known)
    onboard(client, bob, known)

    alice_runs = [learning_path(client, alice).json() for _ in range(5)]
    bob_body = learning_path(client, bob).json()

    assert all(run == alice_runs[0] for run in alice_runs)
    assert alice_runs[0] == bob_body
    for topic in alice_runs[0]["recommended"]:
        assert topic["id"] not in known
        assert set(topic["prerequisites"]) <= known


def test_matches_onboarding_recommendations(client, make_user):
    _, headers = make_user()
    onboarding = client.post(
        "/api/topics/mark-known", json={"topic_ids": ["react_hooks"]}, headers=headers
    ).json()["recommended"]
    assert learning_path(client, headers).json()["recommended"] == onboarding


def test_scoped_to_current_user(client, make_user):
    _, alice = make_user("alice@example.com")
    _, bob = make_user("bob@example.com")
    onboard(client, alice, ALL_IDS)

    bob_body = learning_path(client, bob).json()

    assert bob_body["onboarded"] is False
    assert ids_of(bob_body) == ["git_basics", "html_basics", "javascript_fundamentals"]
