"""G6 · bạn học & thử thách đôi

Revision ID: v9e0f1a2b3c4
Revises: u8d9e0f1a2b3
Create Date: 2026-10-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "v9e0f1a2b3c4"
down_revision: Union[str, None] = "u8d9e0f1a2b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "friendships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("a_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=False),
        sa.Column("b_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=False),
        sa.Column("a_claimed_week", sa.String(10), nullable=True),
        sa.Column("b_claimed_week", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("a_id", "b_id", name="uq_friendship_pair"),
    )
    op.create_index("ix_friendships_a_id", "friendships", ["a_id"])
    op.create_index("ix_friendships_b_id", "friendships", ["b_id"])


def downgrade() -> None:
    op.drop_index("ix_friendships_b_id", table_name="friendships")
    op.drop_index("ix_friendships_a_id", table_name="friendships")
    op.drop_table("friendships")
