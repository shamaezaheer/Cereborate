"""Pydantic schemas for shareability endpoints."""

import uuid

from pydantic import BaseModel, Field


class ShareabilityRuleResponse(BaseModel):
    id: uuid.UUID
    idea_id: uuid.UUID | None
    component_id: uuid.UUID | None
    min_access_tier: int
    classification: str
    auto_classified: bool
    overridden_by: uuid.UUID | None

    model_config = {"from_attributes": True}


class ShareabilityUpdate(BaseModel):
    min_access_tier: int = Field(ge=1, le=10)
    classification: str


class IdeaShareabilityResponse(BaseModel):
    idea_id: uuid.UUID
    shareability_index: float = Field(ge=0.0, le=1.0)
    rules: list[ShareabilityRuleResponse]
    component_scores: list["ComponentShareabilityInfo"]


class ComponentShareabilityInfo(BaseModel):
    component_id: uuid.UUID
    name: str
    shareability_score: float
    classification: str
    min_access_tier: int
    auto_classified: bool


class AccessGrantResponse(BaseModel):
    id: uuid.UUID
    idea_id: uuid.UUID
    component_id: uuid.UUID | None
    granted_to_user_id: uuid.UUID
    granted_by: uuid.UUID
    reason: str | None

    model_config = {"from_attributes": True}
