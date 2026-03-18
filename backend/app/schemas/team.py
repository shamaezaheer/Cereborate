"""Pydantic schemas for team collaboration endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel


# ─── Questions ────────────────────────────────────────────────────────────────

class QuestionCreate(BaseModel):
    question_text: str
    component_id: uuid.UUID | None = None


class QuestionResponse(BaseModel):
    id: uuid.UUID
    idea_id: uuid.UUID
    component_id: uuid.UUID | None
    asked_by: uuid.UUID | None
    question_text: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Answers ──────────────────────────────────────────────────────────────────

class AnswerCreate(BaseModel):
    answer_text: str


class AnswerResponse(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    answered_by: uuid.UUID | None
    answer_text: str
    is_ai_generated: bool
    approved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Notifications ────────────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    idea_id: uuid.UUID | None
    component_id: uuid.UUID | None
    message: str
    read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Shared idea views ────────────────────────────────────────────────────────

class SharedIdeaResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    status: str
    shareability_index: float
    shared_dep_count: int
    creator_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class SharedIdeaDetailResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    status: str
    deadline: datetime | None
    components: list[dict]   # filtered by access tier — no budget
    shareability_index: float

    model_config = {"from_attributes": True}
