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
from seed.domains.ai_ml import AI_ML
from seed.domains.app_development import APP_DEVELOPMENT
from seed.domains.blockchain import BLOCKCHAIN
from seed.domains.cloud_devops import CLOUD_DEVOPS
from seed.domains.cs_core import CS_CORE
from seed.domains.cybersecurity import CYBERSECURITY
from seed.domains.data_science import DATA_SCIENCE
from seed.domains.databases import DATABASES
from seed.domains.foundations import FOUNDATIONS
from seed.domains.game_development import GAME_DEVELOPMENT
from seed.domains.python import PYTHON
from seed.domains.ui_ux_design import UI_UX_DESIGN
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
    assert [d.id for d in DOMAINS] == [
        "foundations", "web-development", "python", "data-science", "ai-ml", "databases", "cs-core",
        "cybersecurity", "cloud-devops", "blockchain", "app-development", "game-development", "ui-ux-design",
    ]
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

EXPECTED_FOUNDATIONS = {
    "how_computers_work": 1, "binary_data_representation": 1, "data_formats": 2, "programming_concepts": 1,
    "algorithmic_thinking": 2, "command_line_basics": 1, "operating_system_basics": 2, "git_basics": 1,
    "how_the_internet_works": 1, "security_basics": 1,
}


def _needs(topic_id: str) -> set[str]:
    return {s for s, t in PREREQUISITES if t == topic_id}


def test_foundations_topics_and_difficulties():
    assert {i: TOPIC_BY_ID[i].difficulty for i in FOUNDATIONS.topic_ids} == EXPECTED_FOUNDATIONS
    assert FOUNDATIONS.shared == ()


def test_foundations_original_topics_are_still_starting_topics():
    # Learners who began on these keep them open, and Web Development's starting topics don't change.
    for topic_id in ("command_line_basics", "how_the_internet_works", "git_basics"):
        assert _needs(topic_id) == set(), topic_id
    starting = {i for i in FOUNDATIONS.topic_ids if not _needs(i)}
    assert starting == {
        "how_computers_work", "programming_concepts", "command_line_basics", "git_basics", "how_the_internet_works",
    }


def test_no_prerequisite_reaches_into_web_development_from_another_domain():
    web = set(WEB_DEVELOPMENT.topic_ids)
    assert {(s, t) for s, t in PREREQUISITES if t in web and s not in web} == set()


def test_git_basics_is_defined_once_in_foundations_and_shared_with_web_development():
    assert [d.id for d in DOMAINS if "git_basics" in {t.id for t in d.topics}] == ["foundations"]
    assert "git_basics" in WEB_DEVELOPMENT.shared
    assert [t.id for t in TOPICS].count("git_basics") == 1


# --- Python ------------------------------------------------------------------------------

EXPECTED_PYTHON = {
    "python_basics": 1, "python_control_flow": 1, "python_strings": 1, "python_functions": 2,
    "python_lists_tuples": 2, "python_dicts_sets": 2, "python_comprehensions": 2, "python_modules": 2,
    "python_virtual_environments": 2, "python_standard_library": 2, "python_files": 2, "python_exceptions": 2,
    "python_type_hints": 2, "python_oop": 3, "python_inheritance": 3, "python_iterators_generators": 3,
    "python_decorators": 3, "python_testing": 3, "python_http_requests": 3, "python_async": 4,
}


def test_python_topics_and_difficulties():
    assert {i: TOPIC_BY_ID[i].difficulty for i in PYTHON.topic_ids} == EXPECTED_PYTHON
    assert len(PYTHON.prerequisites) == 28


def test_python_starts_from_python_basics_with_no_prerequisites():
    assert [i for i in PYTHON.topic_ids if not _needs(i)] == ["python_basics"]


def test_python_builds_on_three_foundations_topics():
    python = set(PYTHON.topic_ids)
    assert {(s, t) for s, t in PREREQUISITES if t in python and s not in python} == {
        ("command_line_basics", "python_virtual_environments"),
        ("data_formats", "python_files"),
        ("how_the_internet_works", "python_http_requests"),
    }


def test_every_python_topic_can_be_reached_from_python_basics_and_foundations():
    done = set(FOUNDATIONS.topic_ids)
    remaining = set(PYTHON.topic_ids)
    while remaining:
        ready = {i for i in remaining if _needs(i) <= done}
        assert ready, f"unreachable: {sorted(remaining)}"
        done |= ready
        remaining -= ready


def test_python_has_no_prerequisites_from_later_domains():
    python = set(PYTHON.topic_ids)
    later = set(DATA_SCIENCE.topic_ids) | set(AI_ML.topic_ids)
    assert not {s for s, t in PREREQUISITES if t in python} & later


# --- Data Science and AI & ML ---------------------------------------------------------------

EXPECTED_DATA_SCIENCE = {
    "ds_jupyter": 1, "ds_numpy": 2, "ds_pandas_basics": 2, "ds_data_cleaning": 2, "ds_pandas_grouping": 3,
    "ds_visualisation": 2, "ds_time_series": 3, "ds_descriptive_stats": 1, "ds_probability": 2,
    "ds_distributions": 3, "ds_sampling": 3, "ds_hypothesis_testing": 3, "ds_ab_testing": 4, "ds_correlation": 2,
    "ds_eda": 3, "ds_communicating": 3,
}
EXPECTED_AI_ML = {
    "ml_what_is_ml": 1, "ml_linear_algebra": 2, "ml_calculus": 3, "ml_train_test": 2, "ml_linear_regression": 2,
    "ml_logistic_regression": 3, "ml_evaluation_metrics": 3, "ml_overfitting": 3, "ml_gradient_descent": 3,
    "ml_scikit_learn": 3, "ml_feature_engineering": 3, "ml_decision_trees": 3, "ml_clustering": 3, "ml_pca": 4,
    "ml_neural_networks": 3, "ml_training_nn": 4, "ml_cnn": 4, "ml_embeddings": 4, "ml_transformers": 4,
    "ml_llm_apis": 3, "ml_responsible_ai": 2,
}


def _edges_into(domain: Domain) -> set[tuple[str, str]]:
    own = {t.id for t in domain.topics}
    return {(s, t) for s, t in PREREQUISITES if t in own and s not in own}


def test_data_science_topics_and_difficulties():
    assert {t.id: t.difficulty for t in DATA_SCIENCE.topics} == EXPECTED_DATA_SCIENCE
    assert len(DATA_SCIENCE.prerequisites) == 20
    # Linear Regression lives in AI & ML and is shared, so progress on it counts in both.
    assert DATA_SCIENCE.shared == ("ml_linear_regression",)
    assert "ml_linear_regression" in AI_ML.topic_ids


def test_ai_ml_topics_and_difficulties():
    assert {i: TOPIC_BY_ID[i].difficulty for i in AI_ML.topic_ids} == EXPECTED_AI_ML
    assert len(AI_ML.prerequisites) == 31
    assert AI_ML.shared == ()


def test_starting_topics_of_data_science_and_ai_ml():
    assert [t.id for t in DATA_SCIENCE.topics if not _needs(t.id)] == ["ds_descriptive_stats"]
    assert [i for i in AI_ML.topic_ids if not _needs(i)] == ["ml_what_is_ml", "ml_linear_algebra"]


def test_data_science_builds_on_python_and_foundations():
    assert _edges_into(DATA_SCIENCE) == {
        ("python_basics", "ds_jupyter"),
        ("python_lists_tuples", "ds_numpy"),
        ("python_dicts_sets", "ds_pandas_basics"),
        ("data_formats", "ds_pandas_basics"),
    }


def test_ai_ml_builds_on_data_science_and_python():
    assert _edges_into(AI_ML) == {
        ("ds_correlation", "ml_linear_regression"),
        ("ds_pandas_basics", "ml_scikit_learn"),
        ("ds_data_cleaning", "ml_feature_engineering"),
        ("python_http_requests", "ml_llm_apis"),
    }


def test_every_data_science_and_ai_ml_topic_can_be_reached():
    done = {t.id for d in (FOUNDATIONS, PYTHON) for t in d.topics}
    remaining = set(DATA_SCIENCE.topic_ids) | set(AI_ML.topic_ids)
    while remaining:
        ready = {i for i in remaining if _needs(i) <= done}
        assert ready, f"unreachable: {sorted(remaining)}"
        done |= ready
        remaining -= ready


# --- Databases and Computer Science Core ------------------------------------------------------

EXPECTED_DATABASES = {
    "db_data_models": 1, "db_keys_constraints": 2, "db_sql_joins": 2, "db_sql_aggregation": 2,
    "db_subqueries_ctes": 3, "db_window_functions": 3, "db_schema_design": 3, "db_indexes": 3,
    "db_transactions": 3, "db_isolation_locking": 4, "db_python_access": 3, "db_scaling": 4,
    "db_data_warehousing": 3, "db_nosql": 2, "db_mongodb": 3, "db_redis": 3, "db_graph_databases": 3,
}
EXPECTED_CS_CORE = {
    "cs_complexity": 2, "cs_arrays_linked_lists": 2, "cs_stacks_queues": 2, "cs_hash_tables": 2, "cs_recursion": 2,
    "cs_sorting": 3, "cs_trees": 3, "cs_heaps": 3, "cs_graphs": 3, "cs_shortest_paths": 4, "cs_greedy": 3,
    "cs_dynamic_programming": 4, "cs_complexity_classes": 4, "cs_computer_architecture": 2,
    "cs_processes_threads": 3, "cs_memory_management": 3, "cs_concurrency": 4, "cs_networking": 3,
    "cs_compilers_interpreters": 3,
}


def test_databases_topics_and_difficulties():
    assert {t.id: t.difficulty for t in DATABASES.topics} == EXPECTED_DATABASES
    assert len(DATABASES.prerequisites) == 24
    # SQL Basics lives in Web Development and is shared, so progress on it counts in both.
    assert DATABASES.shared == ("sql_basics",)


def test_cs_core_topics_and_difficulties():
    assert {t.id: t.difficulty for t in CS_CORE.topics} == EXPECTED_CS_CORE
    assert len(CS_CORE.prerequisites) == 27
    assert CS_CORE.shared == ()


def test_starting_topics_of_databases_and_cs_core():
    assert [i for i in DATABASES.topic_ids if not _needs(i)] == ["db_data_models", "sql_basics"]
    assert [t.id for t in CS_CORE.topics if not _needs(t.id)] == ["cs_complexity"]


def test_databases_and_cs_core_build_on_earlier_domains():
    assert _edges_into(DATABASES) == {
        ("sql_basics", "db_keys_constraints"),
        ("sql_basics", "db_sql_joins"),
        ("sql_basics", "db_sql_aggregation"),
        ("python_exceptions", "db_python_access"),
        ("data_formats", "db_mongodb"),
    }
    assert _edges_into(CS_CORE) == {
        ("binary_data_representation", "cs_computer_architecture"),
        ("operating_system_basics", "cs_processes_threads"),
        ("how_the_internet_works", "cs_networking"),
        ("programming_concepts", "cs_compilers_interpreters"),
    }


# --- Cybersecurity and Cloud & DevOps ---------------------------------------------------------

EXPECTED_CYBERSECURITY = {
    "sec_principles": 1, "sec_threats_attacks": 2, "sec_cryptography": 2, "sec_pki_tls": 3,
    "sec_identity_access": 3, "sec_threat_modelling": 3, "sec_network_security": 3, "sec_web_security": 3,
    "sec_secure_coding": 3, "sec_system_hardening": 3, "sec_vulnerability_management": 3,
    "sec_logging_monitoring": 3, "sec_incident_response": 4, "sec_forensics": 4, "sec_penetration_testing": 4,
    "sec_cloud_security": 4, "sec_privacy_compliance": 3,
}
EXPECTED_CLOUD_DEVOPS = {
    "devops_culture": 1, "devops_linux_admin": 2, "devops_shell_scripting": 2, "devops_git_workflows": 2,
    "devops_ci": 3, "devops_cd": 3, "devops_containers": 3, "devops_kubernetes": 4, "devops_iac": 3,
    "devops_config_management": 3, "cloud_computing_basics": 1, "cloud_compute": 2, "cloud_storage": 2,
    "cloud_iam": 3, "cloud_networking": 3, "cloud_serverless": 3, "cloud_architecture": 4,
    "devops_monitoring": 3, "devops_sre": 4, "devops_devsecops": 4,
}


def test_cybersecurity_topics_and_difficulties():
    assert CYBERSECURITY.id == "cybersecurity"  # the id that switches on the defensive-only quiz rule
    assert {t.id: t.difficulty for t in CYBERSECURITY.topics} == EXPECTED_CYBERSECURITY
    assert len(CYBERSECURITY.prerequisites) == 26
    # Security Basics lives in Foundations and is shared, so progress on it counts in both.
    assert CYBERSECURITY.shared == ("security_basics",)


def test_cloud_devops_topics_and_difficulties():
    assert {t.id: t.difficulty for t in CLOUD_DEVOPS.topics} == EXPECTED_CLOUD_DEVOPS
    assert len(CLOUD_DEVOPS.prerequisites) == 31
    assert CLOUD_DEVOPS.shared == ()


def test_starting_topics_of_cybersecurity_and_cloud_devops():
    assert [i for i in CYBERSECURITY.topic_ids if not _needs(i)] == ["sec_principles"]
    assert [t.id for t in CLOUD_DEVOPS.topics if not _needs(t.id)] == ["devops_culture"]


def test_cybersecurity_and_cloud_devops_build_on_earlier_domains():
    assert _edges_into(CYBERSECURITY) == {
        ("security_basics", "sec_threats_attacks"),
        ("binary_data_representation", "sec_cryptography"),
        ("how_the_internet_works", "sec_pki_tls"),
        ("programming_concepts", "sec_secure_coding"),
        ("operating_system_basics", "sec_system_hardening"),
        ("cloud_computing_basics", "sec_cloud_security"),
    }
    assert _edges_into(CLOUD_DEVOPS) == {
        ("operating_system_basics", "devops_linux_admin"),
        ("command_line_basics", "devops_shell_scripting"),
        ("git_basics", "devops_git_workflows"),
        ("how_the_internet_works", "cloud_computing_basics"),
        ("security_basics", "cloud_iam"),
    }


def test_every_cybersecurity_topic_is_about_defence():
    # The resources and descriptions are written from the defender's side; none promises attack how-tos.
    for topic in CYBERSECURITY.topics:
        text = f"{topic.name} {topic.description}".lower()
        assert not any(word in text for word in ("exploit code", "payload", "bypass", "evade", "crack ")), topic.id


# --- Blockchain & Web3 and App Development ----------------------------------------------------

EXPECTED_BLOCKCHAIN = {
    "bc_what_is_blockchain": 1, "bc_hash_functions": 2, "bc_keys_signatures": 2, "bc_p2p_networks": 2,
    "bc_use_cases": 2, "bc_wallets": 3, "bc_consensus": 3, "bc_bitcoin": 3, "bc_ethereum": 3,
    "bc_smart_contracts": 3, "bc_solidity": 3, "bc_dev_tools": 4, "bc_tokens": 4, "bc_contract_security": 4,
    "bc_dapps": 4, "bc_oracles_storage": 4, "bc_defi": 4, "bc_scaling": 4,
}
EXPECTED_APP_DEVELOPMENT = {
    "app_mobile_landscape": 1, "app_mobile_ux": 2, "app_kotlin_basics": 2, "app_swift_basics": 2,
    "app_android_compose": 3, "app_swiftui": 3, "app_react_native": 3, "app_flutter": 3, "app_pwa": 3,
    "app_navigation": 3, "app_lifecycle": 3, "app_networking": 3, "app_local_storage": 3,
    "app_permissions_privacy": 3, "app_architecture": 4, "app_notifications": 4, "app_testing": 4,
    "app_performance": 4, "app_security": 4, "app_publishing": 4,
}


def test_blockchain_topics_and_difficulties():
    assert {t.id: t.difficulty for t in BLOCKCHAIN.topics} == EXPECTED_BLOCKCHAIN
    assert len(BLOCKCHAIN.prerequisites) == 27
    assert BLOCKCHAIN.shared == ()


def test_app_development_topics_and_difficulties():
    assert {t.id: t.difficulty for t in APP_DEVELOPMENT.topics} == EXPECTED_APP_DEVELOPMENT
    assert len(APP_DEVELOPMENT.prerequisites) == 37
    assert APP_DEVELOPMENT.shared == ()


def test_starting_topics_of_blockchain_and_app_development():
    assert [i for i in BLOCKCHAIN.topic_ids if not _needs(i)] == ["bc_what_is_blockchain"]
    assert [i for i in APP_DEVELOPMENT.topic_ids if not _needs(i)] == ["app_mobile_landscape"]


def test_blockchain_and_app_development_build_on_earlier_domains():
    assert _edges_into(BLOCKCHAIN) == {
        ("binary_data_representation", "bc_hash_functions"),
        ("how_the_internet_works", "bc_p2p_networks"),
        ("security_basics", "bc_wallets"),
        ("programming_concepts", "bc_smart_contracts"),
        ("async_javascript", "bc_dapps"),
    }
    assert _edges_into(APP_DEVELOPMENT) == {
        ("programming_concepts", "app_kotlin_basics"),
        ("programming_concepts", "app_swift_basics"),
        ("programming_concepts", "app_flutter"),
        ("react_fundamentals", "app_react_native"),
        ("responsive_design", "app_pwa"),
        ("async_javascript", "app_pwa"),
        ("operating_system_basics", "app_lifecycle"),
        ("how_the_internet_works", "app_networking"),
        ("data_formats", "app_networking"),
        ("sql_basics", "app_local_storage"),
        ("security_basics", "app_permissions_privacy"),
        ("ux_heuristics", "app_mobile_ux"),
    }


def test_every_blockchain_topic_stays_technical():
    # Blockchain is taught as technology: no topic promises investing, trading or price tips.
    for topic in BLOCKCHAIN.topics:
        text = f"{topic.name} {topic.description}".lower()
        assert not any(word in text for word in ("invest", "trading", "profit", "price prediction", "get rich")), topic.id


# --- Game Development and UI/UX Design --------------------------------------------------------

EXPECTED_GAME_DEVELOPMENT = {
    "game_what_is_gamedev": 1, "game_design_basics": 2, "game_loop": 2, "game_vectors": 2, "game_engines": 2,
    "game_transforms": 3, "game_godot": 3, "game_unity": 3, "game_input": 3, "game_physics": 3,
    "game_2d_graphics": 3, "game_state_machines": 3, "game_audio": 3, "game_feel": 3, "game_level_design": 3,
    "game_3d_graphics": 4, "game_ai": 4, "game_multiplayer": 4, "game_optimisation": 4, "game_shipping": 4,
}
EXPECTED_UI_UX_DESIGN = {
    "ux_what_is": 1, "ux_user_research": 2, "ux_personas_journeys": 2, "ux_information_architecture": 2,
    "ux_heuristics": 2, "ux_visual_hierarchy": 2, "ux_typography": 2, "ux_colour": 2, "ux_wireframing": 2,
    "ux_interaction_design": 3, "ux_accessible_design": 3, "ux_figma": 3, "ux_prototyping": 3,
    "ux_writing_forms": 3, "ux_usability_testing": 3, "ux_ethics": 3, "ux_design_systems": 4, "ux_metrics": 4,
    "ux_handoff": 4,
}


def test_game_development_topics_and_difficulties():
    assert {t.id: t.difficulty for t in GAME_DEVELOPMENT.topics} == EXPECTED_GAME_DEVELOPMENT
    assert len(GAME_DEVELOPMENT.prerequisites) == 30
    assert GAME_DEVELOPMENT.shared == ()


def test_ui_ux_design_topics_and_difficulties():
    assert {t.id: t.difficulty for t in UI_UX_DESIGN.topics} == EXPECTED_UI_UX_DESIGN
    assert len(UI_UX_DESIGN.prerequisites) == 25
    assert UI_UX_DESIGN.shared == ("app_mobile_ux",)


def test_starting_topics_of_game_development_and_ui_ux_design():
    assert [i for i in GAME_DEVELOPMENT.topic_ids if not _needs(i)] == ["game_what_is_gamedev"]
    assert [i for i in UI_UX_DESIGN.topic_ids if not _needs(i)] == ["ux_what_is"]


def test_game_development_and_ui_ux_design_build_on_earlier_domains():
    assert _edges_into(GAME_DEVELOPMENT) == {
        ("programming_concepts", "game_loop"),
        ("programming_concepts", "game_godot"),
        ("programming_concepts", "game_unity"),
        ("cs_graphs", "game_ai"),
        ("how_the_internet_works", "game_multiplayer"),
        ("cs_complexity", "game_optimisation"),
    }
    assert _edges_into(UI_UX_DESIGN) == {("css_basics", "ux_handoff")}


def test_designing_for_mobile_is_shared_by_app_development_and_ui_ux_design():
    # Defined once in App Development, listed in UI/UX Design, and connected to both through its prerequisites.
    assert "app_mobile_ux" in {t.id for t in APP_DEVELOPMENT.topics}
    assert "app_mobile_ux" in UI_UX_DESIGN.topic_ids
    assert _needs("app_mobile_ux") == {"app_mobile_landscape", "ux_heuristics"}


def test_every_domain_has_a_starting_topic():
    # A learner who joins a domain can always start something in it, without another domain first.
    for domain in DOMAINS:
        assert any(not _needs(i) for i in domain.topic_ids), domain.id


def test_every_topic_can_be_reached():
    done: set[str] = set()
    remaining = {t.id for t in TOPICS}
    while remaining:
        ready = {i for i in remaining if _needs(i) <= done}
        assert ready, f"unreachable: {sorted(remaining)}"
        done |= ready
        remaining -= ready


def test_pool_holds_every_topic_once():
    ids = [t.id for t in TOPICS]
    assert len(ids) == len(set(ids)) == 246
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
