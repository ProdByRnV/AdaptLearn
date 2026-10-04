from dataclasses import replace

import pytest

from seed.curriculum import (
    DOMAIN,
    PREREQUISITES,
    TOPICS,
    CurriculumError,
    Resource,
    Topic,
    validate_curriculum,
)

# ARCHITECTURE.md section 7: id -> difficulty
EXPECTED_TOPICS = {
    "html_basics": 1, "semantic_html": 1, "forms_accessibility": 2, "css_basics": 1,
    "flexbox": 2, "css_grid": 2, "responsive_design": 2, "javascript_fundamentals": 1,
    "functions_scope": 2, "arrays_objects": 2, "dom_manipulation": 2, "browser_events": 2,
    "async_javascript": 3, "fetch_http_apis": 3, "es_modules": 2, "git_basics": 1,
    "nodejs_basics": 2, "npm_packages": 2, "express_basics": 3, "rest_api_design": 3,
    "authentication_basics": 4, "sql_basics": 2, "postgresql_basics": 3, "react_fundamentals": 2,
    "props_state": 2, "react_hooks": 3, "react_router": 3, "react_api_integration": 3,
    "testing_basics": 4, "deployment_basics": 4,
}


def test_domain_name():
    assert DOMAIN == "web-development"


def test_real_curriculum_is_valid():
    validate_curriculum(TOPICS, PREREQUISITES)


def test_has_exactly_the_30_specified_topics_and_difficulties():
    assert {t.id: t.difficulty for t in TOPICS} == EXPECTED_TOPICS


def test_has_exactly_37_edges():
    assert len(PREREQUISITES) == 37
    assert len(set(PREREQUISITES)) == 37


def test_root_topics_have_no_prerequisites():
    dependents = {target for _, target in PREREQUISITES}
    roots = {t.id for t in TOPICS} - dependents
    assert roots == {"html_basics", "javascript_fundamentals", "git_basics", "sql_basics"}


def test_deployment_is_the_only_final_topic_on_the_main_path():
    prerequisites = {source for source, _ in PREREQUISITES}
    leaves = {t.id for t in TOPICS} - prerequisites
    assert "deployment_basics" in leaves
    assert leaves == {"deployment_basics", "forms_accessibility", "responsive_design", "browser_events", "es_modules"}


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


def test_every_topic_has_1_to_3_https_resources_of_known_type():
    for topic in TOPICS:
        assert 1 <= len(topic.resources) <= 3, topic.id
        for resource in topic.resources:
            assert resource.url.startswith("https://")
            assert resource.type in ("docs", "video", "article")


# --- The validator catches broken curricula ------------------------------------

def _tiny():
    res = (Resource("Docs", "https://example.com", "docs"),)
    topics = (Topic("a", "A", "First", 1, res), Topic("b", "B", "Second", 2, res))
    return topics, (("a", "b"),)


def test_validator_accepts_tiny_valid_curriculum():
    validate_curriculum(*_tiny())


def test_validator_rejects_duplicate_ids():
    topics, edges = _tiny()
    with pytest.raises(CurriculumError, match="duplicate topic ids"):
        validate_curriculum(topics + (topics[0],), edges)


def test_validator_rejects_edge_to_unknown_topic():
    topics, _ = _tiny()
    with pytest.raises(CurriculumError, match="unknown topic"):
        validate_curriculum(topics, (("a", "missing"),))


def test_validator_rejects_cycles():
    topics, _ = _tiny()
    with pytest.raises(CurriculumError, match="cycle"):
        validate_curriculum(topics, (("a", "b"), ("b", "a")))


def test_validator_rejects_self_loop():
    topics, _ = _tiny()
    with pytest.raises(CurriculumError, match="self-loop"):
        validate_curriculum(topics, (("a", "a"),))


def test_validator_rejects_bad_difficulty():
    topics, edges = _tiny()
    with pytest.raises(CurriculumError, match="difficulty"):
        validate_curriculum((replace(topics[0], difficulty=5), topics[1]), edges)


def test_validator_rejects_missing_or_too_many_resources():
    topics, edges = _tiny()
    with pytest.raises(CurriculumError, match="1-3 resources"):
        validate_curriculum((replace(topics[0], resources=()), topics[1]), edges)
    four = topics[0].resources * 4
    with pytest.raises(CurriculumError, match="1-3 resources"):
        validate_curriculum((replace(topics[0], resources=four), topics[1]), edges)


def test_validator_rejects_bad_resource_type_and_http_url():
    topics, edges = _tiny()
    bad_type = (Resource("Talk", "https://example.com", "podcast"),)
    with pytest.raises(CurriculumError, match="resource type"):
        validate_curriculum((replace(topics[0], resources=bad_type), topics[1]), edges)
    insecure = (Resource("Docs", "http://example.com", "docs"),)
    with pytest.raises(CurriculumError, match="https URL"):
        validate_curriculum((replace(topics[0], resources=insecure), topics[1]), edges)
