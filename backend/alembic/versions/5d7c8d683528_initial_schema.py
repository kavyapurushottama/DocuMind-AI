"""initial_schema

Revision ID: 5d7c8d683528
Revises: 
Create Date: 2026-11-14 20:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

revision: str = '5d7c8d683528'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    tables = inspector.get_table_names()

    # 1. users table
    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.UUID(), primary_key=True),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("hashed_password", sa.String(), nullable=False),
            sa.Column("full_name", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    # 2. workspaces table
    if "workspaces" not in tables:
        op.create_table(
            "workspaces",
            sa.Column("id", sa.UUID(), primary_key=True),
            sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_workspaces_user_id", "workspaces", ["user_id"])

    # 3. documents table
    if "documents" not in tables:
        op.create_table(
            "documents",
            sa.Column("id", sa.UUID(), primary_key=True),
            sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("filename", sa.String(), nullable=False),
            sa.Column("file_type", sa.String(), nullable=False),
            sa.Column("file_path", sa.String(), nullable=False),
            sa.Column("file_size_bytes", sa.Integer(), server_default="0", nullable=True),
            sa.Column("status", sa.String(), nullable=False, server_default="pending"),
            sa.Column("status_detail", sa.String(), nullable=True),
            sa.Column("error_message", sa.String(), nullable=True),
            sa.Column("workspace_id", sa.UUID(), sa.ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True),
            sa.Column("author", sa.String(), nullable=True),
            sa.Column("created_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("modified_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("tags", sa.String(), nullable=True),
            sa.Column("language", sa.String(), nullable=True),
            sa.Column("department", sa.String(), nullable=True),
            sa.Column("document_type", sa.String(), nullable=True),
            sa.Column("page_count", sa.Integer(), nullable=True),
            sa.Column("chunk_count", sa.Integer(), server_default="0", nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_documents_user_id", "documents", ["user_id"])
        op.create_index("ix_documents_workspace_id", "documents", ["workspace_id"])
    else:
        # Check for missing columns in existing documents table
        existing_cols = {c["name"] for c in inspector.get_columns("documents")}
        cols_to_add = [
            ("status_detail", sa.String()),
            ("workspace_id", sa.UUID()),
            ("author", sa.String()),
            ("created_date", sa.DateTime(timezone=True)),
            ("modified_date", sa.DateTime(timezone=True)),
            ("tags", sa.String()),
            ("language", sa.String()),
            ("department", sa.String()),
            ("document_type", sa.String()),
        ]
        for col_name, col_type in cols_to_add:
            if col_name not in existing_cols:
                op.add_column("documents", sa.Column(col_name, col_type, nullable=True))

    # 4. conversations table
    if "conversations" not in tables:
        op.create_table(
            "conversations",
            sa.Column("id", sa.UUID(), primary_key=True),
            sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("document_id", sa.UUID(), sa.ForeignKey("documents.id"), nullable=True),
            sa.Column("workspace_id", sa.UUID(), sa.ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True),
            sa.Column("title", sa.String(), server_default="New chat", nullable=True),
            sa.Column("is_pinned", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
        op.create_index("ix_conversations_workspace_id", "conversations", ["workspace_id"])
    else:
        conv_cols = {c["name"] for c in inspector.get_columns("conversations")}
        if "is_pinned" not in conv_cols:
            op.add_column("conversations", sa.Column("is_pinned", sa.Boolean(), server_default=sa.text("false"), nullable=False))
        if "workspace_id" not in conv_cols:
            op.add_column("conversations", sa.Column("workspace_id", sa.UUID(), nullable=True))

    # 5. messages table
    if "messages" not in tables:
        op.create_table(
            "messages",
            sa.Column("id", sa.UUID(), primary_key=True),
            sa.Column("conversation_id", sa.UUID(), sa.ForeignKey("conversations.id"), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("citations", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("documents")
    op.drop_table("workspaces")
    op.drop_table("users")
