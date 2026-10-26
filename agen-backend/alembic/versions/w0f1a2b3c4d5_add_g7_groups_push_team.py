"""G7 · nhóm học (lớp / doanh nghiệp), push phụ huynh, gói theo ghế

Revision ID: w0f1a2b3c4d5
Revises: v9e0f1a2b3c4
Create Date: 2026-10-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "w0f1a2b3c4d5"
down_revision: Union[str, None] = "v9e0f1a2b3c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nhóm học
    op.create_table(
        "groups",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_groups_owner_user_id", "groups", ["owner_user_id"])
    op.create_index("ix_groups_code", "groups", ["code"], unique=True)
    op.create_table(
        "group_members",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("group_id", sa.String(36), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("learner_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("group_id", "learner_id", name="uq_group_member"),
    )
    op.create_index("ix_group_members_group_id", "group_members", ["group_id"])
    op.create_index("ix_group_members_learner_id", "group_members", ["learner_id"])
    op.create_table(
        "group_assignments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("group_id", sa.String(36), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("title", sa.String(140), nullable=False),
        sa.Column("skill", sa.String(20), nullable=False),
        sa.Column("topic", sa.String(100), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("due_on", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_group_assignments_group_id", "group_assignments", ["group_id"])
    op.create_table(
        "group_assignment_done",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("assignment_id", sa.String(36), sa.ForeignKey("group_assignments.id"), nullable=False),
        sa.Column("learner_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("lesson_id", sa.String(36), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("done_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("assignment_id", "learner_id", name="uq_assignment_learner"),
    )
    op.create_index("ix_group_assignment_done_assignment_id", "group_assignment_done", ["assignment_id"])
    op.create_index("ix_group_assignment_done_learner_id", "group_assignment_done", ["learner_id"])

    # Push cho phụ huynh: subscription theo user, learner_id không bắt buộc nữa
    op.alter_column("push_subscriptions", "learner_id", existing_type=sa.String(36), nullable=True)
    op.add_column("push_subscriptions", sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True))
    op.create_index("ix_push_subscriptions_user_id", "push_subscriptions", ["user_id"])
    op.add_column("parent_profiles", sa.Column("push_alerts", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("parent_child_links", sa.Column("last_streak_alert_on", sa.String(10), nullable=True))

    # Gói theo ghế
    op.add_column("subscriptions", sa.Column("seats", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("payment_orders", sa.Column("seats", sa.Integer(), nullable=False, server_default="1"))


def downgrade() -> None:
    op.drop_column("payment_orders", "seats")
    op.drop_column("subscriptions", "seats")
    op.drop_column("parent_child_links", "last_streak_alert_on")
    op.drop_column("parent_profiles", "push_alerts")
    op.drop_index("ix_push_subscriptions_user_id", table_name="push_subscriptions")
    op.drop_column("push_subscriptions", "user_id")
    op.alter_column("push_subscriptions", "learner_id", existing_type=sa.String(36), nullable=False)
    for name in ("group_assignment_done", "group_assignments", "group_members", "groups"):
        op.drop_table(name)
