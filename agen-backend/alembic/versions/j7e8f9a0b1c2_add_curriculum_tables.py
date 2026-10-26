"""add curriculum map tables

Revision ID: j7e8f9a0b1c2
Revises: i6d7e8f9a0b1
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "j7e8f9a0b1c2"
down_revision: Union[str, None] = "i6d7e8f9a0b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── curriculum_units ──────────────────────────────────────────────────────
    op.create_table(
        "curriculum_units",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("level", sa.String(length=10), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("theme", sa.String(length=100), nullable=True),
        sa.Column("icon", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_curriculum_units_level", "curriculum_units", ["level"])

    # ── curriculum_lessons ────────────────────────────────────────────────────
    op.create_table(
        "curriculum_lessons",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("unit_id", sa.String(length=36), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("skill", sa.String(length=20), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=True),
        sa.Column("topic", sa.String(length=100), nullable=False),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("vocabulary_focus", sa.JSON(), nullable=True),
        sa.Column("grammar_focus", sa.String(length=150), nullable=True),
        sa.Column("cefr_reference", sa.String(length=20), nullable=True),
        sa.Column("vietnam_curriculum_ref", sa.String(length=100), nullable=True),
        sa.Column("prerequisite_code", sa.String(length=40), nullable=True),
        sa.Column("is_review", sa.Boolean(), nullable=True),
        sa.Column("is_assessment", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["unit_id"], ["curriculum_units.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_curriculum_lessons_unit_id", "curriculum_lessons", ["unit_id"])

    # ── learner_curriculum_progress ───────────────────────────────────────────
    op.create_table(
        "learner_curriculum_progress",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("learner_id", sa.String(length=36), nullable=False),
        sa.Column("curriculum_lesson_id", sa.String(length=36), nullable=False),
        sa.Column("generated_lesson_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("best_score", sa.Integer(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=True),
        sa.Column("mastered", sa.Boolean(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["learner_id"], ["learner_profiles.id"]),
        sa.ForeignKeyConstraint(["curriculum_lesson_id"], ["curriculum_lessons.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_learner_curriculum_progress_learner_id",
        "learner_curriculum_progress", ["learner_id"],
    )
    op.create_index(
        "ix_learner_curriculum_progress_curriculum_lesson_id",
        "learner_curriculum_progress", ["curriculum_lesson_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_learner_curriculum_progress_curriculum_lesson_id", table_name="learner_curriculum_progress")
    op.drop_index("ix_learner_curriculum_progress_learner_id", table_name="learner_curriculum_progress")
    op.drop_table("learner_curriculum_progress")
    op.drop_index("ix_curriculum_lessons_unit_id", table_name="curriculum_lessons")
    op.drop_table("curriculum_lessons")
    op.drop_index("ix_curriculum_units_level", table_name="curriculum_units")
    op.drop_table("curriculum_units")
