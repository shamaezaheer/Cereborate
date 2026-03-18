import uuid
from datetime import datetime

from pydantic import BaseModel


class DependencyCreate(BaseModel):
    target_component_id: uuid.UUID
    dependency_type: str


class DependencyResponse(BaseModel):
    id: uuid.UUID
    source_component_id: uuid.UUID
    target_component_id: uuid.UUID
    dependency_type: str
    is_cross_idea: bool
    llm_detected: bool
    confirmed: bool
    llm_rationale: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DependencyConfirmRequest(BaseModel):
    confirmed: bool


class DependencyGraphResponse(BaseModel):
    nodes: list[dict]
    edges: list[dict]


class SharedDepComponentView(BaseModel):
    id: str
    name: str
    description: str
    status: str
    deadline: str | None
    idea_id: str


class SharedDependencyResponse(BaseModel):
    dependency_id: str
    dependency_type: str
    source: SharedDepComponentView
    target: SharedDepComponentView
