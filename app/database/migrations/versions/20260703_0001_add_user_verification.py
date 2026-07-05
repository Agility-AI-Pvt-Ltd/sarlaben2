"""Add phone verification fields to users.

Revision ID: 20260703_0001
Revises: 20260702_0000
Create Date: 2026-07-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260703_0001"
down_revision: str | None = "20260702_0000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "farmers",
        "full_name",
        existing_type=sa.String(length=120),
        nullable=True,
    )
    op.add_column(
        "farmers",
        sa.Column(
            "is_phone_verified",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "farmers",
        sa.Column("phone_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "farmers",
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("farmers", "is_active")
    op.drop_column("farmers", "phone_verified_at")
    op.drop_column("farmers", "is_phone_verified")
    op.execute("UPDATE farmers SET full_name = '' WHERE full_name IS NULL")
    op.alter_column(
        "farmers",
        "full_name",
        existing_type=sa.String(length=120),
        nullable=False,
    )
