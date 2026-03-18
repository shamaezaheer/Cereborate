"""Pydantic schemas for structured LLM output parsing."""

from pydantic import BaseModel, Field


class ExtractedIdeaData(BaseModel):
    title: str = Field(default="")
    description: str = Field(default="")
    deadline: str | None = Field(default=None, description="ISO date string or null")
    total_budget: float | None = Field(default=None)
    budget_currency: str = Field(default="USD")
    components: list["ExtractedComponent"] = Field(default_factory=list)
    follow_up_question: str | None = Field(
        default=None, description="Next question to ask the user, or null if complete"
    )
    is_complete: bool = Field(
        default=False, description="True when enough info to create the idea"
    )


class ExtractedComponent(BaseModel):
    name: str
    description: str
    priority: str = Field(default="should_have")
    estimated_cost: float | None = None


class ShareabilityScore(BaseModel):
    classification: str = Field(description="public|internal|confidential|restricted")
    score: float = Field(ge=0.0, le=1.0)
    rationale: str
    min_access_tier: int = Field(ge=1, le=10)


class LinkDetectionResult(BaseModel):
    linked: bool
    link_type: str | None = Field(default=None)
    similarity_rationale: str
    confidence: float = Field(ge=0.0, le=1.0)


class DependencyDetectionResult(BaseModel):
    has_dependency: bool
    dependency_type: str | None = None
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)


class ConsistencyCheckResult(BaseModel):
    has_issues: bool
    issues: list["ConsistencyIssue"] = Field(default_factory=list)


class ConsistencyIssue(BaseModel):
    flag_type: str
    severity: str = Field(description="info|warning|critical")
    description: str


class QuestionAnswerResult(BaseModel):
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    needs_owner_approval: bool = Field(default=True)
