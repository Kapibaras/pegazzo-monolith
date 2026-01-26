from __future__ import annotations

from sqlalchemy import Column, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.database.base import Base


class TransactionMetrics(Base):
    """Pre-calculated transaction metrics per period."""

    __tablename__ = "transaction_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)

    period_type = Column(String(10), nullable=False)
    week = Column(Integer, nullable=True)
    month = Column(Integer, nullable=True)
    year = Column(Integer, nullable=False)

    total_income = Column(Numeric(12, 2), nullable=False, server_default="0")
    total_expense = Column(Numeric(12, 2), nullable=False, server_default="0")
    balance = Column(Numeric(12, 2), nullable=False, server_default="0")

    transaction_count = Column(Integer, nullable=False, server_default="0")

    payment_method_breakdown = Column(
        JSONB,
        nullable=False,
        server_default=func.cast("{}", JSONB),
    )

    weekly_average_income = Column(Numeric(12, 2), nullable=False, server_default="0")
    weekly_average_expense = Column(Numeric(12, 2), nullable=False, server_default="0")

    income_expense_ratio = Column(Numeric(10, 2), nullable=False, server_default="0")

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("period_type", "week", "month", "year", name="uq_transaction_metrics_period"),
        Index("ix_transaction_metrics_period", "period_type", "year", "month", "week"),
        Index(
            "ix_transaction_metrics_payment_method_breakdown",
            "payment_method_breakdown",
            postgresql_using="gin",
        ),
        Index(
            "uq_transaction_metrics_week",
            "year",
            "week",
            unique=True,
            postgresql_where=(period_type == "week"),
        ),
        Index(
            "uq_transaction_metrics_month",
            "year",
            "month",
            unique=True,
            postgresql_where=(period_type == "month"),
        ),
        Index(
            "uq_transaction_metrics_year",
            "year",
            unique=True,
            postgresql_where=(period_type == "year"),
        ),
    )
