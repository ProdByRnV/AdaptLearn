from typing import Literal

from pydantic import BaseModel, Field

StatusValue = Literal["locked", "unlocked", "in_progress", "completed"]


class ResourceOut(BaseModel):
    title: str
    url: str
    type: Literal["docs", "video", "article"]


class TopicOut(BaseModel):
    id: str
    name: str
    description: str
    difficulty: int
    resources: list[ResourceOut]


class TopicsResponse(BaseModel):
    domain: str
    topics: list[TopicOut]


class GraphNode(TopicOut):
    status: StatusValue
    mastery: float = Field(description="Mastery percentage (p_know x 100), one decimal place")
    mastered: bool = Field(description="True when p_know >= 0.95")
    prerequisites: list[str] = Field(description="Ids of topics that must be completed first")


class GraphLink(BaseModel):
    source: str = Field(description="Prerequisite topic id")
    target: str = Field(description="Topic it unlocks")


class GraphResponse(BaseModel):
    domain: str
    nodes: list[GraphNode]
    links: list[GraphLink]
