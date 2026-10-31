"""The whole curriculum: every domain, one shared pool of topics and one prerequisite graph.

This module is the single source of truth for the seeded graph. Each domain lives in its own
file under seed/domains/; edit those and restart the backend, and the seeder updates Neo4j to
match (see seed/seed_graph.py).
"""

import re
from collections import defaultdict

from seed.domains.ai_ml import AI_ML
from seed.domains.cs_core import CS_CORE
from seed.domains.data_science import DATA_SCIENCE
from seed.domains.databases import DATABASES
from seed.domains.foundations import FOUNDATIONS
from seed.domains.python import PYTHON
from seed.domains.web_development import WEB_DEVELOPMENT
from seed.model import RESOURCE_TYPES, Domain, Resource, Topic

__all__ = [
    "CATALOG", "DEFAULT_DOMAIN", "DOMAINS", "DOMAIN_BY_ID", "PREREQUISITES", "RESOURCE_TYPES", "TOPICS",
    "CurriculumError", "Domain", "Resource", "Topic", "validate_curriculum",
]

DOMAINS: tuple[Domain, ...] = (
    FOUNDATIONS, WEB_DEVELOPMENT, PYTHON, DATA_SCIENCE, AI_ML, DATABASES, CS_CORE,
)
DOMAIN_BY_ID: dict[str, Domain] = {d.id: d for d in DOMAINS}

# The shared pool: every topic exactly once, and every prerequisite edge.
TOPICS: tuple[Topic, ...] = tuple(t for d in DOMAINS for t in d.topics)
PREREQUISITES: tuple[tuple[str, str], ...] = tuple(e for d in DOMAINS for e in d.prerequisites)

# The domain the API uses when a request doesn't name one (the frontend shows only this one until
# domains can be chosen in the UI).
DEFAULT_DOMAIN = WEB_DEVELOPMENT.id

# Seeded nodes are tagged with this, so other seeds (e.g. the tests') never prune them.
CATALOG = "adaptlearn"

_DOMAIN_ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_TOPIC_ID = re.compile(r"^[a-z][a-z0-9_]*$")


class CurriculumError(ValueError):
    pass


def validate_curriculum(domains: tuple[Domain, ...]) -> None:
    """Raise CurriculumError if the curriculum is inconsistent. Run before anything is written to Neo4j."""
    problems: list[str] = []
    if not domains:
        problems.append("no domains")

    domain_ids = [d.id for d in domains]
    for duplicate in sorted({i for i in domain_ids if domain_ids.count(i) > 1}):
        problems.append(f"duplicate domain id: {duplicate}")

    home: dict[str, str] = {}  # topic id -> the domain that defines it
    for d in domains:
        if not _DOMAIN_ID.match(d.id):
            problems.append(f"domain id {d.id!r} must be lowercase words joined by hyphens")
        if not d.name.strip() or not d.description.strip():
            problems.append(f"domain {d.id}: name and description are required")
        if not d.topic_ids:
            problems.append(f"domain {d.id}: has no topics")
        for t in d.topics:
            if t.id in home:
                problems.append(f"topic {t.id} is defined in both {home[t.id]} and {d.id}")
            else:
                home[t.id] = d.id
            problems.extend(_topic_problems(t))

    for d in domains:
        own = {t.id for t in d.topics}
        for topic_id in d.shared:
            if topic_id in own:
                problems.append(f"domain {d.id}: shares its own topic {topic_id}")
            elif topic_id not in home:
                problems.append(f"domain {d.id}: shares unknown topic {topic_id}")
        if len(set(d.shared)) != len(d.shared):
            problems.append(f"domain {d.id}: shares a topic twice")
        for source, target in d.prerequisites:
            if target not in own:
                problems.append(f"domain {d.id}: edge {source} -> {target} belongs in the domain that defines {target}")

    edges = [e for d in domains for e in d.prerequisites]
    if len(set(edges)) != len(edges):
        problems.append("duplicate prerequisite edges")
    for source, target in edges:
        if source not in home or target not in home:
            problems.append(f"edge {source} -> {target} references an unknown topic")
        if source == target:
            problems.append(f"edge {source} -> {target} is a self-loop")

    cycle = _find_cycle(set(home), edges)
    if cycle:
        problems.append("prerequisite cycle: " + " -> ".join(cycle))

    if problems:
        raise CurriculumError("Invalid curriculum:\n  " + "\n  ".join(problems))


def _topic_problems(t: Topic) -> list[str]:
    problems = []
    if not _TOPIC_ID.match(t.id):
        problems.append(f"topic id {t.id!r} must be lowercase letters, digits and underscores")
    if not t.name.strip() or not t.description.strip():
        problems.append(f"{t.id}: name and description are required")
    if not 1 <= t.difficulty <= 4:
        problems.append(f"{t.id}: difficulty {t.difficulty} is outside 1-4")
    if not 1 <= len(t.resources) <= 3:
        problems.append(f"{t.id}: needs 1-3 resources, has {len(t.resources)}")
    for r in t.resources:
        if r.type not in RESOURCE_TYPES:
            problems.append(f"{t.id}: resource type {r.type!r} is not one of {RESOURCE_TYPES}")
        if not r.url.startswith("https://") or not r.title.strip():
            problems.append(f"{t.id}: resource {r.title!r} needs a title and an https URL")
    return problems


def _find_cycle(nodes: set[str], edges: list[tuple[str, str]]) -> list[str] | None:
    graph: dict[str, list[str]] = defaultdict(list)
    for source, target in edges:
        graph[source].append(target)
    visiting, done = set(), set()
    path: list[str] = []

    def visit(node: str) -> list[str] | None:
        visiting.add(node)
        path.append(node)
        for nxt in graph[node]:
            if nxt in visiting:
                return path[path.index(nxt):] + [nxt]
            if nxt not in done:
                found = visit(nxt)
                if found:
                    return found
        visiting.discard(node)
        done.add(node)
        path.pop()
        return None

    for node in sorted(nodes):
        if node not in done:
            found = visit(node)
            if found:
                return found
    return None
