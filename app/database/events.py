# TODO BACKGROUND TASKS TO REDIS
from __future__ import annotations

import logging
from copy import copy
from typing import Set, Tuple

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.models.balance import Transaction
from app.repositories.dto import PeriodKey
from app.repositories.transaction_metrics import TransactionMetricsRepository

logger = logging.getLogger(__name__)


@event.listens_for(Session, "after_flush")
def transaction_metrics_after_flush(session: Session, _flush_context: object) -> None:
    """Recalculate transaction metrics after flushing Transaction changes."""

    if session.info.get("_updating_metrics", False):
        return

    affected: Set[Tuple[Transaction, Transaction | None]] = set()

    for obj in session.new:
        if isinstance(obj, Transaction):
            affected.add((obj, None))

    for obj in session.dirty:
        if not isinstance(obj, Transaction):
            continue
        if not session.is_modified(obj, include_collections=False):
            continue

        insp = inspect(obj)

        old_tx: Transaction | None = None
        date_hist = insp.attrs.date.history
        if date_hist.has_changes() and date_hist.deleted:
            old_tx = copy(obj)
            old_tx.date = date_hist.deleted[0]

        affected.add((obj, old_tx))

    for obj in session.deleted:
        if isinstance(obj, Transaction):
            old = copy(obj)
            affected.add((old, old))

    if not affected:
        return

    affected_periods: Set[PeriodKey] = set()
    for tx, old_tx in affected:
        affected_periods.update(TransactionMetricsRepository.get_affected_periods(tx.date))
        if old_tx is not None:
            affected_periods.update(TransactionMetricsRepository.get_affected_periods(old_tx.date))

    logger.debug("Updating metrics for %d transactions (%d periods)", len(affected), len(affected_periods))

    session.info["_updating_metrics"] = True
    try:
        for key in affected_periods:
            TransactionMetricsRepository.recalc_period(
                session,
                period_type=key.period_type,
                year=key.year,
                month=key.month,
                week=key.week,
            )
    except Exception:
        logger.exception("Failed to recalculate transaction metrics")
        raise
    finally:
        session.info["_updating_metrics"] = False
