import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ComponentBase(BaseModel):
    name: str
    description: str = ""
    priority: str = "should_have"
    estimated_cost: Decimal | None = None
    deadline: datetime | None = None


class ComponentCreate(ComponentBase):
    pass


class ComponentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    estimated_cost: Decimal | None = None
    deadline: datetime | None = None


class ComponentResponse(ComponentBase):
    id: uuid.UUID
    idea_id: uuid.UUID
    status: str
    shareability_score: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IdeaCreate(BaseModel):
    title: str
    description: str = ""
    deadline: datetime | None = None
    total_budget: Decimal | None = None
    budget_currency: str = "USD"


class IdeaUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    deadline: datetime | None = None
    total_budget: Decimal | None = None
    budget_currency: str | None = None


class IdeaResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    creator_id: uuid.UUID | None
    title: str
    description: str
    status: str
    deadline: datetime | None
    total_budget: Decimal | None
    budget_currency: str
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IdeaDetailResponse(IdeaResponse):
    components: list[ComponentResponse] = []
