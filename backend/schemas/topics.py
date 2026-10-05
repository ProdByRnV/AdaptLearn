from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

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


TopicId = Annotated[str, StringConstraints(min_length=1, max_length=100)]


class MarkKnownRequest(BaseModel):
    domain: str = Field(default="web-development", examples=["web-development"])
    topic_ids: list[TopicId] = Field(
        default_factory=list,
        max_length=100,
        description="Topics the learner already knows. May be empty.",
        examples=[["html_basics", "css_basics"]],
    )


class RecommendedTopic(BaseModel):
    id: str
    name: str
    description: str
    difficulty: int
    status: StatusValue
    mastery: float = Field(description="Mastery percentage (p_know x 100), one decimal place")
    prerequisites: list[str] = Field(description="Prerequisite topic ids")
    prerequisite_names: list[str] = Field(description="Prerequisite topic names, same order as prerequisites")


class MarkKnownResponse(BaseModel):
    message: str
    known_count: int = Field(description="Topics now marked known, including implied prerequisites")
    added_prerequisites: list[str] = Field(
        description="Prerequisites marked known automatically because a later topic was selected"
    )
    recommended: list[RecommendedTopic] = Field(description="Next topics to learn (at most 3)")
