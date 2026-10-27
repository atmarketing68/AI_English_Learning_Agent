"""G13: class tests, AI-generated speaking exams

Revision ID: c6f7a8b9c0d1
Revises: b5e6f7a8b9c0
Create Date: 2026-10-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c6f7a8b9c0d1"
down_revision: Union[str, None] = "b5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "group_tests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("group_id", sa.String(36), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("kind", sa.String(12), nullable=False, server_default="mock"),
        sa.Column("exam_id", sa.String(40), nullable=False),
        sa.Column("title", sa.String(140), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("opens_on", sa.Date(), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=False),
        sa.Column("reminded_on", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_group_tests_group_id", "group_tests", ["group_id"])

    for table in ("exam_attempts", "speaking_exam_attempts"):
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column("group_test_id", sa.String(36), nullable=True))
        op.create_index(f"ix_{table}_group_test_id", table, ["group_test_id"])

    op.create_table(
        "generated_speaking_exams",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("exam", sa.String(10), nullable=False),
        sa.Column("title", sa.String(140), nullable=False),
        sa.Column("topic", sa.String(120), nullable=True),
        sa.Column("status", sa.String(12), nullable=False, server_default="draft"),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("tasks", sa.Float(), nullable=False, server_default="0"),
        sa.Column("eval_score", sa.Float(), nullable=True),
        sa.Column("eval_flagged", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_generated_speaking_exams_status", "generated_speaking_exams", ["status"])


def downgrade() -> None:
    op.drop_index("ix_generated_speaking_exams_status", table_name="generated_speaking_exams")
    op.drop_table("generated_speaking_exams")
    for table in ("speaking_exam_attempts", "exam_attempts"):
        op.drop_index(f"ix_{table}_group_test_id", table_name=table)
        with op.batch_alter_table(table) as batch:
            batch.drop_column("group_test_id")
    op.drop_index("ix_group_tests_group_id", table_name="group_tests")
    op.drop_table("group_tests")
