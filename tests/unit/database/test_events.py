from datetime import date
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.database.events import transaction_metrics_after_flush
from app.models.balance import Transaction
from app.repositories.dto import PeriodKey
from app.repositories.transaction_metrics import TransactionMetricsRepository


def make_tx(tx_date: date) -> Transaction:
    tx = Transaction()
    tx.date = tx_date
    return tx


def mock_session(*, new=None, dirty=None, deleted=None, is_modified=True) -> Session:
    session = MagicMock(spec=Session)
    session.new = new or []
    session.dirty = dirty or []
    session.deleted = deleted or []
    session.info = {}
    session.is_modified.return_value = is_modified
    return session


@patch.object(TransactionMetricsRepository, "recalc_period")
@patch.object(TransactionMetricsRepository, "get_affected_periods")
def test_new_transaction_triggers_recalc(
    mock_get_periods,
    mock_recalc_period,
):
    tx_date = date(2026, 1, 10)
    tx = make_tx(tx_date)

    mock_get_periods.return_value = {
        PeriodKey(period_type="month", year=2026, month=1, week=None),
    }

    session = mock_session(new=[tx])

    transaction_metrics_after_flush(session, None)

    mock_get_periods.assert_called_once_with(tx_date)
    mock_recalc_period.assert_called_once()


@patch.object(TransactionMetricsRepository, "recalc_period")
@patch.object(TransactionMetricsRepository, "get_affected_periods")
def test_dirty_transaction_with_date_change_triggers_old_and_new_periods(
    mock_get_periods,
    mock_recalc_period,
):
    old_date = date(2025, 12, 31)
    new_date = date(2026, 1, 1)

    tx = make_tx(new_date)

    history = MagicMock()
    history.has_changes.return_value = True
    history.deleted = [old_date]

    insp = MagicMock()
    insp.attrs.date.history = history

    with patch("app.database.events.inspect", return_value=insp):
        mock_get_periods.side_effect = [
            {PeriodKey("month", 2026, 1, None)},
            {PeriodKey("month", 2025, 12, None)},
        ]

        session = mock_session(dirty=[tx])

        transaction_metrics_after_flush(session, None)

    assert mock_get_periods.call_count == 2
    assert mock_recalc_period.call_count == 2


@patch.object(TransactionMetricsRepository, "recalc_period")
@patch.object(TransactionMetricsRepository, "get_affected_periods")
def test_deleted_transaction_triggers_recalc(
    mock_get_periods,
    mock_recalc_period,
):
    tx_date = date(2026, 2, 5)
    tx = make_tx(tx_date)

    mock_get_periods.return_value = {
        PeriodKey("month", 2026, 2, None),
    }

    session = mock_session(deleted=[tx])

    transaction_metrics_after_flush(session, None)

    mock_recalc_period.assert_called_once()


def test_does_nothing_when_flag_is_set():
    session = mock_session()
    session.info["_updating_metrics"] = True

    transaction_metrics_after_flush(session, None)

    assert session.is_modified.call_count == 0
