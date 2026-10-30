"""Multiple domains sharing one pool of topics (Phase 22), through the real API.

Two test domains are seeded into their own catalog alongside the real curriculum:

    pytest-x:  x1 -> x2
    pytest-y:  y1 -> y2, where y1 also needs x2 from pytest-x; pytest-y shares x1

The real curriculum has no prerequisite crossing into another domain's view yet, so these
domains exercise that path. They are registered as supported only inside these tests.
"""

import pytest
from sqlalchemy import select

from db import neo4j_db
from models import TopicProgress
from seed.curriculum import DOMAIN_BY_ID, Domain, Resource, Topic
from seed.seed_graph import seed_curriculum
from services import topic_service

CATALOG = "pytest-domains"
RES = (Resource("Docs", "https://example.com/docs", "docs"),)
X1 = Topic("pytestd_x1", "X One", "First topic of X", 1, RES)
X2 = Topic("pytestd_x2", "X Two", "Second topic of X", 2, RES)
Y1 = Topic("pytestd_y1", "Y One", "First topic of Y", 1, RES)
Y2 = Topic("pytestd_y2", "Y Two", "Second topic of Y", 2, RES)
X = Domain("pytest-x", "Pytest X", "Test domain X", (X1, X2), ((X1.id, X2.id),))
Y = Domain("pytest-y", "Pytest Y", "Test domain Y", (Y1, Y2), ((X2.id, Y1.id), (Y1.id, Y2.id)), shared=(X1.id,))


def _cleanup() -> None:
    neo4j_db.write("MATCH (n {catalog: $c}) DETACH DELETE n", c=CATALOG)


@pytest.fixture()
def seeded(curriculum):
    _cleanup()
    seed_curriculum((X, Y), CATALOG)
    yield
    _cleanup()


@pytest.fixture()
def supported(seeded, monkeypatch):
    monkeypatch.setattr(topic_service, "SUPPORTED_DOMAINS", (*topic_service.SUPPORTED_DOMAINS, X.id, Y.id))
    monkeypatch.setattr(topic_service, "DOMAIN_BY_ID", {**DOMAIN_BY_ID, X.id: X, Y.id: Y})


def mark_known(client, headers, domain, topic_ids):
    response = client.post("/api/topics/mark-known", json={"domain": domain, "topic_ids": topic_ids}, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def graph(client, headers, domain):
    response = client.get("/api/topics/graph", headers=headers, params={"domain": domain})
    assert response.status_code == 200, response.text
    return response.json()


def nodes(client, headers, domain):
    return {n["id"]: n for n in graph(client, headers, domain)["nodes"]}


def path(client, headers, domain):
    response = client.get("/api/topics/learning-path", headers=headers, params={"domain": domain})
    assert response.status_code == 200, response.text
    return response.json()


def status_of(db, user_id, topic_id):
    db.expire_all()
    row = db.scalar(select(TopicProgress).where(TopicProgress.user_id == user_id, TopicProgress.topic_id == topic_id))
    return row.status if row is not None else None


# --- Reading a domain -------------------------------------------------------------------

@pytest.mark.usefixtures("supported")
def test_graph_includes_shared_topics_and_lists_prerequisites_from_other_domains(client, make_user):
    _, headers = make_user()
    body = graph(client, headers, Y.id)
    by_id = {n["id"]: n for n in body["nodes"]}

    assert set(by_id) == {X1.id, Y1.id, Y2.id}
    # Only links between this domain's topics are drawn; x2 isn't a node here.
    assert {(link["source"], link["target"]) for link in body["links"]} == {(Y1.id, Y2.id)}
    assert by_id[Y1.id]["prerequisites"] == []
    assert by_id[Y1.id]["external_prerequisites"] == [
        {"id": X2.id, "name": "X Two", "domain": X.id, "domain_name": "Pytest X"}
    ]
    assert by_id[Y2.id]["prerequisites"] == [Y1.id]
    assert by_id[X1.id]["domains"] == [X.id, Y.id]
    # A new learner: x1 is open; y1 waits for x2 although nothing in this domain comes before it.
    assert (by_id[X1.id]["status"], by_id[Y1.id]["status"]) == ("unlocked", "locked")


@pytest.mark.usefixtures("supported")
def test_topic_list_of_a_domain_includes_its_shared_topics(client, make_user):
    _, headers = make_user()
    body = client.get("/api/topics/all", headers=headers, params={"domain": Y.id}).json()
    assert [t["id"] for t in body["topics"]] == [X1.id, Y1.id, Y2.id]


@pytest.mark.usefixtures("seeded")
def test_domains_are_invisible_until_supported(client, make_user):
    _, headers = make_user()
    assert client.get("/api/topics/graph", headers=headers, params={"domain": Y.id}).status_code == 404
    assert client.get(f"/api/quiz/generate/{X1.id}", headers=headers).status_code == 404
    real = {n["id"] for n in graph(client, headers, "web-development")["nodes"]}
    assert not any(topic_id.startswith("pytestd_") for topic_id in real)


# --- Status across domains --------------------------------------------------------------

@pytest.mark.usefixtures("supported")
def test_a_prerequisite_in_another_domain_keeps_a_topic_locked(client, make_user, db):
    user_id, headers = make_user()
    mark_known(client, headers, Y.id, [])

    assert [t["id"] for t in path(client, headers, Y.id)["recommended"]] == [X1.id]
    assert status_of(db, user_id, Y1.id) == "locked"


@pytest.mark.usefixtures("supported")
def test_completing_a_prerequisite_in_its_own_domain_unlocks_the_dependent(client, make_user, db):
    user_id, headers = make_user()
    body = mark_known(client, headers, X.id, [X2.id])

    assert body["added_prerequisites"] == [X1.id]
    assert [t["id"] for t in path(client, headers, Y.id)["recommended"]] == [Y1.id]
    assert status_of(db, user_id, Y1.id) == "unlocked"


@pytest.mark.usefixtures("supported")
def test_viewing_one_domain_never_locks_topics_of_another(client, make_user, db):
    user_id, headers = make_user()
    mark_known(client, headers, X.id, [X2.id])
    assert status_of(db, user_id, Y1.id) == "unlocked"

    # Every read that syncs statuses, from the point of view of other domains.
    path(client, headers, X.id)
    path(client, headers, "web-development")
    assert client.get("/api/progress/dashboard", headers=headers, params={"domain": "foundations"}).status_code == 200
    mark_known(client, headers, "web-development", ["html_basics"])

    assert status_of(db, user_id, Y1.id) == "unlocked"
    assert nodes(client, headers, Y.id)[Y1.id]["status"] == "unlocked"


@pytest.mark.usefixtures("supported")
def test_known_topic_brings_its_prerequisites_from_other_domains(client, make_user, db):
    user_id, headers = make_user()
    body = mark_known(client, headers, Y.id, [Y2.id])

    assert body["added_prerequisites"] == [X1.id, X2.id, Y1.id]
    assert body["known_count"] == 4
    assert all(status_of(db, user_id, t) == "completed" for t in (X1.id, X2.id, Y1.id, Y2.id))


@pytest.mark.usefixtures("supported")
def test_marking_a_topic_from_another_domain_is_rejected(client, make_user):
    _, headers = make_user()
    response = client.post("/api/topics/mark-known", json={"domain": X.id, "topic_ids": [Y1.id]}, headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": f"Unknown topic ids: {Y1.id}"}


# --- Completing a domain ----------------------------------------------------------------

@pytest.mark.usefixtures("supported")
def test_domain_is_not_complete_while_a_topic_waits_on_another_domain(client, make_user):
    _, headers = make_user()
    mark_known(client, headers, Y.id, [X1.id])

    # Nothing in Y is learnable (y1 needs x2), but Y isn't finished.
    body = path(client, headers, Y.id)
    assert body["recommended"] == []
    assert body["curriculum_complete"] is False
    dashboard = client.get("/api/progress/dashboard", headers=headers, params={"domain": Y.id}).json()
    assert dashboard["curriculum_complete"] is False


@pytest.mark.usefixtures("supported")
def test_domain_is_complete_once_all_its_topics_are(client, make_user):
    _, headers = make_user()
    mark_known(client, headers, Y.id, [Y2.id])

    assert path(client, headers, Y.id)["curriculum_complete"] is True
    assert path(client, headers, X.id)["curriculum_complete"] is True  # x1 and x2 came along
    assert path(client, headers, "web-development")["curriculum_complete"] is False


# --- Quizzes ------------------------------------------------------------------------------

@pytest.mark.usefixtures("supported")
def test_mastery_is_shared_by_every_domain_using_a_topic(client, make_user, fake_llm, quiz_taker):
    _, headers = make_user()
    mark_known(client, headers, Y.id, [])
    result = quiz_taker(headers, X1.id, "CCC")

    assert result["passed"] is True
    in_x, in_y = nodes(client, headers, X.id)[X1.id], nodes(client, headers, Y.id)[X1.id]
    assert in_x["status"] == in_y["status"] == "completed"
    assert in_x["mastery"] == in_y["mastery"] == round(result["p_know_after"] * 100, 1)


@pytest.mark.usefixtures("supported")
def test_quiz_prompt_names_the_topics_home_domain(client, make_user, fake_llm, quiz_taker):
    _, headers = make_user()
    mark_known(client, headers, X.id, [X2.id])
    quiz_taker(headers, X1.id, "CCC")  # x1 lives in X (and is shared with Y)
    quiz_taker(headers, Y1.id, "CCC")

    prompts = [call["messages"][-1]["content"] for call in fake_llm.calls]
    assert "Domain: Pytest X" in prompts[0]
    assert "Domain: Pytest Y" in prompts[1]


@pytest.mark.usefixtures("supported")
def test_next_topics_stay_within_the_quizzed_topics_domains(client, make_user, fake_llm, quiz_taker):
    _, headers = make_user()
    mark_known(client, headers, Y.id, [])

    # x1 is in X and Y: next is x2 (X); y1 still waits. Real-domain topics never appear.
    first = quiz_taker(headers, X1.id, "CCC")
    assert [t["id"] for t in first["next_topics"]] == [X2.id]

    # x2 is only in X, which is now finished; y1 (in Y) is reported as newly unlocked instead.
    second = quiz_taker(headers, X2.id, "CCC")
    assert second["next_topics"] == []
    assert second["newly_unlocked"] == [Y1.id]


@pytest.mark.usefixtures("curriculum")
def test_topics_getting_their_first_row_are_not_reported_as_newly_unlocked(client, make_user, db, fake_llm, quiz_taker):
    # A learner who onboarded before Foundations existed has no rows for its starting topics.
    user_id, headers = make_user()
    mark_known(client, headers, "web-development", ["html_basics"])
    db.execute(TopicProgress.__table__.delete().where(
        TopicProgress.user_id == user_id, TopicProgress.topic_id.in_(["command_line_basics", "how_the_internet_works"])
    ))
    db.commit()

    result = quiz_taker(headers, "css_basics", "CCC")

    # The quiz unlocked what builds on CSS; the Foundations topics got rows but were already open.
    assert result["newly_unlocked"] == ["css_grid", "flexbox"]
    assert status_of(db, user_id, "command_line_basics") == "unlocked"
