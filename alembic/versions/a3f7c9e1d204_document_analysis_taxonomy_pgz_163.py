"""Document analysis model, taxonomy enums and verification traceability - PGZ-163

Revision ID: a3f7c9e1d204
Revises: 7191b37efe63
Create Date: 2026-10-24 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3f7c9e1d204"
down_revision: Union[str, Sequence[str], None] = "7191b37efe63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Widen type column to accommodate longer identifiers (e.g. amortization_table)
    op.alter_column("document", "type", type_=sa.String(40), existing_type=sa.String(20))

    # Set new default for category
    op.alter_column(
        "document",
        "category",
        server_default=sa.text("'UNCLASSIFIED'"),
        existing_type=sa.String(50),
    )

    # Backfill existing rows from legacy "pending" placeholder
    op.execute("UPDATE document SET category = 'UNCLASSIFIED' WHERE category = 'pending'")

    # Analysis pipeline columns
    op.add_column(
        "document",
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'not_analyzed'")),
    )
    op.add_column("document", sa.Column("detected_type", sa.String(40), nullable=True))
    op.add_column("document", sa.Column("review_reasons", sa.JSON(), nullable=True))
    op.add_column(
        "document",
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column("document", sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("document", sa.Column("model_version", sa.String(50), nullable=True))
    op.add_column("document", sa.Column("error_reason", sa.String(50), nullable=True))

    # Human-verification traceability
    op.add_column(
        "document",
        sa.Column("verified_by", sa.String(30), sa.ForeignKey("user.username"), nullable=True),
    )
    op.add_column("document", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Drop verification columns
    op.drop_column("document", "verified_at")
    op.drop_column("document", "verified_by")

    # Drop analysis pipeline columns
    op.drop_column("document", "error_reason")
    op.drop_column("document", "model_version")
    op.drop_column("document", "analyzed_at")
    op.drop_column("document", "attempts")
    op.drop_column("document", "review_reasons")
    op.drop_column("document", "detected_type")
    op.drop_column("document", "status")

    # Restore legacy category values
    op.execute("UPDATE document SET category = 'pending' WHERE category = 'UNCLASSIFIED'")
    op.alter_column("document", "category", server_default=None, existing_type=sa.String(50))

    # Truncate guard: prevent data loss when narrowing the column
    op.execute("UPDATE document SET type = LEFT(type, 20) WHERE LENGTH(type) > 20")
    op.alter_column("document", "type", type_=sa.String(20), existing_type=sa.String(40))
