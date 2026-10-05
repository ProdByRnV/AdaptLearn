from datetime import datetime

from pydantic import BaseModel, Field

from schemas.topics import RecommendedTopic, ResourceOut, StatusValue


class DashboardStats(BaseModel):
    total_topics: int
    completed_topics: int
    in_progress_topics: int
    mastered_topics: int = Field(description="Topics with p_know >= 0.95")
    average_mastery: float = Field(description="Mean mastery % across the learner's initialised topics")
    total_attempts: int = Field(description="Quizzes submitted")
    progress_percent: float = Field(description="Completed topics as a % of the curriculum")


class AttentionTopic(BaseModel):
    id: str
    name: str
    difficulty: int
    mastery: float
    attempts: int
    resources: list[ResourceOut]


class RecentAttempt(BaseModel):
    id: int
    topic_id: str
    topic_name: str
    score: int
    total: int
    passed: bool
    mastery_before: float
    mastery_after: float
    created_at: datetime


class MasteryItem(BaseModel):
    id: str
    name: str
    difficulty: int
    status: StatusValue
    mastery: float
    mastered: bool


class DashboardResponse(BaseModel):
    domain: str
    onboarded: bool
    curriculum_complete: bool
    stats: DashboardStats
    recommended: list[RecommendedTopic] = Field(description="Next topics to learn (at most 3)")
    needs_attention: list[AttentionTopic]
    recent_attempts: list[RecentAttempt] = Field(description="Latest 5 quiz attempts, newest first")
    mastery: list[MasteryItem] = Field(description="Every topic in the domain, easiest first")


class ProgressItem(BaseModel):
    topic_id: str
    status: StatusValue
    p_know: float
    attempts: int
    correct: int
    needs_attention: bool


class ProgressAllResponse(BaseModel):
    topics: list[ProgressItem]
