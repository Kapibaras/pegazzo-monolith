"""restore transaction_metrics table erroneously dropped

Revision ID: 7191b37efe63
Revises: 96e6f47e3c52
Create Date: 2026-08-27 12:18:47.984940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7191b37efe63'
down_revision: Union[str, Sequence[str], None] = '96e6f47e3c52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Restore transaction_metrics table that was erroneously dropped.

    Migration 96e6f47e3c52 dropped this table because TransactionMetrics
    was not exported in app/models/__init__.py, so alembic autogenerate
    treated it as orphaned. The table is actively used by balance endpoints.
    """
    op.create_table('transaction_metrics',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('period_type', sa.VARCHAR(length=10), autoincrement=False, nullable=False),
        sa.Column('week', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('month', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('year', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('total_income', sa.NUMERIC(precision=12, scale=2), server_default=sa.text("'0'::numeric"), autoincrement=False, nullable=False),
        sa.Column('total_expense', sa.NUMERIC(precision=12, scale=2), server_default=sa.text("'0'::numeric"), autoincrement=False, nullable=False),
        sa.Column('balance', sa.NUMERIC(precision=12, scale=2), server_default=sa.text("'0'::numeric"), autoincrement=False, nullable=False),
        sa.Column('transaction_count', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False),
        sa.Column('payment_method_breakdown', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), autoincrement=False, nullable=False),
        sa.Column('weekly_average_income', sa.NUMERIC(precision=12, scale=2), server_default=sa.text("'0'::numeric"), autoincrement=False, nullable=False),
        sa.Column('weekly_average_expense', sa.NUMERIC(precision=12, scale=2), server_default=sa.text("'0'::numeric"), autoincrement=False, nullable=False),
        sa.Column('income_expense_ratio', sa.NUMERIC(precision=10, scale=2), server_default=sa.text("'0'::numeric"), autoincrement=False, nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('transaction_metrics_pkey')),
        sa.UniqueConstraint('period_type', 'week', 'month', 'year', name=op.f('uq_transaction_metrics_period'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('uq_transaction_metrics_year'), 'transaction_metrics', ['year'], unique=True, postgresql_where="((period_type)::text = 'year'::text)")
    op.create_index(op.f('uq_transaction_metrics_week'), 'transaction_metrics', ['year', 'week'], unique=True, postgresql_where="((period_type)::text = 'week'::text)")
    op.create_index(op.f('uq_transaction_metrics_month'), 'transaction_metrics', ['year', 'month'], unique=True, postgresql_where="((period_type)::text = 'month'::text)")
    op.create_index(op.f('ix_transaction_metrics_period'), 'transaction_metrics', ['period_type', 'year', 'month', 'week'], unique=False)
    op.create_index(op.f('ix_transaction_metrics_payment_method_breakdown'), 'transaction_metrics', ['payment_method_breakdown'], unique=False, postgresql_using='gin')


def downgrade() -> None:
    """Drop transaction_metrics table."""
    op.drop_index(op.f('ix_transaction_metrics_payment_method_breakdown'), table_name='transaction_metrics', postgresql_using='gin')
    op.drop_index(op.f('ix_transaction_metrics_period'), table_name='transaction_metrics')
    op.drop_index(op.f('uq_transaction_metrics_month'), table_name='transaction_metrics', postgresql_where="((period_type)::text = 'month'::text)")
    op.drop_index(op.f('uq_transaction_metrics_week'), table_name='transaction_metrics', postgresql_where="((period_type)::text = 'week'::text)")
    op.drop_index(op.f('uq_transaction_metrics_year'), table_name='transaction_metrics', postgresql_where="((period_type)::text = 'year'::text)")
    op.drop_table('transaction_metrics')
