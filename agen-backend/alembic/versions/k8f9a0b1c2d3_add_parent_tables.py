"""add parent profiles, parent-child links, user role, learner invite code

Revision ID: k8f9a0b1c2d3
Revises: j7e8f9a0b1c2
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "k8f9a0b1c2d3"
down_revision: Union[str, None] = "j7e8f9a0b1c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users.role ────────────────────────────────────────────────────────────
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("role", sa.String(length=20), nullable=False, server_default="learner"))

    # ── learner_profiles.invite_code ──────────────────────────────────────────
    with op.batch_alter_table("learner_profiles", schema=None) as batch_op:
        batch_op.add_column(sa.Column("invite_code", sa.String(length=20), nullable=True))
        batch_op.create_index("ix_learner_profiles_invite_code", ["invite_code"], unique=True)

    # ── parent_profiles ───────────────────────────────────────────────────────
    op.create_table(
        "parent_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    # ── parent_child_links ────────────────────────────────────────────────────
    op.create_table(
        "parent_child_links",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("parent_id", sa.String(length=36), nullable=False),
        sa.Column("learner_id", sa.String(length=36), nullable=False),
        sa.Column("relationship_label", sa.String(length=30), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["parent_profiles.id"]),
        sa.ForeignKeyConstraint(["learner_id"], ["learner_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_parent_child_links_parent_id", "parent_child_links", ["parent_id"])
    op.create_index("ix_parent_child_links_learner_id", "parent_child_links", ["learner_id"])


def downgrade() -> None:
    op.drop_index("ix_parent_child_links_learner_id", table_name="parent_child_links")
    op.drop_index("ix_parent_child_links_parent_id", table_name="parent_child_links")
    op.drop_table("parent_child_links")
    op.drop_table("parent_profiles")
    with op.batch_alter_table("learner_profiles", schema=None) as batch_op:
        batch_op.drop_index("ix_learner_profiles_invite_code")
        batch_op.drop_column("invite_code")
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("role")
