"""add daily reminder settings and web push subscriptions

Revision ID: r5a6b7c8d9e0
Revises: q4f5a6b7c8d9
Create Date: 2026-10-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "r5a6b7c8d9e0"
down_revision: Union[str, None] = "q4f5a6b7c8d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("learner_profiles", sa.Column("reminder_hour", sa.Integer(), nullable=True))
    op.add_column("learner_profiles", sa.Column("reminder_email", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("learner_profiles", sa.Column("last_reminder_on", sa.String(10), nullable=True))

    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("learner_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False, unique=True),
        sa.Column("p256dh", sa.String(200), nullable=False),
        sa.Column("auth", sa.String(100), nullable=False),
        sa.Column("user_agent", sa.String(300), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_sent_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_push_subscriptions_learner_id", "push_subscriptions", ["learner_id"])


def downgrade() -> None:
    op.drop_index("ix_push_subscriptions_learner_id", table_name="push_subscriptions")
    op.drop_table("push_subscriptions")
    with op.batch_alter_table("learner_profiles") as batch:
        batch.drop_column("last_reminder_on")
        batch.drop_column("reminder_email")
        batch.drop_column("reminder_hour")
