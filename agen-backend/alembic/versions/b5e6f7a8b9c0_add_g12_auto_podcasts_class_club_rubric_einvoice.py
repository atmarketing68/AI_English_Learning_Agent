"""G12: auto podcast drafts, weekly class speaking-club sessions, writing rubric, e-invoices

Revision ID: b5e6f7a8b9c0
Revises: a4d5e6f7a8b9
Create Date: 2026-10-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b5e6f7a8b9c0"
down_revision: Union[str, None] = "a4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("generated_episodes") as batch:
        batch.add_column(sa.Column("auto", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        "group_club_schedules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("group_id", sa.String(36), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("time_local", sa.String(5), nullable=False),
        sa.Column("topic_id", sa.String(40), nullable=True),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_group_club_schedules_group_id", "group_club_schedules", ["group_id"])

    with op.batch_alter_table("speaking_rooms") as batch:
        batch.alter_column("host_learner_id", existing_type=sa.String(36), nullable=True)
        batch.add_column(sa.Column("group_id", sa.String(36), sa.ForeignKey("groups.id", name="fk_speaking_rooms_group_id"), nullable=True))
        batch.add_column(sa.Column("schedule_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("group_reminded_at", sa.DateTime(), nullable=True))
    op.create_index("ix_speaking_rooms_group_id", "speaking_rooms", ["group_id"])
    op.create_index("ix_speaking_rooms_schedule_id", "speaking_rooms", ["schedule_id"])

    with op.batch_alter_table("writing_submissions") as batch:
        batch.add_column(sa.Column("teacher_rubric", sa.JSON(), nullable=True))

    with op.batch_alter_table("payment_orders") as batch:
        batch.add_column(sa.Column("einvoice_no", sa.String(40), nullable=True))
        batch.add_column(sa.Column("einvoice_lookup_code", sa.String(60), nullable=True))
        batch.add_column(sa.Column("einvoice_txn", sa.String(40), nullable=True))
        batch.add_column(sa.Column("einvoice_error", sa.String(300), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("payment_orders") as batch:
        for col in ("einvoice_error", "einvoice_txn", "einvoice_lookup_code", "einvoice_no"):
            batch.drop_column(col)
    with op.batch_alter_table("writing_submissions") as batch:
        batch.drop_column("teacher_rubric")
    op.drop_index("ix_speaking_rooms_schedule_id", table_name="speaking_rooms")
    op.drop_index("ix_speaking_rooms_group_id", table_name="speaking_rooms")
    with op.batch_alter_table("speaking_rooms") as batch:
        batch.drop_column("group_reminded_at")
        batch.drop_column("schedule_id")
        batch.drop_constraint("fk_speaking_rooms_group_id", type_="foreignkey")
        batch.drop_column("group_id")
        batch.alter_column("host_learner_id", existing_type=sa.String(36), nullable=False)
    op.drop_index("ix_group_club_schedules_group_id", table_name="group_club_schedules")
    op.drop_table("group_club_schedules")
    with op.batch_alter_table("generated_episodes") as batch:
        batch.drop_column("auto")
