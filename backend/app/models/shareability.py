"""Shareability models — tiered access control with LLM-scored classification."""

import uuid
from enum import Enum

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class ShareabilityClassification(str, Enum):
    public = "public"
    internal = "internal"
    confidential = "confidential"
    restricted = "restricted"


class ShareabilityRule(Base, TenantMixin, TimestampMixin):
    __tablename__ = "shareability_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    idea_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ideas.id", ondelete="CASCADE"), nullable=True
    )
    component_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("idea_components.id", ondelete="CASCADE"),
        nullable=True,
    )
    min_access_tier: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    classification: Mapped[str] = mapped_column(
        String(20), default=ShareabilityClassification.public.value, nullable=False
    )
    auto_classified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    overridden_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class AccessGrant(Base, TenantMixin, TimestampMixin):
    __tablename__ = "access_grants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    idea_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False
    )
    component_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("idea_components.id", ondelete="CASCADE"),
        nullable=True,
    )
    granted_to_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    granted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
