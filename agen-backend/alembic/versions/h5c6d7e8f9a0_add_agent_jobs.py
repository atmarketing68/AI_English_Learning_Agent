"""add durable agent jobs

Revision ID: h5c6d7e8f9a0
Revises: g4b5c6d7e8f9
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "h5c6d7e8f9a0"
down_revision: Union[str, None] = "g4b5c6d7e8f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("trace_id", sa.String(length=36), nullable=False),
        sa.Column("learner_id", sa.String(length=36), nullable=False),
        sa.Column("agent", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["learner_id"], ["learner_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id"),
    )
    op.create_index("ix_agent_jobs_job_id", "agent_jobs", ["job_id"])
    op.create_index("ix_agent_jobs_trace_id", "agent_jobs", ["trace_id"])
    op.create_index("ix_agent_jobs_learner_id", "agent_jobs", ["learner_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_jobs_learner_id", table_name="agent_jobs")
    op.drop_index("ix_agent_jobs_trace_id", table_name="agent_jobs")
    op.drop_index("ix_agent_jobs_job_id", table_name="agent_jobs")
    op.drop_table("agent_jobs")
