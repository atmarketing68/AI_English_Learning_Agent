"""merge application and agent trace migration heads

Revision ID: g4b5c6d7e8f9
Revises: c7e1a2b3d456, f3a9b8c7d6e5
"""
from typing import Sequence, Union


revision: str = "g4b5c6d7e8f9"
down_revision: Union[tuple[str, str], None] = ("c7e1a2b3d456", "f3a9b8c7d6e5")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
