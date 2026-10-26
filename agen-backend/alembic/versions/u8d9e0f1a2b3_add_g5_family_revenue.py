"""G5 · family plan + conversion stats

Revision ID: u8d9e0f1a2b3
Revises: t7c8d9e0f1a2
Create Date: 2026-10-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "u8d9e0f1a2b3"
down_revision: Union[str, None] = "t7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Đơn thanh toán ghi gói: premium (học viên) | family (phụ huynh mua cho các con)
    op.add_column("payment_orders", sa.Column("plan", sa.String(20), nullable=False, server_default="premium"))
    # Khi khách lưu tài khoản (thống kê chuyển đổi học thử → đăng ký)
    op.add_column("users", sa.Column("claimed_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "claimed_at")
    op.drop_column("payment_orders", "plan")
