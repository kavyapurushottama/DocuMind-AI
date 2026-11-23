"""add_document_files

Revision ID: 6e8f1a2b3c4d
Revises: 5d7c8d683528
Create Date: 2026-11-16 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision: str = '6e8f1a2b3c4d'
down_revision: Union[str, None] = '5d7c8d683528'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "document_files" not in tables:
        op.create_table(
            "document_files",
            sa.Column("id", sa.UUID(), primary_key=True),
            sa.Column("document_id", sa.UUID(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("file_data", sa.LargeBinary(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_document_files_document_id", "document_files", ["document_id"], unique=True)


def downgrade() -> None:
    op.drop_table("document_files")

