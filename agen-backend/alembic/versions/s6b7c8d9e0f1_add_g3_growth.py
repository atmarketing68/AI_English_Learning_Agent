"""G3 · growth: guest accounts, payments + trial, weekly league, parent digests, goal tracks

Revision ID: s6b7c8d9e0f1
Revises: r5a6b7c8d9e0
Create Date: 2026-10-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "s6b7c8d9e0f1"
down_revision: Union[str, None] = "r5a6b7c8d9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Học thử không cần đăng ký
    op.add_column("users", sa.Column("is_guest", sa.Boolean(), nullable=False, server_default=sa.false()))

    # Thanh toán thật + dùng thử 7 ngày
    op.add_column("subscriptions", sa.Column("trial_started_at", sa.DateTime(), nullable=True))
    op.create_table(
        "payment_orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("months", sa.Integer(), nullable=False),
        sa.Column("amount_vnd", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("provider_txn", sa.String(120), nullable=True),
        sa.Column("pay_url", sa.String(2000), nullable=True),
        sa.Column("callback", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_payment_orders_user_id", "payment_orders", ["user_id"])

    # Giải đấu tuần
    op.add_column("learner_profiles", sa.Column("league_reward_claimed_week", sa.String(10), nullable=True))

    # Phụ huynh chủ động
    op.add_column("parent_profiles", sa.Column("weekly_report_email", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("parent_profiles", sa.Column("last_weekly_report_week", sa.String(10), nullable=True))
    op.add_column("parent_child_links", sa.Column("last_inactivity_alert_on", sa.String(10), nullable=True))

    # Khoá theo mục tiêu
    op.create_table(
        "goal_track_progress",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("learner_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=False),
        sa.Column("track_id", sa.String(30), nullable=False),
        sa.Column("lesson_code", sa.String(40), nullable=False),
        sa.Column("generated_lesson_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("best_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mastered", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("learner_id", "lesson_code", name="uq_goal_track_learner_lesson"),
    )
    op.create_index("ix_goal_track_progress_learner_id", "goal_track_progress", ["learner_id"])
    op.create_index("ix_goal_track_progress_track_id", "goal_track_progress", ["track_id"])


def downgrade() -> None:
    op.drop_index("ix_goal_track_progress_track_id", table_name="goal_track_progress")
    op.drop_index("ix_goal_track_progress_learner_id", table_name="goal_track_progress")
    op.drop_table("goal_track_progress")
    with op.batch_alter_table("parent_child_links") as batch:
        batch.drop_column("last_inactivity_alert_on")
    with op.batch_alter_table("parent_profiles") as batch:
        batch.drop_column("last_weekly_report_week")
        batch.drop_column("weekly_report_email")
    with op.batch_alter_table("learner_profiles") as batch:
        batch.drop_column("league_reward_claimed_week")
    op.drop_index("ix_payment_orders_user_id", table_name="payment_orders")
    op.drop_table("payment_orders")
    with op.batch_alter_table("subscriptions") as batch:
        batch.drop_column("trial_started_at")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("is_guest")
