"""add AI evaluation columns to agent_traces

Revision ID: l9a0b1c2d3e4
Revises: k8f9a0b1c2d3
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "l9a0b1c2d3e4"
down_revision: Union[str, None] = "k8f9a0b1c2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("agent_traces", schema=None) as batch_op:
        batch_op.add_column(sa.Column("eval_score", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("eval_flags", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("eval_flagged", sa.Boolean(), nullable=True))
        batch_op.create_index("ix_agent_traces_eval_flagged", ["eval_flagged"])


def downgrade() -> None:
    with op.batch_alter_table("agent_traces", schema=None) as batch_op:
        batch_op.drop_index("ix_agent_traces_eval_flagged")
        batch_op.drop_column("eval_flagged")
        batch_op.drop_column("eval_flags")
        batch_op.drop_column("eval_score")
