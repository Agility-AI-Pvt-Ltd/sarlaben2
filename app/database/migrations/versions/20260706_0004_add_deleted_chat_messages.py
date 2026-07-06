"""Add temporary archive for cleared chat messages.

Revision ID: 20260706_0004
Revises: 20260705_0003
Create Date: 2026-07-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260706_0004"
down_revision: str | None = "20260705_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "deleted_chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "original_message_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cattle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("farmer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("message_type", sa.String(length=16), nullable=False),
        sa.Column(
            "original_created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "original_updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("purge_after", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["cattle_id"],
            ["cattle.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["farmer_id"],
            ["farmers.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["chat_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_deleted_chat_messages_original_message_id",
        "deleted_chat_messages",
        ["original_message_id"],
    )
    op.create_index(
        "ix_deleted_chat_messages_session_id",
        "deleted_chat_messages",
        ["session_id"],
    )
    op.create_index(
        "ix_deleted_chat_messages_cattle_id",
        "deleted_chat_messages",
        ["cattle_id"],
    )
    op.create_index(
        "ix_deleted_chat_messages_farmer_id",
        "deleted_chat_messages",
        ["farmer_id"],
    )
    op.create_index(
        "ix_deleted_chat_messages_purge_after",
        "deleted_chat_messages",
        ["purge_after"],
    )


def downgrade() -> None:
    op.drop_table("deleted_chat_messages")
