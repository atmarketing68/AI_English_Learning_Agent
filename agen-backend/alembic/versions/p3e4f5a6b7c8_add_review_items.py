"""add review_items for spaced repetition

Revision ID: p3e4f5a6b7c8
Revises: o2d3e4f5a6b7
Create Date: 2026-10-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "p3e4f5a6b7c8"
down_revision: Union[str, None] = "o2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "review_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("learner_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("front", sa.Text(), nullable=False),
        sa.Column("back", sa.Text(), nullable=False),
        sa.Column("phonetic", sa.String(100), nullable=True),
        sa.Column("example", sa.Text(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.Column("source_lesson_id", sa.String(36), nullable=True),
        sa.Column("state", sa.String(20), nullable=False, server_default="new"),
        sa.Column("stability", sa.Float(), nullable=True),
        sa.Column("difficulty", sa.Float(), nullable=True),
        sa.Column("reps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lapses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("due_at", sa.DateTime(), nullable=False),
        sa.Column("last_review_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("learner_id", "kind", "key", name="uq_review_item_learner_kind_key"),
    )
    op.create_index("ix_review_items_learner_due", "review_items", ["learner_id", "due_at"])


def downgrade() -> None:
    op.drop_index("ix_review_items_learner_due", table_name="review_items")
    op.drop_table("review_items")
