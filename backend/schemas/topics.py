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


class ExternalPrerequisite(BaseModel):
    id: str
    name: str
    domain: str = Field(description="Id of the domain that defines this prerequisite")
    domain_name: str
    completed: bool = Field(description="True when the learner has completed this prerequisite")


class GraphNode(TopicOut):
    status: StatusValue
    mastery: float = Field(description="Mastery percentage (p_know x 100), one decimal place")
    mastered: bool = Field(description="True when p_know >= 0.95")
    prerequisites: list[str] = Field(description="Ids of topics in this domain that must be completed first")
    external_prerequisites: list[ExternalPrerequisite] = Field(
        default_factory=list, description="Prerequisites from other domains, which must also be completed first"
    )
    domains: list[str] = Field(default_factory=list, description="Every domain this topic belongs to")
    home_domain: str = Field(description="The domain that defines this topic")


class GraphLink(BaseModel):
    source: str = Field(description="Prerequisite topic id")
    target: str = Field(description="Topic it unlocks")


class DomainRef(BaseModel):
    id: str
    name: str


class GraphResponse(BaseModel):
    domain: str
    domain_name: str
    domains: list[DomainRef] = Field(description="Every domain, to name the other domains a topic belongs to")
    nodes: list[GraphNode]
    links: list[GraphLink]


class MapResponse(BaseModel):
    domains: list[DomainRef] = Field(description="Every domain, in curriculum order")
    nodes: list[GraphNode] = Field(description="Every topic once, easiest first; no external prerequisites")
    links: list[GraphLink] = Field(description="Every prerequisite, across domains")


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


class LearningPathResponse(BaseModel):
    domain: str
    onboarded: bool = Field(description="False until the learner has completed onboarding")
    curriculum_complete: bool = Field(description="True when every topic in the domain is completed")
    recommended: list[RecommendedTopic] = Field(description="Next topics to learn (at most 3), easiest first")


class MarkKnownResponse(BaseModel):
    message: str
    known_count: int = Field(description="Topics now marked known, including implied prerequisites")
    added_prerequisites: list[str] = Field(
        description="Prerequisites marked known automatically because a later topic was selected"
    )
    recommended: list[RecommendedTopic] = Field(description="Next topics to learn (at most 3)")
