"""G8 · thi thử, hỏi Bo, token FCM, hoá đơn VAT

Revision ID: x1a2b3c4d5e6
Revises: w0f1a2b3c4d5
Create Date: 2026-10-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "x1a2b3c4d5e6"
down_revision: Union[str, None] = "w0f1a2b3c4d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "exam_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("learner_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=False),
        sa.Column("exam_id", sa.String(40), nullable=False),
        sa.Column("exam", sa.String(10), nullable=False),
        sa.Column("skill", sa.String(20), nullable=False),
        sa.Column("correct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("estimate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sections", sa.JSON(), nullable=True),
        sa.Column("answers", sa.JSON(), nullable=True),
        sa.Column("seconds", sa.Integer(), nullable=True),
        sa.Column("xp_earned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_exam_attempts_learner_id", "exam_attempts", ["learner_id"])
    op.create_index("ix_exam_attempts_exam_id", "exam_attempts", ["exam_id"])
    op.create_index("ix_exam_attempts_created_at", "exam_attempts", ["created_at"])

    op.create_table(
        "tutor_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("learner_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.Column("fallback", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_tutor_messages_learner_id", "tutor_messages", ["learner_id"])
    op.create_index("ix_tutor_messages_created_at", "tutor_messages", ["created_at"])

    op.create_table(
        "device_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("learner_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=True),
        sa.Column("platform", sa.String(10), nullable=False, server_default="android"),
        sa.Column("token", sa.String(400), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_sent_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("token", name="uq_device_tokens_token"),
    )
    op.create_index("ix_device_tokens_user_id", "device_tokens", ["user_id"])
    op.create_index("ix_device_tokens_learner_id", "device_tokens", ["learner_id"])

    op.add_column("payment_orders", sa.Column("invoice_info", sa.JSON(), nullable=True))
    op.add_column("payment_orders", sa.Column("invoice_issued_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("payment_orders", "invoice_issued_at")
    op.drop_column("payment_orders", "invoice_info")
    for name in ("device_tokens", "tutor_messages", "exam_attempts"):
        op.drop_table(name)
