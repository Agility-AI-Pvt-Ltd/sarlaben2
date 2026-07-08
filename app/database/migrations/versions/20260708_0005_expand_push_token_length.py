"""Expand push token length for FCM.

Revision ID: 20260708_0005
Revises: 20260706_0004
Create Date: 2026-07-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260708_0005"
down_revision: str | None = "20260706_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "push_tokens",
        "expo_push_token",
        existing_type=sa.String(length=255),
        type_=sa.String(length=4096),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "push_tokens",
        "expo_push_token",
        existing_type=sa.String(length=4096),
        type_=sa.String(length=255),
        existing_nullable=False,
    )
