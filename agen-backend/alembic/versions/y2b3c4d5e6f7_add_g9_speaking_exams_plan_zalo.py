"""G9 · thi thử Speaking, đề do AI sinh, kế hoạch ôn thi, Zalo OA

Revision ID: y2b3c4d5e6f7
Revises: x1a2b3c4d5e6
Create Date: 2026-10-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "y2b3c4d5e6f7"
down_revision: Union[str, None] = "x1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "speaking_exam_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("learner_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=False),
        sa.Column("exam_id", sa.String(40), nullable=False),
        sa.Column("exam", sa.String(10), nullable=False),
        sa.Column("status", sa.String(12), nullable=False, server_default="started"),
        sa.Column("responses", sa.JSON(), nullable=True),
        sa.Column("estimate", sa.Float(), nullable=True),
        sa.Column("criteria", sa.JSON(), nullable=True),
        sa.Column("feedback", sa.JSON(), nullable=True),
        sa.Column("fallback", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("xp_earned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_speaking_exam_attempts_learner_id", "speaking_exam_attempts", ["learner_id"])
    op.create_index("ix_speaking_exam_attempts_exam_id", "speaking_exam_attempts", ["exam_id"])
    op.create_index("ix_speaking_exam_attempts_created_at", "speaking_exam_attempts", ["created_at"])

    op.create_table(
        "generated_exams",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("exam", sa.String(10), nullable=False),
        sa.Column("skill", sa.String(20), nullable=False),
        sa.Column("title", sa.String(140), nullable=False),
        sa.Column("topic", sa.String(120), nullable=True),
        sa.Column("status", sa.String(12), nullable=False, server_default="draft"),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("questions", sa.Float(), nullable=False, server_default="0"),
        sa.Column("eval_score", sa.Float(), nullable=True),
        sa.Column("eval_flagged", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_generated_exams_status", "generated_exams", ["status"])

    op.create_table(
        "app_config",
        sa.Column("key", sa.String(60), primary_key=True),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.add_column("users", sa.Column("zalo_user_id", sa.String(40), nullable=True))
    op.add_column("users", sa.Column("zalo_link_code", sa.String(12), nullable=True))
    op.create_index("ix_users_zalo_user_id", "users", ["zalo_user_id"], unique=True)
    op.create_index("ix_users_zalo_link_code", "users", ["zalo_link_code"], unique=True)

    op.add_column("learner_profiles", sa.Column("exam_target", sa.String(10), nullable=True))
    op.add_column("learner_profiles", sa.Column("exam_target_score", sa.Float(), nullable=True))
    op.add_column("learner_profiles", sa.Column("exam_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("learner_profiles", "exam_date")
    op.drop_column("learner_profiles", "exam_target_score")
    op.drop_column("learner_profiles", "exam_target")
    op.drop_index("ix_users_zalo_link_code", table_name="users")
    op.drop_index("ix_users_zalo_user_id", table_name="users")
    op.drop_column("users", "zalo_link_code")
    op.drop_column("users", "zalo_user_id")
    for name in ("app_config", "generated_exams", "speaking_exam_attempts"):
        op.drop_table(name)
