from __future__ import annotations

import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

# ✅ Fix: permite importar `app.*` cuando corres desde /scripts
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from sqlalchemy.orm import Session  # noqa: E402

from app.database.session import SessionLocal  # noqa: E402 (ajusta si tu factory tiene otro nombre)
from app.enum.balance import Type as TxType  # noqa: E402
from app.models.balance import Transaction  # noqa: E402
from app.models.transaction_metrics import TransactionMetrics  # noqa: E402


def utc_dt(y, m, d, hh=12, mm=0, ss=0) -> datetime:
    return datetime(y, m, d, hh, mm, ss, tzinfo=timezone.utc)


def create_tx(*, reference: str, tx_type: str, amount: str, payment_method: str, dt: datetime) -> Transaction:
    """
    Ajusta aquí si tu Transaction requiere más campos obligatorios.
    """
    tx = Transaction()
    tx.reference = reference
    tx.type = tx_type
    tx.amount = Decimal(amount)
    tx.payment_method = payment_method
    tx.date = dt
    return tx


def print_metrics(db: Session, *, period_type: str, year: int, month: int | None = None, week: int | None = None) -> None:
    q = db.query(TransactionMetrics).filter(
        TransactionMetrics.period_type == period_type,
        TransactionMetrics.year == year,
    )
    if month is not None:
        q = q.filter(TransactionMetrics.month == month)
    if week is not None:
        q = q.filter(TransactionMetrics.week == week)

    row = q.first()
    if not row:
        print("❌ No metrics row found for", period_type, year, month, week)
        return

    print("\n✅ METRICS FOUND")
    print("period:", row.period_type, "year:", row.year, "month:", row.month, "week:", row.week)
    print("total_income:", row.total_income)
    print("total_expense:", row.total_expense)
    print("balance:", row.balance)
    print("transaction_count:", row.transaction_count)
    print("income_expense_ratio:", row.income_expense_ratio)
    print("payment_method_breakdown:", row.payment_method_breakdown)
    print("updated_at:", row.updated_at)


def main() -> None:
    db = SessionLocal()
    created_refs: list[str] = []

    try:
        # 1) INSERT: 2 credits + 1 debit (mismo mes)
        txs = [
            create_tx(
                reference="manual-metrics-001",
                tx_type=TxType.CREDIT.value,
                amount="100.00",
                payment_method="cash",
                dt=utc_dt(2026, 1, 10),
            ),
            create_tx(
                reference="manual-metrics-002",
                tx_type=TxType.DEBIT.value,
                amount="40.00",
                payment_method="card",
                dt=utc_dt(2026, 1, 12),
            ),
            create_tx(
                reference="manual-metrics-003",
                tx_type=TxType.CREDIT.value,
                amount="60.00",
                payment_method="cash",
                dt=utc_dt(2026, 1, 20),
            ),
        ]

        for tx in txs:
            db.add(tx)
            created_refs.append(tx.reference)

        # ✅ Esto dispara after_flush -> recalcula métricas
        db.commit()

        # 2) CONSULTA métricas del mes Enero 2026
        print_metrics(db, period_type="month", year=2026, month=1)

        # 3) UPDATE: cambia fecha de una tx (para probar old+new period)
        tx_to_move = db.query(Transaction).filter(Transaction.reference == "manual-metrics-003").first()
        if tx_to_move:
            tx_to_move.date = utc_dt(2026, 2, 1)  # se mueve a Febrero
            db.commit()
            print("\n✅ After moving one tx to Feb 2026:")
            print_metrics(db, period_type="month", year=2026, month=1)
            print_metrics(db, period_type="month", year=2026, month=2)

        # 4) DELETE: borra una tx (probar delete path)
        tx_to_delete = db.query(Transaction).filter(Transaction.reference == "manual-metrics-002").first()
        if tx_to_delete:
            db.delete(tx_to_delete)
            db.commit()
            print("\n✅ After deleting one tx:")
            print_metrics(db, period_type="month", year=2026, month=1)

    finally:
        # Limpieza opcional (si NO quieres dejar basura en DB)
        # OJO: si tienes FK/constraints, ajusta como corresponda
        try:
            for ref in created_refs:
                tx = db.query(Transaction).filter(Transaction.reference == ref).first()
                if tx:
                    db.delete(tx)
            db.commit()
        except Exception:
            db.rollback()

        db.close()


if __name__ == "__main__":
    main()
