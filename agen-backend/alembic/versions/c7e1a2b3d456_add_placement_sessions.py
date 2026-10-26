"""add persisted placement sessions

Revision ID: c7e1a2b3d456
Revises: b4d2f7a1c901
Create Date: 2026-09-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7e1a2b3d456"
down_revision: Union[str, None] = "b4d2f7a1c901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "placement_sessions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("learner_id", sa.String(36), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("current_index", sa.Integer(), nullable=False),
        sa.Column("current_question", sa.JSON(), nullable=True),
        sa.Column("last_correct", sa.Boolean(), nullable=True),
        sa.Column("level", sa.String(10), nullable=False),
        sa.Column("learner_age", sa.Integer(), nullable=True),
        sa.Column("learner_grade", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["learner_id"], ["learner_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_placement_sessions_learner_id",
        "placement_sessions",
        ["learner_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_placement_sessions_learner_id", table_name="placement_sessions")
    op.drop_table("placement_sessions")