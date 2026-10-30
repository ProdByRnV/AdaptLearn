from dataclasses import replace

import pytest

from seed.curriculum import (
    DEFAULT_DOMAIN,
    DOMAIN_BY_ID,
    DOMAINS,
    PREREQUISITES,
    TOPICS,
    CurriculumError,
    Domain,
    Resource,
    Topic,
    validate_curriculum,
)
from seed.domains.foundations import FOUNDATIONS
from seed.domains.web_development import WEB_DEVELOPMENT

# ARCHITECTURE.md section 7: id -> difficulty
EXPECTED_WEB_TOPICS = {
    "html_basics": 1, "semantic_html": 1, "forms_accessibility": 2, "css_basics": 1,
    "flexbox": 2, "css_grid": 2, "responsive_design": 2, "javascript_fundamentals": 1,
    "functions_scope": 2, "arrays_objects": 2, "dom_manipulation": 2, "browser_events": 2,
    "async_javascript": 3, "fetch_http_apis": 3, "es_modules": 2, "git_basics": 1,
    "nodejs_basics": 2, "npm_packages": 2, "express_basics": 3, "rest_api_design": 3,
    "authentication_basics": 4, "sql_basics": 2, "postgresql_basics": 3, "react_fundamentals": 2,
    "props_state": 2, "react_hooks": 3, "react_router": 3, "react_api_integration": 3,
    "testing_basics": 4, "deployment_basics": 4,
}
TOPIC_BY_ID = {t.id: t for t in TOPICS}


def _web_edges() -> set[tuple[str, str]]:
    web = set(WEB_DEVELOPMENT.topic_ids)
    return {e for e in PREREQUISITES if e[0] in web and e[1] in web}


def test_real_curriculum_is_valid():
    validate_curriculum(DOMAINS)


def test_domains_and_default():
    assert [d.id for d in DOMAINS] == ["foundations", "web-development"]
    assert DEFAULT_DOMAIN == "web-development"
    assert DOMAIN_BY_ID["web-development"].name == "Web Development"


# --- Web Development keeps exactly the specified curriculum -------------------------

def test_web_development_has_exactly_the_30_specified_topics_and_difficulties():
    assert {i: TOPIC_BY_ID[i].difficulty for i in WEB_DEVELOPMENT.topic_ids} == EXPECTED_WEB_TOPICS


def test_web_development_has_exactly_37_edges():
    assert len(WEB_DEVELOPMENT.prerequisites) == 37
    assert len(_web_edges()) == 37


def test_web_development_roots_and_leaves():
    edges = _web_edges()
    ids = set(WEB_DEVELOPMENT.topic_ids)
    assert ids - {t for _, t in edges} == {"html_basics", "javascript_fundamentals", "git_basics", "sql_basics"}
    assert ids - {s for s, _ in edges} == {
        "deployment_basics", "forms_accessibility", "responsive_design", "browser_events", "es_modules",
    }


@pytest.mark.parametrize(
    "edge",
    [
        ("html_basics", "semantic_html"),
        ("css_grid", "responsive_design"),
        ("git_basics", "nodejs_basics"),
        ("rest_api_design", "postgresql_basics"),
        ("react_router", "react_api_integration"),
        ("authentication_basics", "deployment_basics"),
    ],
)
def test_sample_edges_point_from_prerequisite_to_dependent(edge):
    assert edge in PREREQUISITES
    assert tuple(reversed(edge)) not in PREREQUISITES


# --- Foundations and sharing -----------------------------------------------------------

def test_foundations_starter_set():
    assert set(FOUNDATIONS.topic_ids) == {"command_line_basics", "how_the_internet_works", "git_basics"}
    assert all(TOPIC_BY_ID[i].difficulty == 1 for i in FOUNDATIONS.topic_ids)


def test_git_basics_is_defined_once_in_foundations_and_shared_with_web_development():
    assert [d.id for d in DOMAINS if "git_basics" in {t.id for t in d.topics}] == ["foundations"]
    assert "git_basics" in WEB_DEVELOPMENT.shared
    assert [t.id for t in TOPICS].count("git_basics") == 1


def test_pool_holds_every_topic_once():
    ids = [t.id for t in TOPICS]
    assert len(ids) == len(set(ids)) == 32
    assert set(ids) == {i for d in DOMAINS for i in d.topic_ids}


def test_every_topic_has_1_to_3_https_resources_of_known_type():
    for topic in TOPICS:
        assert 1 <= len(topic.resources) <= 3, topic.id
        for resource in topic.resources:
            assert resource.url.startswith("https://")
            assert resource.type in ("docs", "video", "article")


# --- The validator catches broken curricula ------------------------------------

RES = (Resource("Docs", "https://example.com", "docs"),)
A = Topic("a", "A", "First", 1, RES)
B = Topic("b", "B", "Second", 2, RES)
C = Topic("c", "C", "Third", 2, RES)


def _tiny() -> tuple[Domain, ...]:
    """Two domains: `one` defines a and b; `two` defines c, needs a first and shares b."""
    return (
        Domain("one", "One", "First domain", (A, B), (("a", "b"),)),
        Domain("two", "Two", "Second domain", (C,), (("a", "c"),), shared=("b",)),
    )


def test_validator_accepts_tiny_valid_curriculum_with_a_cross_domain_edge():
    validate_curriculum(_tiny())


def test_validator_rejects_no_domains():
    with pytest.raises(CurriculumError, match="no domains"):
        validate_curriculum(())


def test_validator_rejects_duplicate_domain_ids():
    one, two = _tiny()
    with pytest.raises(CurriculumError, match="duplicate domain id: one"):
        validate_curriculum((one, replace(two, id="one")))


@pytest.mark.parametrize("bad_id", ["Web Dev", "web_dev", "-web", "web-", ""])
def test_validator_rejects_bad_domain_ids(bad_id):
    one, two = _tiny()
    with pytest.raises(CurriculumError, match="lowercase words joined by hyphens"):
        validate_curriculum((replace(one, id=bad_id), two))


@pytest.mark.parametrize("bad_id", ["Html", "html-basics", "1st_topic", ""])
def test_validator_rejects_bad_topic_ids(bad_id):
    one, two = _tiny()
    bad = replace(A, id=bad_id)
    with pytest.raises(CurriculumError, match="lowercase letters, digits and underscores"):
        validate_curriculum((replace(one, topics=(bad, B), prerequisites=()), replace(two, prerequisites=())))


def test_validator_rejects_domain_without_name_or_topics():
    one, two = _tiny()
    with pytest.raises(CurriculumError, match="name and description are required"):
        validate_curriculum((replace(one, name=" "), two))
    with pytest.raises(CurriculumError, match="has no topics"):
        validate_curriculum((one, two, Domain("three", "Three", "Empty", ())))


def test_validator_rejects_topic_without_name_or_description():
    one, two = _tiny()
    with pytest.raises(CurriculumError, match="a: name and description are required"):
        validate_curriculum((replace(one, topics=(replace(A, description=""), B)), two))


def test_validator_rejects_a_topic_defined_in_two_domains():
    one, two = _tiny()
    with pytest.raises(CurriculumError, match="topic b is defined in both one and two"):
        validate_curriculum((one, replace(two, topics=(C, B), shared=())))


def test_validator_rejects_sharing_unknown_own_or_duplicate_topics():
    one, two = _tiny()
    with pytest.raises(CurriculumError, match="shares unknown topic missing"):
        validate_curriculum((one, replace(two, shared=("missing",))))
    with pytest.raises(CurriculumError, match="shares its own topic c"):
        validate_curriculum((one, replace(two, shared=("c",))))
    with pytest.raises(CurriculumError, match="shares a topic twice"):
        validate_curriculum((one, replace(two, shared=("b", "b"))))


def test_validator_rejects_an_edge_filed_in_the_wrong_domain():
    one, two = _tiny()
    with pytest.raises(CurriculumError, match="edge a -> b belongs in the domain that defines b"):
        validate_curriculum((replace(one, prerequisites=()), replace(two, prerequisites=(("a", "c"), ("a", "b")))))


def test_validator_rejects_duplicate_edges():
    one, two = _tiny()
    with pytest.raises(CurriculumError, match="duplicate prerequisite edges"):
        validate_curriculum((replace(one, prerequisites=(("a", "b"), ("a", "b"))), two))


def test_validator_rejects_edge_to_unknown_topic():
    one, two = _tiny()
    with pytest.raises(CurriculumError, match="unknown topic"):
        validate_curriculum((one, replace(two, prerequisites=(("missing", "c"),))))


def test_validator_rejects_cycles_including_across_domains():
    one, two = _tiny()
    with pytest.raises(CurriculumError, match="cycle"):
        validate_curriculum((replace(one, prerequisites=(("a", "b"), ("c", "a"))), two))


def test_validator_rejects_self_loop():
    one, two = _tiny()
    with pytest.raises(CurriculumError, match="self-loop"):
        validate_curriculum((replace(one, prerequisites=(("a", "a"),)), two))


def test_validator_rejects_bad_difficulty():
    one, two = _tiny()
    with pytest.raises(CurriculumError, match="difficulty"):
        validate_curriculum((replace(one, topics=(replace(A, difficulty=5), B)), two))


def test_validator_rejects_missing_or_too_many_resources():
    one, two = _tiny()
    with pytest.raises(CurriculumError, match="1-3 resources"):
        validate_curriculum((replace(one, topics=(replace(A, resources=()), B)), two))
    with pytest.raises(CurriculumError, match="1-3 resources"):
        validate_curriculum((replace(one, topics=(replace(A, resources=RES * 4), B)), two))


def test_validator_rejects_bad_resource_type_and_http_url():
    one, two = _tiny()
    bad_type = (Resource("Talk", "https://example.com", "podcast"),)
    with pytest.raises(CurriculumError, match="resource type"):
        validate_curriculum((replace(one, topics=(replace(A, resources=bad_type), B)), two))
    insecure = (Resource("Docs", "http://example.com", "docs"),)
    with pytest.raises(CurriculumError, match="https URL"):
        validate_curriculum((replace(one, topics=(replace(A, resources=insecure), B)), two))
