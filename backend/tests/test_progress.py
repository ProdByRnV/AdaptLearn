"""Dashboard (GET /api/progress/dashboard) and raw progress (GET /api/progress/all) tests.

Quizzes are taken through the real API with the LLM faked (conftest.fake_llm), so every
number on the dashboard comes from genuinely persisted state.
"""

import pytest
from sqlalchemy import select

from db import neo4j_db
from models import QuizSession
from seed.curriculum import TOPICS

pytestmark = pytest.mark.usefixtures("curriculum", "fake_llm")

ALL_IDS = {t.id for t in TOPICS}
TOPIC_BY_ID = {t.id: t for t in TOPICS}
ROOTS = {"html_basics", "javascript_fundamentals", "git_basics", "sql_basics"}


# --- Helpers ------------------------------------------------------------------------

def dashboard(client, headers, **params):
    response = client.get("/api/progress/dashboard", headers=headers, params=params)
    assert response.status_code == 200, response.text
    return response.json()


def onboard(client, headers, topic_ids=()):
    response = client.post("/api/topics/mark-known", json={"topic_ids": sorted(topic_ids)}, headers=headers)
    assert response.status_code == 200, response.text


def take_quiz(client, headers, db, topic_id, pattern):
    """Generate a quiz and answer it following a pattern such as CCW (correct, correct, wrong)."""
    quiz_id = client.get(f"/api/quiz/generate/{topic_id}", headers=headers).json()["quiz_id"]
    db.expire_all()
    key = [q["correct"] for q in db.get(QuizSession, quiz_id).questions]
    answers = [k if p == "C" else (k + 1) % 4 for k, p in zip(key, pattern)]
    response = client.post("/api/quiz/submit", json={"quiz_id": quiz_id, "answers": answers}, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


# --- Access -------------------------------------------------------------------------

@pytest.mark.parametrize("path", ["/api/progress/dashboard", "/api/progress/all"])
def test_requires_authentication(client, path):
    assert client.get(path).status_code == 401


def test_unknown_domain_returns_404(client, make_user):
    _, headers = make_user()
    response = client.get("/api/progress/dashboard", params={"domain": "knitting"}, headers=headers)
    assert response.status_code == 404


# --- Dashboard shape and empty states ----------------------------------------------------

def test_dashboard_shape_matches_spec(client, make_user):
    _, headers = make_user()
    body = dashboard(client, headers)

    # ARCHITECTURE 13.10 keys, plus domain/onboarded/curriculum_complete.
    assert set(body) == {
        "domain", "onboarded", "curriculum_complete", "stats", "recommended", "needs_attention",
        "recent_attempts", "mastery",
    }
    assert {"total_topics", "completed_topics", "mastered_topics", "average_mastery", "total_attempts"} <= set(
        body["stats"]
    )


def test_dashboard_before_onboarding(client, make_user):
    _, headers = make_user()
    body = dashboard(client, headers)

    assert body["onboarded"] is False
    assert body["stats"] == {
        "total_topics": 30, "completed_topics": 0, "in_progress_topics": 0, "mastered_topics": 0,
        "average_mastery": 0.0, "total_attempts": 0, "progress_percent": 0.0,
    }
    assert [t["id"] for t in body["recommended"]] == ["git_basics", "html_basics", "javascript_fundamentals"]
    assert body["needs_attention"] == [] and body["recent_attempts"] == []
    assert len(body["mastery"]) == 30
    assert {m["id"] for m in body["mastery"] if m["status"] == "unlocked"} == ROOTS


def test_dashboard_after_onboarding(client, make_user):
    _, headers = make_user()
    onboard(client, headers, {"html_basics", "css_basics"})

    stats = dashboard(client, headers)["stats"]

    assert stats["completed_topics"] == 2
    assert stats["mastered_topics"] == 2  # known topics start at 0.95
    assert stats["average_mastery"] == round((2 * 95 + 28 * 10) / 30, 1)  # 15.7
    assert stats["progress_percent"] == round(2 / 30 * 100, 1)  # 6.7
    assert stats["total_attempts"] == 0


# --- Stats from real quiz activity ---------------------------------------------------------

def test_stats_reflect_quiz_activity(client, make_user, db):
    _, headers = make_user()
    onboard(client, headers)
    html = take_quiz(client, headers, db, "html_basics", "CCC")   # pass, mastered (0.989)
    git = take_quiz(client, headers, db, "git_basics", "CCW")     # pass, not mastered (0.759)
    js = take_quiz(client, headers, db, "javascript_fundamentals", "CWW")  # fail -> in progress (0.465)

    stats = dashboard(client, headers)["stats"]

    assert stats["completed_topics"] == 2
    assert stats["in_progress_topics"] == 1
    assert stats["mastered_topics"] == 1
    assert stats["total_attempts"] == 3
    expected_average = (html["p_know_after"] + git["p_know_after"] + js["p_know_after"] + 27 * 0.10) / 30 * 100
    assert stats["average_mastery"] == round(expected_average, 1)
    assert stats["progress_percent"] == round(2 / 30 * 100, 1)


def test_recommended_matches_learning_path(client, make_user, db):
    _, headers = make_user()
    onboard(client, headers)
    take_quiz(client, headers, db, "html_basics", "CCC")

    body = dashboard(client, headers)
    path = client.get("/api/topics/learning-path", headers=headers).json()

    assert body["recommended"] == path["recommended"]
    assert [t["id"] for t in body["recommended"]] == ["css_basics", "git_basics", "javascript_fundamentals"]
    for card in body["recommended"]:
        assert card["status"] != "locked"
        assert {"name", "description", "difficulty", "status", "mastery", "prerequisite_names"} <= set(card)


def test_recent_attempts_newest_first_and_limited_to_five(client, make_user, db):
    _, headers = make_user()
    onboard(client, headers)
    patterns = ["WWW", "CWW", "CCW", "WCC", "CWC", "CCC"]
    for pattern in patterns:
        take_quiz(client, headers, db, "html_basics", pattern)

    recent = dashboard(client, headers)["recent_attempts"]

    assert len(recent) == 5
    assert [a["score"] for a in recent] == [p.count("C") for p in reversed(patterns)][:5]
    ids = [a["id"] for a in recent]
    assert ids == sorted(ids, reverse=True)
    newest = recent[0]
    assert newest["topic_id"] == "html_basics" and newest["topic_name"] == "HTML Basics"
    assert (newest["score"], newest["total"], newest["passed"]) == (3, 3, True)
    assert newest["created_at"]
    # Same topic each time, so each attempt starts where the previous one ended.
    for later, earlier in zip(recent, recent[1:]):
        assert later["mastery_before"] == earlier["mastery_after"]


def test_needs_attention_lists_topic_with_resources_then_clears(client, make_user, db):
    _, headers = make_user()
    onboard(client, headers)
    for _ in range(3):
        take_quiz(client, headers, db, "html_basics", "WWW")

    attention = dashboard(client, headers)["needs_attention"]

    assert [t["id"] for t in attention] == ["html_basics"]
    item = attention[0]
    assert item["name"] == "HTML Basics" and item["attempts"] == 3 and item["mastery"] < 50
    expected = [{"title": r.title, "url": r.url, "type": r.type} for r in TOPIC_BY_ID["html_basics"].resources]
    assert item["resources"] == expected

    take_quiz(client, headers, db, "html_basics", "CCC")
    assert dashboard(client, headers)["needs_attention"] == []


def test_mastery_list_covers_every_topic_with_names(client, make_user, db):
    _, headers = make_user()
    onboard(client, headers)
    take_quiz(client, headers, db, "html_basics", "CCC")

    mastery = dashboard(client, headers)["mastery"]

    assert {m["id"] for m in mastery} == ALL_IDS
    assert all(m["name"] == TOPIC_BY_ID[m["id"]].name for m in mastery)
    keys = [(m["difficulty"], m["name"]) for m in mastery]
    assert keys == sorted(keys)
    html = next(m for m in mastery if m["id"] == "html_basics")
    assert (html["status"], html["mastered"], html["mastery"]) == ("completed", True, 98.9)


def test_curriculum_complete(client, make_user):
    _, headers = make_user()
    onboard(client, headers, ALL_IDS)

    body = dashboard(client, headers)

    assert body["curriculum_complete"] is True
    assert body["recommended"] == []
    assert body["stats"]["completed_topics"] == 30 and body["stats"]["progress_percent"] == 100.0


def test_dashboard_is_scoped_to_the_current_user(client, make_user, db):
    _, alice = make_user("alice@example.com")
    _, bob = make_user("bob@example.com")
    onboard(client, alice)
    for _ in range(3):
        take_quiz(client, alice, db, "html_basics", "WWW")

    body = dashboard(client, bob)

    assert body["stats"]["total_attempts"] == 0
    assert body["recent_attempts"] == [] and body["needs_attention"] == []


def test_dashboard_uses_two_neo4j_queries_regardless_of_activity(client, make_user, db, monkeypatch):
    """ARCHITECTURE 16: no N+1 lookups - topic metadata is fetched once and joined in memory."""
    _, headers = make_user()
    onboard(client, headers)
    for topic_id in ("html_basics", "git_basics", "sql_basics"):
        for _ in range(3):
            take_quiz(client, headers, db, topic_id, "WWW")  # 9 attempts, 3 topics needing attention

    real_read, calls = neo4j_db.read, []

    def counting_read(*args, **kwargs):
        calls.append(args[0])
        return real_read(*args, **kwargs)

    monkeypatch.setattr(neo4j_db, "read", counting_read)
    body = dashboard(client, headers)

    assert len(body["needs_attention"]) == 3 and body["stats"]["total_attempts"] == 9
    assert len(calls) == 2


# --- GET /api/progress/all -----------------------------------------------------------------

def test_progress_all_empty_before_onboarding(client, make_user):
    _, headers = make_user()
    assert client.get("/api/progress/all", headers=headers).json() == {"topics": []}


def test_progress_all_matches_spec_shape_and_values(client, make_user, db):
    _, headers = make_user()
    onboard(client, headers, {"html_basics"})
    take_quiz(client, headers, db, "git_basics", "CCW")

    topics = client.get("/api/progress/all", headers=headers).json()["topics"]

    assert len(topics) == 30
    assert [t["topic_id"] for t in topics] == sorted(ALL_IDS)
    for item in topics:
        assert set(item) == {"topic_id", "status", "p_know", "attempts", "correct", "needs_attention"}
    by_id = {t["topic_id"]: t for t in topics}
    assert by_id["html_basics"] == {
        "topic_id": "html_basics", "status": "completed", "p_know": 0.95, "attempts": 0, "correct": 0,
        "needs_attention": False,
    }
    git = by_id["git_basics"]
    assert (git["status"], git["attempts"], git["correct"]) == ("completed", 1, 2)
    assert git["p_know"] == pytest.approx(0.7589958159, abs=1e-9)


def test_progress_all_is_scoped_to_the_current_user(client, make_user):
    _, alice = make_user("alice@example.com")
    _, bob = make_user("bob@example.com")
    onboard(client, alice)
    assert client.get("/api/progress/all", headers=bob).json() == {"topics": []}
