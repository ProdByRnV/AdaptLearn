from datetime import datetime

from pydantic import BaseModel, Field

from schemas.progress import RecentAttempt
from schemas.topics import RecommendedTopic


class TopicRef(BaseModel):
    id: str
    name: str


class DomainSummary(BaseModel):
    id: str
    name: str
    description: str
    total_topics: int
    completed_topics: int = Field(description="Completed in any domain: progress belongs to topics")
    in_progress_topics: int
    available_topics: int = Field(description="Topics the learner can study now (prerequisites all completed)")
    progress_percent: float = Field(description="Completed topics as a % of the domain")
    curriculum_complete: bool = Field(description="True when every topic in the domain is completed")
    joined: bool
    joined_at: datetime | None
    onboarded: bool = Field(description="True once the learner has been through this domain's onboarding")
    known_topics: list[TopicRef] = Field(description="The domain's completed topics, easiest first")
    ready_topics: list[TopicRef] = Field(
        description="Available topics that have prerequisites, i.e. opened by what the learner already completed"
    )
    suggested: bool = Field(description="Not joined, but the learner already has a head start here")


class CatalogueResponse(BaseModel):
    domains: list[DomainSummary] = Field(description="Every domain, in curriculum order")


class EnrolmentResponse(BaseModel):
    domain: str
    domain_name: str
    joined_at: datetime
    onboarded: bool


class HomeDomain(DomainSummary):
    up_next: RecommendedTopic | None = Field(description="The next topic to learn in this domain, if any")


class HomeTopic(RecommendedTopic):
    domains: list[str] = Field(description="The learner's onboarded domains this topic counts towards")


class HomeResponse(BaseModel):
    domains: list[HomeDomain] = Field(description="Joined domains, in the order they were joined")
    up_next: list[HomeTopic] = Field(description="Next topics across onboarded domains (at most 3), easiest first")
    suggestions: list[DomainSummary] = Field(
        description="Domains not joined yet with a head start (at most 3), biggest head start first"
    )
    recent_attempts: list[RecentAttempt] = Field(description="Latest 5 quiz attempts in any domain, newest first")
