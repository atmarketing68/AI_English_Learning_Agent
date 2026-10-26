"""G11: AI podcast episodes, booked club sessions, teacher writing re-grade, refunds

Revision ID: a4d5e6f7a8b9
Revises: z3c4d5e6f7a8
Create Date: 2026-10-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a4d5e6f7a8b9"
down_revision: Union[str, None] = "z3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "generated_episodes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("level", sa.String(4), nullable=False),
        sa.Column("topic", sa.String(120), nullable=True),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("status", sa.String(12), nullable=False, server_default="draft"),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("youtube_id", sa.String(20), nullable=True),
        sa.Column("video_start", sa.Integer(), nullable=True),
        sa.Column("video_end", sa.Integer(), nullable=True),
        sa.Column("eval_score", sa.Float(), nullable=True),
        sa.Column("eval_flagged", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_generated_episodes_status", "generated_episodes", ["status"])

    with op.batch_alter_table("speaking_rooms") as batch:
        batch.add_column(sa.Column("scheduled_at", sa.DateTime(), nullable=True))
    op.create_index("ix_speaking_rooms_scheduled_at", "speaking_rooms", ["scheduled_at"])
    with op.batch_alter_table("room_members") as batch:
        batch.add_column(sa.Column("reminded_at", sa.DateTime(), nullable=True))

    with op.batch_alter_table("writing_submissions") as batch:
        batch.add_column(sa.Column("teacher_score", sa.Float(), nullable=True))
        batch.add_column(sa.Column("teacher_band", sa.Float(), nullable=True))
        batch.add_column(sa.Column("teacher_comment", sa.Text(), nullable=True))
        batch.add_column(sa.Column("teacher_user_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("teacher_scored_at", sa.DateTime(), nullable=True))

    with op.batch_alter_table("payment_orders") as batch:
        batch.add_column(sa.Column("refunded_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("refund_txn", sa.String(120), nullable=True))
        batch.add_column(sa.Column("refund_note", sa.String(300), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("payment_orders") as batch:
        batch.drop_column("refund_note")
        batch.drop_column("refund_txn")
        batch.drop_column("refunded_at")
    with op.batch_alter_table("writing_submissions") as batch:
        for col in ("teacher_scored_at", "teacher_user_id", "teacher_comment", "teacher_band", "teacher_score"):
            batch.drop_column(col)
    with op.batch_alter_table("room_members") as batch:
        batch.drop_column("reminded_at")
    op.drop_index("ix_speaking_rooms_scheduled_at", table_name="speaking_rooms")
    with op.batch_alter_table("speaking_rooms") as batch:
        batch.drop_column("scheduled_at")
    op.drop_index("ix_generated_episodes_status", table_name="generated_episodes")
    op.drop_table("generated_episodes")
