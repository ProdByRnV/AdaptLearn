"""Joining domains, per-domain onboarding, the domain catalogue and the home page (Phase 23).

Uses the real curriculum: Foundations (10 topics, five of them starting topics, including
git_basics), Web Development (30 topics, sharing git_basics) and Python (20 topics, one starting
topic). Cross-domain prerequisites are covered with the test domains in test_domains.py.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select, text

from db import neo4j_db
from db.postgres import init_db
from models import DomainEnrolment, TopicProgress, User

pytestmark = pytest.mark.usefixtures("curriculum")

WEB = "web-development"
FOUNDATIONS = "foundations"
PYTHON = "python"
# Every Foundations topic: onboarding with all of them completes the domain.
ALL_FOUNDATIONS = [
    "how_computers_work", "binary_data_representation", "data_formats", "programming_concepts",
    "algorithmic_thinking", "command_line_basics", "operating_system_basics", "git_basics",
    "how_the_internet_works", "security_basics",
]


def catalogue(client, headers):
    response = client.get("/api/domains", headers=headers)
    assert response.status_code == 200, response.text
    return {d["id"]: d for d in response.json()["domains"]}


def home(client, headers):
    response = client.get("/api/home", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def join(client, headers, domain):
    return client.post(f"/api/domains/{domain}/join", headers=headers)


def onboard(client, headers, domain, topic_ids=()):
    response = client.post(
        "/api/topics/mark-known", json={"domain": domain, "topic_ids": sorted(topic_ids)}, headers=headers
    )
    assert response.status_code == 200, response.text
    return response.json()


def learning_path(client, headers, domain):
    response = client.get("/api/topics/learning-path", headers=headers, params={"domain": domain})
    assert response.status_code == 200, response.text
    return response.json()


def dashboard(client, headers, domain):
    response = client.get("/api/progress/dashboard", headers=headers, params={"domain": domain})
    assert response.status_code == 200, response.text
    return response.json()


def progress_rows(db, user_id):
    db.expire_all()
    return {r.topic_id: (r.status, r.p_know) for r in db.scalars(select(TopicProgress).where(TopicProgress.user_id == user_id))}


def count_neo4j_reads(monkeypatch):
    real_read, calls = neo4j_db.read, []

    def counting_read(*args, **kwargs):
        calls.append(args[0])
        return real_read(*args, **kwargs)

    monkeypatch.setattr(neo4j_db, "read", counting_read)
    return calls


# --- Access ------------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("method", "url"), [("get", "/api/domains"), ("post", f"/api/domains/{WEB}/join"), ("get", "/api/home")]
)
def test_endpoints_require_authentication(client, method, url):
    response = getattr(client, method)(url)
    assert response.status_code == 401


# --- Catalogue ---------------------------------------------------------------------------

def test_catalogue_lists_every_domain_in_curriculum_order_with_its_size(client, make_user, db):
    user_id, headers = make_user()
    response = client.get("/api/domains", headers=headers)

    domains = response.json()["domains"]
    assert [d["id"] for d in domains] == [FOUNDATIONS, WEB, PYTHON]
    foundations, web, python = domains
    assert [(d["name"], d["total_topics"]) for d in domains] == [
        ("Foundations", 10), ("Web Development", 30), ("Python", 20)
    ]
    assert all(d["description"] for d in domains)
    for d in domains:
        assert (d["joined"], d["joined_at"], d["onboarded"], d["suggested"]) == (False, None, False, False)
        assert (d["completed_topics"], d["in_progress_topics"], d["progress_percent"]) == (0, 0, 0.0)
        assert d["known_topics"] == [] and d["ready_topics"] == [] and d["curriculum_complete"] is False
    # Starting topics: five in Foundations, four in Web Development (Git Basics is shared), one in Python.
    assert (foundations["available_topics"], web["available_topics"], python["available_topics"]) == (5, 4, 1)
    assert progress_rows(db, user_id) == {}  # reading the catalogue writes nothing for a new learner


def test_catalogue_counts_progress_made_through_another_domain(client, make_user):
    _, headers = make_user()
    onboard(client, headers, WEB, ["git_basics", "css_basics"])  # css_basics brings html_basics

    by_id = catalogue(client, headers)

    web, foundations = by_id[WEB], by_id[FOUNDATIONS]
    assert (web["completed_topics"], web["progress_percent"], web["joined"], web["onboarded"]) == (3, 10.0, True, True)
    # Git Basics counts in Foundations too, so the learner has a head start there.
    assert (foundations["completed_topics"], foundations["progress_percent"]) == (1, 10.0)
    assert foundations["known_topics"] == [{"id": "git_basics", "name": "Git Basics"}]
    assert (foundations["joined"], foundations["suggested"]) == (False, True)
    assert [t["id"] for t in web["known_topics"]] == ["css_basics", "git_basics", "html_basics"]
    # Topics opened by that progress (not starting topics) are "ready".
    ready = {t["id"] for t in web["ready_topics"]}
    assert {"semantic_html", "css_grid"} <= ready
    assert not {"javascript_fundamentals", "sql_basics", "html_basics"} & ready


def test_a_joined_domain_is_never_suggested(client, make_user):
    _, headers = make_user()
    onboard(client, headers, WEB, ["git_basics"])
    assert catalogue(client, headers)[FOUNDATIONS]["suggested"] is True

    join(client, headers, FOUNDATIONS)

    assert catalogue(client, headers)[FOUNDATIONS]["suggested"] is False
    assert home(client, headers)["suggestions"] == []


def test_completed_domain(client, make_user):
    _, headers = make_user()
    onboard(client, headers, FOUNDATIONS, ALL_FOUNDATIONS)

    foundations = catalogue(client, headers)[FOUNDATIONS]

    assert (foundations["curriculum_complete"], foundations["progress_percent"], foundations["available_topics"]) == (
        True, 100.0, 0
    )


def test_catalogue_counts_topics_in_progress(client, make_user, fake_llm):
    _, headers = make_user()
    onboard(client, headers, WEB, ["css_basics"])  # brings html_basics: two completed
    assert client.get("/api/quiz/generate/semantic_html", headers=headers).status_code == 200

    by_id = catalogue(client, headers)

    assert (by_id[WEB]["in_progress_topics"], by_id[WEB]["completed_topics"]) == (1, 2)
    assert by_id[FOUNDATIONS]["in_progress_topics"] == 0


@pytest.mark.parametrize("url", ["/api/domains", "/api/home"])
def test_reading_saves_newly_learnable_topics(client, make_user, db, url):
    user_id, headers = make_user()
    onboard(client, headers, WEB)
    db.execute(text("UPDATE topic_progress SET status = 'locked' WHERE user_id = :u AND topic_id = 'html_basics'"),
               {"u": user_id})
    db.commit()

    assert client.get(url, headers=headers).status_code == 200

    assert progress_rows(db, user_id)["html_basics"][0] == "unlocked"


def test_catalogue_uses_two_neo4j_queries(client, make_user, monkeypatch):
    _, headers = make_user()
    onboard(client, headers, WEB, ["git_basics"])
    calls = count_neo4j_reads(monkeypatch)

    catalogue(client, headers)

    assert len(calls) == 2  # every topic + the frontier, however many domains there are


def test_enrolment_in_a_domain_no_longer_offered_is_ignored(client, make_user, db):
    user_id, headers = make_user()
    db.add(DomainEnrolment(user_id=user_id, domain_id="retired-domain"))
    db.commit()

    assert set(catalogue(client, headers)) == {FOUNDATIONS, WEB, PYTHON}
    assert home(client, headers)["domains"] == []


# --- Joining -----------------------------------------------------------------------------

def test_join_a_domain(client, make_user, db):
    user_id, headers = make_user()
    response = join(client, headers, FOUNDATIONS)

    assert response.status_code == 201
    body = response.json()
    assert (body["domain"], body["domain_name"], body["onboarded"]) == (FOUNDATIONS, "Foundations", False)
    joined_at = datetime.fromisoformat(body["joined_at"])
    assert abs(joined_at - datetime.now(timezone.utc)) < timedelta(minutes=1)
    foundations = catalogue(client, headers)[FOUNDATIONS]
    assert (foundations["joined"], foundations["onboarded"]) == (True, False)
    assert learning_path(client, headers, FOUNDATIONS)["onboarded"] is False
    assert progress_rows(db, user_id) == {}  # joining records interest only


def test_joining_again_changes_nothing(client, make_user, db):
    user_id, headers = make_user()
    first = join(client, headers, WEB).json()

    again = join(client, headers, WEB)

    assert again.status_code == 200
    assert again.json() == first
    assert db.scalar(select(func.count()).select_from(DomainEnrolment).where(DomainEnrolment.user_id == user_id)) == 1


def test_joining_never_changes_topic_status(client, make_user, db):
    user_id, headers = make_user()
    onboard(client, headers, WEB, ["git_basics"])
    before = progress_rows(db, user_id)

    join(client, headers, FOUNDATIONS)

    assert progress_rows(db, user_id) == before


@pytest.mark.parametrize("domain", ["quantum-basket-weaving", "Web-Development", "pytest-x"])
def test_joining_an_unknown_domain_is_rejected(client, make_user, db, domain):
    _, headers = make_user()
    response = join(client, headers, domain)

    assert response.status_code == 404
    assert response.json() == {"detail": f"Unknown domain '{domain}'"}
    assert db.scalar(select(func.count()).select_from(DomainEnrolment)) == 0


def test_joining_is_per_learner(client, make_user):
    _, alice = make_user("alice@example.com")
    _, bob = make_user("bob@example.com")
    join(client, alice, FOUNDATIONS)

    assert catalogue(client, bob)[FOUNDATIONS]["joined"] is False


# --- Onboarding per domain ---------------------------------------------------------------

def test_onboarding_joins_the_domain_and_marks_it_onboarded(client, make_user):
    _, headers = make_user()
    assert learning_path(client, headers, WEB)["onboarded"] is False

    onboard(client, headers, WEB)

    assert learning_path(client, headers, WEB)["onboarded"] is True
    assert dashboard(client, headers, WEB)["onboarded"] is True
    web = catalogue(client, headers)[WEB]
    assert (web["joined"], web["onboarded"]) == (True, True)


def test_onboarding_after_joining_keeps_the_join_date(client, make_user, db):
    user_id, headers = make_user()
    joined_at = join(client, headers, FOUNDATIONS).json()["joined_at"]

    onboard(client, headers, FOUNDATIONS)

    assert catalogue(client, headers)[FOUNDATIONS]["joined_at"] == joined_at
    assert catalogue(client, headers)[FOUNDATIONS]["onboarded"] is True


def test_onboarding_is_per_domain(client, make_user):
    _, headers = make_user()
    onboard(client, headers, FOUNDATIONS, ["git_basics"])

    web_path = learning_path(client, headers, WEB)

    assert learning_path(client, headers, FOUNDATIONS)["onboarded"] is True
    assert web_path["onboarded"] is False
    # Not onboarded in Web Development, but Git Basics already counts there.
    assert [t["id"] for t in web_path["recommended"]] == ["html_basics", "javascript_fundamentals", "sql_basics"]
    assert catalogue(client, headers)[WEB]["joined"] is False


def test_onboarding_again_keeps_the_first_onboarding_date(client, make_user, db):
    user_id, headers = make_user()
    onboard(client, headers, WEB)
    first = db.scalar(select(DomainEnrolment.onboarded_at).where(DomainEnrolment.user_id == user_id))

    onboard(client, headers, WEB, ["html_basics"])

    db.expire_all()
    assert db.scalar(select(DomainEnrolment.onboarded_at).where(DomainEnrolment.user_id == user_id)) == first


# --- Home --------------------------------------------------------------------------------

def test_home_for_a_new_learner_is_empty_and_writes_nothing(client, make_user, db):
    user_id, headers = make_user()

    assert home(client, headers) == {"domains": [], "up_next": [], "suggestions": [], "recent_attempts": []}
    assert progress_rows(db, user_id) == {}


def test_home_shows_each_joined_domain_with_its_next_topic(client, make_user):
    _, headers = make_user()
    onboard(client, headers, WEB, ["html_basics"])

    body = home(client, headers)

    assert [d["id"] for d in body["domains"]] == [WEB]
    web = body["domains"][0]
    assert (web["completed_topics"], web["total_topics"], web["onboarded"]) == (1, 30, True)
    path = learning_path(client, headers, WEB)["recommended"]
    assert web["up_next"] == path[0]
    assert body["up_next"] == [{**topic, "domains": [WEB]} for topic in path]


def test_home_up_next_spans_onboarded_domains_and_lists_shared_topics_once(client, make_user):
    _, headers = make_user()
    onboard(client, headers, WEB)
    onboard(client, headers, FOUNDATIONS)

    body = home(client, headers)

    assert [d["id"] for d in body["domains"]] == [WEB, FOUNDATIONS]  # the order they were joined
    # Easiest first, then by name, across both domains; Git Basics counts towards both.
    assert [(t["id"], t["domains"]) for t in body["up_next"]] == [
        ("command_line_basics", [FOUNDATIONS]),
        ("git_basics", [WEB, FOUNDATIONS]),
        ("html_basics", [WEB]),
    ]


def test_a_joined_domain_without_onboarding_adds_nothing_to_up_next(client, make_user):
    _, headers = make_user()
    onboard(client, headers, WEB, ["git_basics"])
    join(client, headers, FOUNDATIONS)

    body = home(client, headers)

    foundations = next(d for d in body["domains"] if d["id"] == FOUNDATIONS)
    assert (foundations["onboarded"], foundations["up_next"]) == (False, None)
    assert all(t["domains"] == [WEB] for t in body["up_next"])
    assert "command_line_basics" not in {t["id"] for t in body["up_next"]}


def test_home_suggests_domains_with_a_head_start(client, make_user):
    _, headers = make_user()
    onboard(client, headers, WEB, ["git_basics"])

    suggestions = home(client, headers)["suggestions"]

    assert [s["id"] for s in suggestions] == [FOUNDATIONS]
    assert suggestions[0]["known_topics"] == [{"id": "git_basics", "name": "Git Basics"}]


def test_home_without_any_head_start_suggests_nothing(client, make_user):
    _, headers = make_user()
    onboard(client, headers, WEB, ["html_basics"])  # nothing shared with Foundations

    assert home(client, headers)["suggestions"] == []


def test_completed_domain_has_no_next_topic(client, make_user):
    _, headers = make_user()
    onboard(client, headers, FOUNDATIONS, ALL_FOUNDATIONS)

    body = home(client, headers)

    assert body["domains"][0]["curriculum_complete"] is True and body["domains"][0]["up_next"] is None
    assert body["up_next"] == []


def test_home_uses_two_neo4j_queries(client, make_user, monkeypatch):
    _, headers = make_user()
    onboard(client, headers, WEB)
    onboard(client, headers, FOUNDATIONS)
    calls = count_neo4j_reads(monkeypatch)

    home(client, headers)

    assert len(calls) == 2


# --- Quizzes per domain ------------------------------------------------------------------

def test_locked_quiz_names_only_the_unfinished_prerequisites(client, make_user, fake_llm):
    _, headers = make_user()
    onboard(client, headers, WEB, ["html_basics"])

    response = client.get("/api/quiz/generate/react_fundamentals", headers=headers)

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Topic is still locked. Complete its prerequisites first: CSS Basics, JavaScript Fundamentals."
    }


def test_dashboard_counts_only_the_domains_quizzes_and_home_counts_all(client, make_user, fake_llm, quiz_taker):
    _, headers = make_user()
    onboard(client, headers, WEB)
    onboard(client, headers, FOUNDATIONS)
    quiz_taker(headers, "html_basics", "WWW")
    quiz_taker(headers, "command_line_basics", "WWW")
    quiz_taker(headers, "git_basics", "WWW")  # shared: counts in both domains

    web, foundations = dashboard(client, headers, WEB), dashboard(client, headers, FOUNDATIONS)

    assert web["stats"]["total_attempts"] == 2
    assert [a["topic_id"] for a in web["recent_attempts"]] == ["git_basics", "html_basics"]
    assert foundations["stats"]["total_attempts"] == 2
    assert [a["topic_id"] for a in foundations["recent_attempts"]] == ["git_basics", "command_line_basics"]
    assert [a["topic_id"] for a in home(client, headers)["recent_attempts"]] == [
        "git_basics", "command_line_basics", "html_basics"
    ]


def test_home_keeps_quizzes_on_topics_no_longer_in_the_curriculum(client, make_user, db, fake_llm, quiz_taker):
    user_id, headers = make_user()
    onboard(client, headers, WEB)
    quiz_taker(headers, "html_basics", "CCC")
    db.execute(text("UPDATE quiz_attempts SET topic_id = 'retired_topic' WHERE user_id = :u"), {"u": user_id})
    db.commit()

    recent = home(client, headers)["recent_attempts"]

    assert [(a["topic_id"], a["topic_name"]) for a in recent] == [("retired_topic", "retired_topic")]
    assert dashboard(client, headers, WEB)["recent_attempts"] == []


# --- Existing learners (one-time migration) ----------------------------------------------

@pytest.fixture()
def without_enrolments_table(engine):
    """Recreate the pre-Phase-23 database shape: everything except domain_enrolments."""
    DomainEnrolment.__table__.drop(engine)
    yield
    DomainEnrolment.__table__.create(engine, checkfirst=True)


def test_existing_learners_are_enrolled_once_when_the_table_is_created(engine, db, without_enrolments_table):
    early = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)
    learner = User(username="Early", email="early@example.com", hashed_password="$2b$12$" + "a" * 53)
    newcomer = User(username="New", email="new@example.com", hashed_password="$2b$12$" + "b" * 53)
    db.add_all([learner, newcomer])
    db.flush()
    db.add_all([
        TopicProgress(user_id=learner.id, topic_id="html_basics", created_at=early),
        TopicProgress(user_id=learner.id, topic_id="css_basics", created_at=early + timedelta(days=2)),
    ])
    db.commit()

    init_db(engine)

    rows = db.scalars(select(DomainEnrolment)).all()
    assert [(r.user_id, r.domain_id, r.joined_at, r.onboarded_at) for r in rows] == [
        (learner.id, WEB, early, early)
    ]

    # Runs only when the table is first created: a later startup never re-enrols anyone.
    db.execute(text("DELETE FROM domain_enrolments"))
    db.commit()
    init_db(engine)
    assert db.scalar(select(func.count()).select_from(DomainEnrolment)) == 0
