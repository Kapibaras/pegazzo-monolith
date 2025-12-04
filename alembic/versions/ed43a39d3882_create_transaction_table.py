"""create transaction table

Revision ID: ed43a39d3882
Revises: b95f9ea974b3
Create Date: 2025-11-29 12:51:41.272548
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ed43a39d3882"
down_revision: Union[str, Sequence[str], None] = "b95f9ea974b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create transaction table."""
    op.create_table(
        "transaction",
        sa.Column("reference", sa.String(length=50), primary_key=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("payment_method", sa.String(length=20), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema: drop transaction table."""
    op.drop_table("transaction")
