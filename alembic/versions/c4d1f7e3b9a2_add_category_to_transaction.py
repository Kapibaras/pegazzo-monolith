"""add category to transaction table

Revision ID: c4d1f7e3b9a2
Revises: a1b2c3d4e5f6
Create Date: 2026-04-19 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4d1f7e3b9a2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add category column to transaction table. Existing records default to 'Otro'."""
    op.add_column(
        "transaction",
        sa.Column("category", sa.String(100), nullable=False, server_default="Otro"),
    )


def downgrade() -> None:
    """Remove category column from transaction table."""
    op.drop_column("transaction", "category")
