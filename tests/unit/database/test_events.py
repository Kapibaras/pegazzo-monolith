from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

from sqlalchemy.orm import Session

from app.database.events import transaction_metrics_after_flush
from app.models.balance import Transaction
from app.repositories.transaction_metrics import TransactionMetricsRepository
from app.schemas.dto.periods import PeriodKey


def make_tx(tx_dt: datetime, status: str = "CONFIRMED") -> Transaction:
    tx = Transaction()
    tx.date = tx_dt
    tx.status = status
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
@patch("app.database.events.get_affected_periods")
def test_new_transaction_does_not_trigger_recalc(
    mock_get_periods,
    mock_recalc_period,
):
    """New transactions are always PENDING — no metrics recalculation."""
    tx_dt = datetime(2026, 1, 10, 10, 0, 0, tzinfo=timezone.utc)
    tx = make_tx(tx_dt, status="PENDING")

    session = mock_session(new=[tx])

    transaction_metrics_after_flush(session, None)

    mock_get_periods.assert_not_called()
    mock_recalc_period.assert_not_called()


@patch.object(TransactionMetricsRepository, "recalc_period")
@patch("app.database.events.get_affected_periods")
def test_dirty_confirmed_transaction_with_date_change_triggers_old_and_new_periods(
    mock_get_periods,
    mock_recalc_period,
):
    """Editing a CONFIRMED transaction's date triggers recalc for both old and new periods."""
    old_dt = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    new_dt = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    tx = make_tx(new_dt, status="CONFIRMED")

    date_history = MagicMock()
    date_history.has_changes.return_value = True
    date_history.deleted = [old_dt]

    status_history = MagicMock()
    status_history.deleted = []

    insp = MagicMock()
    insp.attrs.date.history = date_history
    insp.attrs.status.history = status_history

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
@patch("app.database.events.get_affected_periods")
def test_dirty_pending_transaction_does_not_trigger_recalc(
    mock_get_periods,
    mock_recalc_period,
):
    """Editing a PENDING transaction does not trigger metrics recalculation."""
    tx = make_tx(datetime(2026, 1, 10, tzinfo=timezone.utc), status="PENDING")

    status_history = MagicMock()
    status_history.deleted = []

    insp = MagicMock()
    insp.attrs.date.history.has_changes.return_value = False
    insp.attrs.status.history = status_history

    with patch("app.database.events.inspect", return_value=insp):
        session = mock_session(dirty=[tx])
        transaction_metrics_after_flush(session, None)

    mock_get_periods.assert_not_called()
    mock_recalc_period.assert_not_called()


@patch.object(TransactionMetricsRepository, "recalc_period")
@patch("app.database.events.get_affected_periods")
def test_status_transition_to_confirmed_triggers_recalc(
    mock_get_periods,
    mock_recalc_period,
):
    """Transitioning a transaction to CONFIRMED triggers metrics recalculation."""
    tx_dt = datetime(2026, 3, 5, tzinfo=timezone.utc)
    tx = make_tx(tx_dt, status="CONFIRMED")

    date_history = MagicMock()
    date_history.has_changes.return_value = False

    status_history = MagicMock()
    status_history.deleted = ["PENDING"]  # old status was PENDING

    insp = MagicMock()
    insp.attrs.date.history = date_history
    insp.attrs.status.history = status_history

    mock_get_periods.return_value = {PeriodKey("month", 2026, 3, None)}

    with patch("app.database.events.inspect", return_value=insp):
        session = mock_session(dirty=[tx])
        transaction_metrics_after_flush(session, None)

    mock_get_periods.assert_called_once_with(tx_dt)
    mock_recalc_period.assert_called_once()


@patch.object(TransactionMetricsRepository, "recalc_period")
@patch("app.database.events.get_affected_periods")
def test_deleted_confirmed_transaction_triggers_recalc(
    mock_get_periods,
    mock_recalc_period,
):
    """Deleting a CONFIRMED transaction triggers metrics recalculation."""
    tx_dt = datetime(2026, 2, 5, 12, 0, 0, tzinfo=timezone.utc)
    tx = make_tx(tx_dt, status="CONFIRMED")

    mock_get_periods.return_value = {
        PeriodKey("month", 2026, 2, None),
    }

    session = mock_session(deleted=[tx])

    transaction_metrics_after_flush(session, None)

    mock_get_periods.assert_has_calls([call(tx_dt), call(tx_dt)])
    assert mock_get_periods.call_count == 2

    mock_recalc_period.assert_called_once()


@patch.object(TransactionMetricsRepository, "recalc_period")
@patch("app.database.events.get_affected_periods")
def test_deleted_pending_transaction_does_not_trigger_recalc(
    mock_get_periods,
    mock_recalc_period,
):
    """Deleting a PENDING transaction does NOT trigger metrics recalculation."""
    tx_dt = datetime(2026, 2, 5, 12, 0, 0, tzinfo=timezone.utc)
    tx = make_tx(tx_dt, status="PENDING")

    session = mock_session(deleted=[tx])

    transaction_metrics_after_flush(session, None)

    mock_get_periods.assert_not_called()
    mock_recalc_period.assert_not_called()


def test_does_nothing_when_flag_is_set():
    session = mock_session()
    session.info["_updating_metrics"] = True

    transaction_metrics_after_flush(session, None)

    assert session.is_modified.call_count == 0
