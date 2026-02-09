from datetime import datetime, timezone
from decimal import Decimal

from app.database.session import SessionLocal  # ajusta si aplica
from app.enum.balance import Type as TxType
from app.models.balance import Transaction
from app.models.transaction_metrics import TransactionMetrics


def main():
    db = SessionLocal()

    try:
        # 1) Insertar una transacción (esto debe disparar metrics en after_flush)
        tx = Transaction(
            reference="manual-test-001",
            type=TxType.CREDIT.value,  # o TxType.CREDIT si tu modelo usa enum directo
            amount=Decimal("100.00"),
            payment_method="cash",  # ajusta a tu modelo
            date=datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc),
        )

        db.add(tx)

        # IMPORTANTE: el evento corre en flush (y commit hace flush)
        db.commit()

        # 2) Verifica que existe row en TransactionMetrics para enero 2026
        row = (
            db.query(TransactionMetrics)
            .filter(
                TransactionMetrics.period_type == "month",
                TransactionMetrics.year == 2026,
                TransactionMetrics.month == 1,
            )
            .first()
        )

        assert row is not None, "❌ No se creó/actualizó TransactionMetrics para enero 2026"
        print("✅ Event fired and metrics updated:", row.total_income, row.transaction_count)

    finally:
        # Limpieza opcional (si no quieres ensuciar tu DB)
        # db.delete(tx); db.commit()
        db.close()


if __name__ == "__main__":
    main()
