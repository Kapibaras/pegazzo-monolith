from __future__ import annotations

from app.database.session import SessionLocal
from app.models.transaction_metrics import TransactionMetrics


def main(dry_run: bool = True) -> None:
    db = SessionLocal()
    try:
        total = db.query(TransactionMetrics).count()

        print("=== DELETE transaction_metrics ===")
        print(f"total rows found: {total}")
        print(f"dry_run: {dry_run}")

        if total == 0:
            print("ℹ️  No rows to delete.")
            return

        if dry_run:
            print("Dry-run only. No rows deleted.")
            return

        deleted = db.query(TransactionMetrics).delete(synchronize_session=False)
        db.commit()

        print(f"✅ Deleted {deleted} rows from transaction_metrics.")

    except Exception as e:
        db.rollback()
        print("❌ Deletion failed:", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # 1️⃣ Primero revisa cuántas rows hay
    main(dry_run=False)

    # 2️⃣ Cuando estés seguro, cambia a:
    # main(dry_run=False)
