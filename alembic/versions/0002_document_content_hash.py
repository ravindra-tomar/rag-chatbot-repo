"""Add document content hashes for deduplication."""

from alembic import op
import sqlalchemy as sa


revision = "0002_document_content_hash"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("content_hash", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_documents_content_hash",
        "documents",
        ["content_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_documents_content_hash", table_name="documents")
    op.drop_column("documents", "content_hash")
