from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.enum.balance import PaymentMethod, Type
from app.models.balance import Transaction
from app.models.transaction_metrics import TransactionMetrics
from app.services.transaction_metrics import update_metrics_for_transaction
from tests.unit.utils.test_errors_util import DatabaseError


def _make_tx(
    *,
    reference: str,
    dt: datetime,
    amount: str,
    tx_type: Type,
    payment_method: PaymentMethod,
) -> Transaction:
    """Create a Transaction instance for metrics tests."""
    mapped_type = "credit" if tx_type == Type.CREDIT else "debit"

    return Transaction(
        reference=reference,
        date=dt,
        amount=Decimal(amount),
        type=mapped_type,
        description="test",
        payment_method=payment_method.value,
    )


@pytest.fixture
def metrics_db_session():
    """Real Postgres session (Docker) used for transaction_metrics tests. This is required because we use JSONB + UPSERT + ON CONFLICT."""
    import os

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise DatabaseError

    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(bind=engine)

    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = testing_session_local()

    session.info["is_testing"] = True

    try:
        session.execute(text("TRUNCATE transaction_metrics RESTART IDENTITY CASCADE;"))
        session.execute(text('TRUNCATE "transaction" CASCADE;'))
        session.commit()

        yield session
    finally:
        session.rollback()
        session.close()


def test_week_metrics_not_duplicated_when_week_crosses_month(metrics_db_session):
    """Same ISO week across months must generate only one weekly metrics row."""
    s = metrics_db_session

    tx1 = _make_tx(
        reference="TESTW1",
        dt=datetime(2026, 1, 31, 12, 0, tzinfo=timezone.utc),
        amount="100.00",
        tx_type=Type.CREDIT,
        payment_method=PaymentMethod.CASH,
    )
    tx2 = _make_tx(
        reference="TESTW2",
        dt=datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc),
        amount="50.00",
        tx_type=Type.DEBIT,
        payment_method=PaymentMethod.CASH,
    )

    s.add_all([tx1, tx2])
    s.flush()

    update_metrics_for_transaction(s, transaction=tx1)
    update_metrics_for_transaction(s, transaction=tx2)
    s.commit()

    weekly_rows = s.execute(select(TransactionMetrics).where(TransactionMetrics.period_type == "week")).scalars().all()

    assert len(weekly_rows) == 1


def test_ratio_is_zero_when_expense_zero(metrics_db_session):
    """If total_expense == 0, income_expense_ratio must be 0."""
    s = metrics_db_session

    tx = _make_tx(
        reference="TESTR1",
        dt=datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc),
        amount="200.00",
        tx_type=Type.CREDIT,
        payment_method=PaymentMethod.CASH,
    )

    s.add(tx)
    s.flush()

    update_metrics_for_transaction(s, transaction=tx)
    s.commit()

    month_row = (
        s.execute(
            select(TransactionMetrics).where(
                TransactionMetrics.period_type == "month",
                TransactionMetrics.month == 1,
                TransactionMetrics.year == 2026,
            ),
        )
        .scalars()
        .one()
    )

    assert month_row.total_income == Decimal("200.00")
    assert month_row.total_expense == Decimal("0.00")
    assert month_row.income_expense_ratio == Decimal("0.00")


def test_payment_method_breakdown_amounts_and_percentages(metrics_db_session):
    """Breakdown must include amounts and percentages by payment method."""
    s = metrics_db_session

    tx1 = _make_tx(
        reference="TESTB1",
        dt=datetime(2026, 1, 12, 12, 0, tzinfo=timezone.utc),
        amount="100.00",
        tx_type=Type.CREDIT,
        payment_method=PaymentMethod.CASH,
    )
    tx2 = _make_tx(
        reference="TESTB2",
        dt=datetime(2026, 1, 13, 12, 0, tzinfo=timezone.utc),
        amount="300.00",
        tx_type=Type.CREDIT,
        payment_method=PaymentMethod.TRANSFER_PEGAZZO_ACCOUNT,
    )

    s.add_all([tx1, tx2])
    s.flush()

    update_metrics_for_transaction(s, transaction=tx1)
    update_metrics_for_transaction(s, transaction=tx2)
    s.commit()

    month_row = (
        s.execute(
            select(TransactionMetrics).where(
                TransactionMetrics.period_type == "month",
                TransactionMetrics.month == 1,
                TransactionMetrics.year == 2026,
            ),
        )
        .scalars()
        .one()
    )

    breakdown = month_row.payment_method_breakdown

    assert "amounts" in breakdown
    assert "percentages" in breakdown

    assert breakdown["amounts"][PaymentMethod.CASH.value] == 100.0
    assert breakdown["amounts"][PaymentMethod.TRANSFER_PEGAZZO_ACCOUNT.value] == 300.0

    assert breakdown["percentages"][PaymentMethod.CASH.value] == 25.0
    assert breakdown["percentages"][PaymentMethod.TRANSFER_PEGAZZO_ACCOUNT.value] == 75.0


def test_update_date_recalculates_old_and_new_periods(metrics_db_session):
    """If transaction date changes, metrics must recalc old and new periods."""
    s = metrics_db_session

    tx = _make_tx(
        reference="TESTU1",
        dt=datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc),
        amount="100.00",
        tx_type=Type.CREDIT,
        payment_method=PaymentMethod.CASH,
    )

    s.add(tx)
    s.flush()

    update_metrics_for_transaction(s, transaction=tx)
    s.commit()

    old_tx = Transaction(
        reference=tx.reference,
        date=datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc),
        amount=tx.amount,
        type=tx.type,
        description=tx.description,
        payment_method=tx.payment_method,
    )

    tx.date = datetime(2026, 2, 10, 12, 0, tzinfo=timezone.utc)
    s.flush()

    update_metrics_for_transaction(s, transaction=tx, old_transaction=old_tx)
    s.commit()

    jan_row = (
        s.execute(
            select(TransactionMetrics).where(
                TransactionMetrics.period_type == "month",
                TransactionMetrics.year == 2026,
                TransactionMetrics.month == 1,
            ),
        )
        .scalars()
        .one()
    )

    feb_row = (
        s.execute(
            select(TransactionMetrics).where(
                TransactionMetrics.period_type == "month",
                TransactionMetrics.year == 2026,
                TransactionMetrics.month == 2,
            ),
        )
        .scalars()
        .one()
    )

    assert jan_row.total_income == Decimal("0.00")
    assert feb_row.total_income == Decimal("100.00")


def test_delete_recalculates(metrics_db_session):
    """Deleting a transaction must recalculate metrics for the affected periods."""
    s = metrics_db_session

    tx1 = _make_tx(
        reference="TESTD1",
        dt=datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc),
        amount="80.00",
        tx_type=Type.CREDIT,
        payment_method=PaymentMethod.CASH,
    )
    tx2 = _make_tx(
        reference="TESTD2",
        dt=datetime(2026, 1, 11, 12, 0, tzinfo=timezone.utc),
        amount="30.00",
        tx_type=Type.DEBIT,
        payment_method=PaymentMethod.CASH,
    )

    s.add_all([tx1, tx2])
    s.flush()

    update_metrics_for_transaction(s, transaction=tx1)
    update_metrics_for_transaction(s, transaction=tx2)
    s.commit()

    s.delete(tx2)
    s.flush()

    update_metrics_for_transaction(s, transaction=tx2, old_transaction=tx2)
    s.commit()

    month_row = (
        s.execute(
            select(TransactionMetrics).where(
                TransactionMetrics.period_type == "month",
                TransactionMetrics.year == 2026,
                TransactionMetrics.month == 1,
            ),
        )
        .scalars()
        .one()
    )

    assert month_row.total_income == Decimal("80.00")
    assert month_row.total_expense == Decimal("0.00")
    assert month_row.balance == Decimal("80.00")
