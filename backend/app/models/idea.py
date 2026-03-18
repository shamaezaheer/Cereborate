import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin, TimestampMixin


class IdeaStatus(str, Enum):
    draft = "draft"
    active = "active"
    archived = "archived"


class ComponentPriority(str, Enum):
    must_have = "must_have"
    should_have = "should_have"
    nice_to_have = "nice_to_have"


class ComponentStatus(str, Enum):
    proposed = "proposed"
    approved = "approved"
    in_progress = "in_progress"
    done = "done"


class PlanningSessionMode(str, Enum):
    chat = "chat"
    form = "form"
    hybrid = "hybrid"


class PlanningSessionStatus(str, Enum):
    active = "active"
    completed = "completed"
    abandoned = "abandoned"


class Idea(Base, TenantMixin, TimestampMixin):
    __tablename__ = "ideas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[IdeaStatus] = mapped_column(
        String(20), default=IdeaStatus.draft, nullable=False
    )
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_budget: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    budget_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    components: Mapped[list["IdeaComponent"]] = relationship(
        back_populates="idea", cascade="all, delete-orphan"
    )
    versions: Mapped[list["IdeaVersion"]] = relationship(
        back_populates="idea", cascade="all, delete-orphan"
    )


class IdeaVersion(Base, TenantMixin):
    __tablename__ = "idea_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    idea_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    idea: Mapped["Idea"] = relationship(back_populates="versions")


class IdeaComponent(Base, TenantMixin, TimestampMixin):
    __tablename__ = "idea_components"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    idea_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    priority: Mapped[ComponentPriority] = mapped_column(
        String(20), default=ComponentPriority.should_have, nullable=False
    )
    status: Mapped[ComponentStatus] = mapped_column(
        String(20), default=ComponentStatus.proposed, nullable=False
    )
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)
    shareability_score: Mapped[float] = mapped_column(Numeric(3, 2), default=0.5, nullable=False)
    shareability_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    idea: Mapped["Idea"] = relationship(back_populates="components")


class PlanningSession(Base, TenantMixin):
    __tablename__ = "planning_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    idea_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ideas.id", ondelete="SET NULL"), nullable=True
    )
    mode: Mapped[PlanningSessionMode] = mapped_column(
        String(20), default=PlanningSessionMode.chat, nullable=False
    )
    status: Mapped[PlanningSessionStatus] = mapped_column(
        String(20), default=PlanningSessionStatus.active, nullable=False
    )
    conversation_history: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    extracted_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
