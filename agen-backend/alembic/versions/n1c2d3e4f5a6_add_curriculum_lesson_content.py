"""add curriculum lesson content cache

Revision ID: n1c2d3e4f5a6
Revises: m0b1c2d3e4f5
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "n1c2d3e4f5a6"
down_revision: Union[str, None] = "m0b1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "curriculum_lesson_content",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("curriculum_code", sa.String(length=40), nullable=False),
        sa.Column("level", sa.String(length=10), nullable=False),
        sa.Column("skill", sa.String(length=20), nullable=False),
        sa.Column("topic", sa.String(length=100), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("eval_score", sa.Float(), nullable=True),
        sa.Column("eval_flagged", sa.Boolean(), nullable=True),
        sa.Column("eval_flags", sa.JSON(), nullable=True),
        sa.Column("total_exercises", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("curriculum_code"),
    )
    op.create_index("ix_curriculum_lesson_content_curriculum_code", "curriculum_lesson_content", ["curriculum_code"])
    op.create_index("ix_curriculum_lesson_content_level", "curriculum_lesson_content", ["level"])
    op.create_index("ix_curriculum_lesson_content_status", "curriculum_lesson_content", ["status"])


def downgrade() -> None:
    op.drop_index("ix_curriculum_lesson_content_status", table_name="curriculum_lesson_content")
    op.drop_index("ix_curriculum_lesson_content_level", table_name="curriculum_lesson_content")
    op.drop_index("ix_curriculum_lesson_content_curriculum_code", table_name="curriculum_lesson_content")
    op.drop_table("curriculum_lesson_content")
