from __future__ import annotations

from collections import Counter
from typing import Any

from app.database.session import SessionLocal  # ajusta si aplica
from app.models.transaction_metrics import TransactionMetrics


def classify_breakdown(bd: Any) -> str:
    """
    Clasifica el JSONB payment_method_breakdown:
    - old: tiene keys 'amounts'/'percentages' en top-level
    - new: tiene keys 'credit'/'debit' en top-level (opción B)
    - empty: None o {}
    - other: cualquier otra forma
    """
    if not bd:
        return "empty"

    if isinstance(bd, dict):
        if "credit" in bd or "debit" in bd:
            return "new"
        if "amounts" in bd or "percentages" in bd:
            return "old"
        return "other"

    # a veces SQLAlchemy retorna JSONB como objeto especial; intenta castear a dict
    try:
        d = dict(bd)
        if "credit" in d or "debit" in d:
            return "new"
        if "amounts" in d or "percentages" in d:
            return "old"
        return "other"
    except Exception:
        return "other"


def short_json(obj: Any, max_len: int = 240) -> str:
    s = str(obj)
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


def main():
    db = SessionLocal()
    try:
        # 1) Conteo global de formatos
        rows = db.query(TransactionMetrics).all()
        counts = Counter(classify_breakdown(r.payment_method_breakdown) for r in rows)

        print("\n=== payment_method_breakdown format counts ===")
        for k in ["new", "old", "empty", "other"]:
            print(f"{k:>5}: {counts.get(k, 0)}")
        print(f" total: {len(rows)}")

        # 2) Muestra últimos N registros para inspección rápida
        N = 15
        latest = db.query(TransactionMetrics).order_by(TransactionMetrics.updated_at.desc()).limit(N).all()

        print(f"\n=== latest {N} rows (by updated_at desc) ===")
        for r in latest:
            fmt = classify_breakdown(r.payment_method_breakdown)
            print(f"- id={r.id} period={r.period_type} y={r.year} m={r.month} w={r.week} fmt={fmt} updated_at={r.updated_at}")
            print(f"  breakdown={short_json(r.payment_method_breakdown)}")

        # 3) Si quieres ver “ejemplos concretos” de cada formato:
        def show_one(fmt: str):
            one = None
            for r in latest:
                if classify_breakdown(r.payment_method_breakdown) == fmt:
                    one = r
                    break
            if not one:
                one = (
                    db.query(TransactionMetrics)
                    .filter(TransactionMetrics.payment_method_breakdown.isnot(None))
                    .order_by(TransactionMetrics.updated_at.desc())
                    .all()
                )
                one = next((x for x in one if classify_breakdown(x.payment_method_breakdown) == fmt), None)

            print(f"\n=== example of {fmt} format ===")
            if not one:
                print("  (none found)")
                return
            print(f"  id={one.id} period={one.period_type} y={one.year} m={one.month} w={one.week} updated_at={one.updated_at}")
            print(f"  breakdown={one.payment_method_breakdown}")

        show_one("old")
        show_one("new")

    finally:
        db.close()


if __name__ == "__main__":
    main()
