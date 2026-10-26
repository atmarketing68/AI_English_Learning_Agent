"""add persisted roleplay sessions

Revision ID: b4d2f7a1c901
Revises: 6593cb632837
Create Date: 2026-09-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4d2f7a1c901"
down_revision: Union[str, None] = "6593cb632837"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roleplay_sessions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("learner_id", sa.String(36), nullable=False),
        sa.Column("topic", sa.String(255), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("history", sa.JSON(), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("total_turns", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["learner_id"], ["learner_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_roleplay_sessions_learner_id",
        "roleplay_sessions",
        ["learner_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_roleplay_sessions_learner_id", table_name="roleplay_sessions")
    op.drop_table("roleplay_sessions")