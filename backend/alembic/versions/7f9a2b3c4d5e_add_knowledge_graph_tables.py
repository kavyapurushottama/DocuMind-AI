"""add_knowledge_graph_tables

Revision ID: 7f9a2b3c4d5e
Revises: 6e8f1a2b3c4d
Create Date: 2026-11-17 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision: str = '7f9a2b3c4d5e'
down_revision: Union[str, None] = '6e8f1a2b3c4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "document_entities" not in tables:
        op.create_table(
            "document_entities",
            sa.Column("id", sa.UUID(), primary_key=True),
            sa.Column("document_id", sa.UUID(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("entity_key", sa.String(length=255), nullable=False),
            sa.Column("label", sa.String(length=255), nullable=False),
            sa.Column("category", sa.String(length=100), nullable=True),
            sa.Column("description", sa.String(length=1000), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_document_entities_document_id", "document_entities", ["document_id"])
        op.create_index("ix_document_entities_user_id", "document_entities", ["user_id"])
        op.create_index("ix_document_entities_entity_key", "document_entities", ["entity_key"])

    if "document_relationships" not in tables:
        op.create_table(
            "document_relationships",
            sa.Column("id", sa.UUID(), primary_key=True),
            sa.Column("document_id", sa.UUID(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("source_key", sa.String(length=255), nullable=False),
            sa.Column("target_key", sa.String(length=255), nullable=False),
            sa.Column("relation", sa.String(length=255), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=True, server_default="1.0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_document_relationships_document_id", "document_relationships", ["document_id"])
        op.create_index("ix_document_relationships_user_id", "document_relationships", ["user_id"])
        op.create_index("ix_document_relationships_source_key", "document_relationships", ["source_key"])
        op.create_index("ix_document_relationships_target_key", "document_relationships", ["target_key"])


def downgrade() -> None:
    op.drop_table("document_relationships")
    op.drop_table("document_entities")

