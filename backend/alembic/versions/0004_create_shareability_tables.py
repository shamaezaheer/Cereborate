"""create_shareability_tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "shareability_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idea_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("component_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("min_access_tier", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "classification", sa.String(20), nullable=False, server_default="public"
        ),
        sa.Column(
            "auto_classified", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("overridden_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["idea_id"], ["ideas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["component_id"], ["idea_components.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["overridden_by"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_shareability_rules_tenant_id", "shareability_rules", ["tenant_id"]
    )
    op.create_index(
        "ix_shareability_rules_idea_id", "shareability_rules", ["idea_id"]
    )
    op.create_index(
        "ix_shareability_rules_component_id",
        "shareability_rules",
        ["component_id"],
    )

    op.create_table(
        "access_grants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idea_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("component_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "granted_to_user_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("granted_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["idea_id"], ["ideas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["component_id"], ["idea_components.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["granted_to_user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["granted_by"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_access_grants_tenant_id", "access_grants", ["tenant_id"]
    )


def downgrade() -> None:
    op.drop_table("access_grants")
    op.drop_table("shareability_rules")
