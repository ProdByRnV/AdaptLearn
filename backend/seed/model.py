"""The building blocks of the curriculum: resources, topics and domains.

A topic is defined once, in the domain file it belongs to most (its home domain). Other domains
include it by id, so learners master it once and it counts everywhere it is used.
"""

from dataclasses import dataclass, field
from typing import Literal

ResourceType = Literal["docs", "video", "article"]
RESOURCE_TYPES: tuple[str, ...] = ("docs", "video", "article")


@dataclass(frozen=True)
class Resource:
    title: str
    url: str
    type: ResourceType


@dataclass(frozen=True)
class Topic:
    id: str
    name: str
    description: str
    difficulty: int
    resources: tuple[Resource, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Domain:
    """A curated collection of topics.

    `topics` are defined here (this is their home domain); `shared` are ids of topics defined in
    other domains that this one also uses. `prerequisites` are (prerequisite, dependent) edges whose
    dependent is one of this domain's own topics; the prerequisite may come from any domain.
    """

    id: str
    name: str
    description: str
    topics: tuple[Topic, ...]
    prerequisites: tuple[tuple[str, str], ...] = ()
    shared: tuple[str, ...] = ()

    @property
    def topic_ids(self) -> tuple[str, ...]:
        return tuple(t.id for t in self.topics) + self.shared


def docs(title: str, url: str) -> Resource:
    return Resource(title, url, "docs")


def article(title: str, url: str) -> Resource:
    return Resource(title, url, "article")


def video(title: str, url: str) -> Resource:
    return Resource(title, url, "video")
