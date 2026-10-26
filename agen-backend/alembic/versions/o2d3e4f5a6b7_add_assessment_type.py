"""add assessment type to placement sessions

Revision ID: o2d3e4f5a6b7
Revises: n1c2d3e4f5a6
Create Date: 2026-09-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "o2d3e4f5a6b7"
down_revision: Union[str, None] = "n1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "placement_sessions",
        sa.Column("assessment_type", sa.String(20), nullable=False, server_default="baseline"),
    )
    op.alter_column("placement_sessions", "assessment_type", server_default=None)


def downgrade() -> None:
    op.drop_column("placement_sessions", "assessment_type")