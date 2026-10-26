"""add agent traces

Revision ID: f3a9b8c7d6e5
Revises: 6593cb632837
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a9b8c7d6e5"
down_revision: Union[str, None] = "6593cb632837"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_traces",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("trace_id", sa.String(length=36), nullable=False),
        sa.Column("learner_id", sa.String(length=36), nullable=False),
        sa.Column("agent", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=False),
        sa.Column("error", sa.String(length=255), nullable=True),
        sa.Column("input_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["learner_id"], ["learner_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trace_id"),
    )
    op.create_index("ix_agent_traces_trace_id", "agent_traces", ["trace_id"])
    op.create_index("ix_agent_traces_learner_id", "agent_traces", ["learner_id"])
    op.create_index("ix_agent_traces_agent", "agent_traces", ["agent"])
    op.create_index("ix_agent_traces_created_at", "agent_traces", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_agent_traces_created_at", table_name="agent_traces")
    op.drop_index("ix_agent_traces_agent", table_name="agent_traces")
    op.drop_index("ix_agent_traces_learner_id", table_name="agent_traces")
    op.drop_index("ix_agent_traces_trace_id", table_name="agent_traces")
    op.drop_table("agent_traces")