"""Create transaction_metrics table

Revision ID: 178f75115eae
Revises: ed43a39d3882
Create Date: 2026-01-19 14:28:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "178f75115eae"
down_revision: Union[str, Sequence[str], None] = "ed43a39d3882"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create transaction_metrics table and indexes."""
    op.create_table(
        "transaction_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("period_type", sa.String(length=10), nullable=False),
        sa.Column("week", sa.Integer(), nullable=True),
        sa.Column("month", sa.Integer(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("total_income", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("total_expense", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("balance", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("transaction_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "payment_method_breakdown",
            JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("weekly_average_income", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("weekly_average_expense", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("income_expense_ratio", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("period_type", "week", "month", "year", name="uq_transaction_metrics_period"),
    )

    op.create_index(
        "ix_transaction_metrics_period",
        "transaction_metrics",
        ["period_type", "year", "month", "week"],
    )

    op.create_index(
        "ix_transaction_metrics_payment_method_breakdown",
        "transaction_metrics",
        ["payment_method_breakdown"],
        postgresql_using="gin",
    )

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
    """Drop transaction_metrics table and indexes."""
    op.drop_index("uq_transaction_metrics_year", table_name="transaction_metrics")
    op.drop_index("uq_transaction_metrics_month", table_name="transaction_metrics")
    op.drop_index("uq_transaction_metrics_week", table_name="transaction_metrics")
    op.drop_index("ix_transaction_metrics_payment_method_breakdown", table_name="transaction_metrics")
    op.drop_index("ix_transaction_metrics_period", table_name="transaction_metrics")
    op.drop_table("transaction_metrics")
