"""G10: podcast progress, speaking club, teacher feedback, certificates, AI usage, Stripe currency

Revision ID: z3c4d5e6f7a8
Revises: y2b3c4d5e6f7
Create Date: 2026-10-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "z3c4d5e6f7a8"
down_revision: Union[str, None] = "y2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "media_progress",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("learner_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=False),
        sa.Column("episode_id", sa.String(40), nullable=False),
        sa.Column("best_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("last_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("learner_id", "episode_id", name="uq_media_progress"),
    )
    op.create_index("ix_media_progress_learner_id", "media_progress", ["learner_id"])

    op.create_table(
        "speaking_rooms",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(12), nullable=False),
        sa.Column("topic_id", sa.String(40), nullable=False),
        sa.Column("host_learner_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=False),
        sa.Column("status", sa.String(12), nullable=False, server_default="waiting"),
        sa.Column("is_public", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("question_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("turn_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("turns_taken", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_speaking_rooms_code", "speaking_rooms", ["code"], unique=True)
    op.create_index("ix_speaking_rooms_status", "speaking_rooms", ["status"])
    op.create_index("ix_speaking_rooms_created_at", "speaking_rooms", ["created_at"])

    op.create_table(
        "room_members",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("room_id", sa.String(36), sa.ForeignKey("speaking_rooms.id"), nullable=False),
        sa.Column("learner_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=False),
        sa.Column("turns", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("words", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("xp_earned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.Column("left_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("room_id", "learner_id", name="uq_room_member"),
    )
    op.create_index("ix_room_members_room_id", "room_members", ["room_id"])
    op.create_index("ix_room_members_learner_id", "room_members", ["learner_id"])

    op.create_table(
        "room_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("room_id", sa.String(36), sa.ForeignKey("speaking_rooms.id"), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("learner_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_room_messages_room_id", "room_messages", ["room_id"])

    op.create_table(
        "teacher_feedback",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("group_id", sa.String(36), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("teacher_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("learner_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=False),
        sa.Column("target_type", sa.String(20), nullable=False, server_default="general"),
        sa.Column("target_id", sa.String(36), nullable=True),
        sa.Column("target_label", sa.String(200), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_teacher_feedback_group_id", "teacher_feedback", ["group_id"])
    op.create_index("ix_teacher_feedback_learner_id", "teacher_feedback", ["learner_id"])
    op.create_index("ix_teacher_feedback_created_at", "teacher_feedback", ["created_at"])

    op.create_table(
        "certificates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(24), nullable=False),
        sa.Column("learner_id", sa.String(36), sa.ForeignKey("learner_profiles.id"), nullable=False),
        sa.Column("kind", sa.String(12), nullable=False),
        sa.Column("ref_id", sa.String(40), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("recipient_name", sa.String(120), nullable=False),
        sa.Column("issuer_name", sa.String(160), nullable=False),
        sa.Column("note", sa.String(300), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("issued_by_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_certificates_code", "certificates", ["code"], unique=True)
    op.create_index("ix_certificates_learner_id", "certificates", ["learner_id"])

    op.create_table(
        "ai_usage",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("feature", sa.String(60), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("model", sa.String(60), nullable=True),
        sa.Column("input_chars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_chars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_ai_usage_user_id", "ai_usage", ["user_id"])
    op.create_index("ix_ai_usage_feature", "ai_usage", ["feature"])
    op.create_index("ix_ai_usage_created_at", "ai_usage", ["created_at"])

    with op.batch_alter_table("payment_orders") as batch:
        batch.add_column(sa.Column("currency", sa.String(3), nullable=False, server_default="VND"))
        batch.add_column(sa.Column("amount_foreign", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("payment_orders") as batch:
        batch.drop_column("amount_foreign")
        batch.drop_column("currency")
    for ix, table in (("ix_ai_usage_created_at", "ai_usage"), ("ix_ai_usage_feature", "ai_usage"), ("ix_ai_usage_user_id", "ai_usage")):
        op.drop_index(ix, table_name=table)
    op.drop_table("ai_usage")
    op.drop_index("ix_certificates_learner_id", table_name="certificates")
    op.drop_index("ix_certificates_code", table_name="certificates")
    op.drop_table("certificates")
    for ix in ("ix_teacher_feedback_created_at", "ix_teacher_feedback_learner_id", "ix_teacher_feedback_group_id"):
        op.drop_index(ix, table_name="teacher_feedback")
    op.drop_table("teacher_feedback")
    op.drop_index("ix_room_messages_room_id", table_name="room_messages")
    op.drop_table("room_messages")
    op.drop_index("ix_room_members_learner_id", table_name="room_members")
    op.drop_index("ix_room_members_room_id", table_name="room_members")
    op.drop_table("room_members")
    for ix in ("ix_speaking_rooms_created_at", "ix_speaking_rooms_status", "ix_speaking_rooms_code"):
        op.drop_index(ix, table_name="speaking_rooms")
    op.drop_table("speaking_rooms")
    op.drop_index("ix_media_progress_learner_id", table_name="media_progress")
    op.drop_table("media_progress")
