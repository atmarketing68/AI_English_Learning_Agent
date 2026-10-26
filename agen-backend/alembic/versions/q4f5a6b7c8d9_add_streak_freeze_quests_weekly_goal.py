"""add streak freeze, weekly goal and daily quests

Revision ID: q4f5a6b7c8d9
Revises: p3e4f5a6b7c8
Create Date: 2026-10-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "q4f5a6b7c8d9"
down_revision: Union[str, None] = "p3e4f5a6b7c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Every existing learner starts with one free streak freeze.
    op.add_column("learner_profiles", sa.Column("streak_freezes", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("learner_profiles", sa.Column("streak_freeze_used_at", sa.DateTime(), nullable=True))
    op.add_column("learner_profiles", sa.Column("weekly_goal_days", sa.Integer(), nullable=False, server_default="5"))
    op.add_column("learner_profiles", sa.Column("weekly_goal_claimed_week", sa.String(10), nullable=True))

    op.create_table(
        "daily_quests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("learner_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=False),
        sa.Column("date", sa.String(10), nullable=False),
        sa.Column("slot", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("target", sa.Integer(), nullable=False),
        sa.Column("xp_reward", sa.Integer(), nullable=False),
        sa.Column("claimed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("learner_id", "date", "code", name="uq_daily_quest_learner_date_code"),
    )
    op.create_index("ix_daily_quests_learner_id", "daily_quests", ["learner_id"])


def downgrade() -> None:
    op.drop_index("ix_daily_quests_learner_id", table_name="daily_quests")
    op.drop_table("daily_quests")
    with op.batch_alter_table("learner_profiles") as batch:
        batch.drop_column("weekly_goal_claimed_week")
        batch.drop_column("weekly_goal_days")
        batch.drop_column("streak_freeze_used_at")
        batch.drop_column("streak_freezes")
