"""Add profile image URI to users.

Revision ID: 20260705_0002
Revises: 20260703_0001
Create Date: 2026-07-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260705_0002"
down_revision: str | None = "20260703_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "farmers",
        sa.Column("profile_image_uri", sa.String(length=2048), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("farmers", "profile_image_uri")
