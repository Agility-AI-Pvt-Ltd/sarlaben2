"""Create the initial application schema.

Revision ID: 20260702_0000
Revises:
Create Date: 2026-07-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260702_0000"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _common_columns() -> tuple[sa.Column, sa.Column, sa.Column]:
    return (
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def upgrade() -> None:
    op.create_table(
        "farmers",
        *_common_columns(),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("preferred_language", sa.String(length=16), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone_number"),
    )
    op.create_table(
        "cattle",
        *_common_columns(),
        sa.Column("farmer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cattle_tag", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("breed", sa.String(length=120), nullable=True),
        sa.Column("sex", sa.String(length=24), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["farmer_id"],
            ["farmers.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cattle_tag"),
    )
    op.create_index("ix_cattle_cattle_tag", "cattle", ["cattle_tag"])
    op.create_index("ix_cattle_farmer_id", "cattle", ["farmer_id"])

    op.create_table(
        "chat_sessions",
        *_common_columns(),
        sa.Column("cattle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("farmer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["cattle_id"], ["cattle.id"]),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_sessions_cattle_id", "chat_sessions", ["cattle_id"])
    op.create_index("ix_chat_sessions_farmer_id", "chat_sessions", ["farmer_id"])

    op.create_table(
        "chat_messages",
        *_common_columns(),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cattle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("farmer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("message_type", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(["cattle_id"], ["cattle.id"]),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_messages_cattle_id", "chat_messages", ["cattle_id"])
    op.create_index("ix_chat_messages_farmer_id", "chat_messages", ["farmer_id"])
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])

    op.create_table(
        "cattle_memories",
        *_common_columns(),
        sa.Column("cattle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "source_message_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("cattle_data_text", sa.Text(), nullable=False),
        sa.Column("data_type_stored_by_ai", sa.String(length=48), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["cattle_id"], ["cattle.id"]),
        sa.ForeignKeyConstraint(["source_message_id"], ["chat_messages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cattle_memories_cattle_id",
        "cattle_memories",
        ["cattle_id"],
    )

    op.create_table(
        "call_logs",
        *_common_columns(),
        sa.Column("cattle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("farmer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("call_logs", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["cattle_id"], ["cattle.id"]),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_call_logs_cattle_id", "call_logs", ["cattle_id"])
    op.create_index("ix_call_logs_farmer_id", "call_logs", ["farmer_id"])


def downgrade() -> None:
    op.drop_table("call_logs")
    op.drop_table("cattle_memories")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("cattle")
    op.drop_table("farmers")
