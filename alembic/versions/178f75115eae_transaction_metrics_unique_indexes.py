"""fix transaction_metrics unique indexes

Revision ID: 6e0b86803f0b
Revises: ed43a39d3882
Create Date: 2026-01-19 14:10:46.268218
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "6e0b86803f0b"
down_revision: Union[str, Sequence[str], None] = "ed43a39d3882"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_index(
        "uq_transaction_metrics_week",
        "transaction_metrics",
        ["year", "week"],
        unique=True,
        postgresql_where=sa.text("period_type = 'week'"),
    )
    op.create_index(
        "uq_transaction_metrics_month",
        "transaction_metrics",
        ["year", "month"],
        unique=True,
        postgresql_where=sa.text("period_type = 'month'"),
    )
    op.create_index(
        "uq_transaction_metrics_year",
        "transaction_metrics",
        ["year"],
        unique=True,
        postgresql_where=sa.text("period_type = 'year'"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_transaction_metrics_year", table_name="transaction_metrics")
    op.drop_index("uq_transaction_metrics_month", table_name="transaction_metrics")
    op.drop_index("uq_transaction_metrics_week", table_name="transaction_metrics")
