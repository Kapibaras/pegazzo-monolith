from __future__ import annotations

from copy import copy
from typing import Set, Tuple

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.models.balance import Transaction
from app.services.transaction_metrics import update_metrics_for_transaction


@event.listens_for(Session, "after_flush")
def transaction_metrics_after_flush(session: Session, _flush_context: object) -> None:
    """Run inside the same DB transaction (atomic). Recalculate metrics when Transaction rows are inserted, updated, or deleted."""

    if session.info.get("is_testing", False):
        return

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

        old_tx = None
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

    session.info["_updating_metrics"] = True
    try:
        for tx, old_tx in affected:
            update_metrics_for_transaction(session, transaction=tx, old_transaction=old_tx)
    finally:
        session.info["_updating_metrics"] = False
