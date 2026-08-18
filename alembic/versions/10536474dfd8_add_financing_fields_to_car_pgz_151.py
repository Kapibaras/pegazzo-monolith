"""Add financing fields to Car model - PGZ-151

Revision ID: 10536474dfd8
Revises: d1e2f3a4b5c6
Create Date: 2026-08-16 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "10536474dfd8"
down_revision: Union[str, None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old financed_status column
    op.drop_column("car", "financed_status")

    # Add is_financed_liquidated — NOT NULL, default false for existing rows
    op.add_column(
        "car",
        sa.Column(
            "is_financed_liquidated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    # Remove server_default after backfill so future rows must be explicit
    op.alter_column("car", "is_financed_liquidated", server_default=None)

    # Add nullable financing detail columns
    op.add_column("car", sa.Column("financing_agency", sa.String(100), nullable=True))
    op.add_column("car", sa.Column("financing_purchase_date", sa.Date(), nullable=True))
    op.add_column("car", sa.Column("financing_term_months", sa.Integer(), nullable=True))
    op.add_column("car", sa.Column("financing_remaining_amount", sa.Numeric(12, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("car", "financing_remaining_amount")
    op.drop_column("car", "financing_term_months")
    op.drop_column("car", "financing_purchase_date")
    op.drop_column("car", "financing_agency")
    op.drop_column("car", "is_financed_liquidated")

    op.add_column(
        "car",
        sa.Column(
            "financed_status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'UNKNOWN'"),
        ),
    )
    op.alter_column("car", "financed_status", server_default=None)
