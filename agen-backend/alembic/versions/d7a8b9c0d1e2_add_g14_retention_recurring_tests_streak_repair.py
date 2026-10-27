"""G14: signup source, monthly class tests, streak repair

Revision ID: d7a8b9c0d1e2
Revises: c6f7a8b9c0d1
Create Date: 2026-10-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d7a8b9c0d1e2"
down_revision: Union[str, None] = "c6f7a8b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("signup_source", sa.String(60), nullable=True))
    op.create_index("ix_users_signup_source", "users", ["signup_source"])

    with op.batch_alter_table("group_tests") as batch:
        batch.add_column(sa.Column("repeat", sa.String(10), nullable=True))
        batch.add_column(sa.Column("next_test_id", sa.String(36), nullable=True))

    with op.batch_alter_table("learner_profiles") as batch:
        batch.add_column(sa.Column("streak_lost_value", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("streak_lost_on", sa.String(10), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("learner_profiles") as batch:
        batch.drop_column("streak_lost_on")
        batch.drop_column("streak_lost_value")
    with op.batch_alter_table("group_tests") as batch:
        batch.drop_column("next_test_id")
        batch.drop_column("repeat")
    op.drop_index("ix_users_signup_source", table_name="users")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("signup_source")
