"""G4 · fun layer: gems + avatar shop, UI skin, league groups/tiers

Revision ID: t7c8d9e0f1a2
Revises: s6b7c8d9e0f1
Create Date: 2026-10-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "t7c8d9e0f1a2"
down_revision: Union[str, None] = "s6b7c8d9e0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Đá quý, avatar, vật phẩm đã mua, giao diện đã chọn
    op.add_column("learner_profiles", sa.Column("gems", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("learner_profiles", sa.Column("avatar", sa.JSON(), nullable=True))
    op.add_column("learner_profiles", sa.Column("owned_items", sa.JSON(), nullable=True))
    op.add_column("learner_profiles", sa.Column("ui_skin", sa.String(10), nullable=True))

    # Giải đấu tuần: nhóm 30 người theo hạng
    op.create_table(
        "league_memberships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("learner_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=False),
        sa.Column("week", sa.String(10), nullable=False),
        sa.Column("tier", sa.Integer(), nullable=False),
        sa.Column("group_no", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("learner_id", "week", name="uq_league_membership_learner_week"),
    )
    op.create_index("ix_league_memberships_learner_id", "league_memberships", ["learner_id"])
    op.create_index("ix_league_memberships_week", "league_memberships", ["week"])


def downgrade() -> None:
    op.drop_index("ix_league_memberships_week", table_name="league_memberships")
    op.drop_index("ix_league_memberships_learner_id", table_name="league_memberships")
    op.drop_table("league_memberships")
    op.drop_column("learner_profiles", "ui_skin")
    op.drop_column("learner_profiles", "owned_items")
    op.drop_column("learner_profiles", "avatar")
    op.drop_column("learner_profiles", "gems")
