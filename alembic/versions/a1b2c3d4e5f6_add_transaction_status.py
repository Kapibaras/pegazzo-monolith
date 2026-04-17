"""add transaction status field

Revision ID: a1b2c3d4e5f6
Revises: 3c8e2f1a9d47
Create Date: 2026-04-10 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "3c8e2f1a9d47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add status column to transaction table. Existing records default to CONFIRMED."""
    op.add_column(
        "transaction",
        sa.Column("status", sa.String(10), nullable=False, server_default="PENDING"),
    )
    # Existing records were accepted before this workflow existed
    op.execute("UPDATE transaction SET status = 'CONFIRMED'")


def downgrade() -> None:
    """Remove status column from transaction table."""
    op.drop_column("transaction", "status")
