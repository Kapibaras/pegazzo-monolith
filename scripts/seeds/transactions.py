"""Seed dummy transactions into the database.

Usage:
    python -m scripts.seeds.transactions income    # More income than expenses
    python -m scripts.seeds.transactions expense   # More expenses than income
"""

import random
import sys
from datetime import UTC, datetime, timedelta

from app.database.session import SessionLocal
from app.models.balance import Transaction
from app.utils.reference import PAYMENT_MAP, TYPE_MAP, calculate_mod11

PAYMENT_METHODS = ["cash", "personal_transfer", "pegazzo_transfer"]

CREDIT_TEMPLATES = [
    "Pago viaje aeropuerto cliente VIP",
    "Servicio de traslado corporativo",
    "Viaje zona norte",
    "Servicio express centro historico",
    "Contrato semanal empresa logistica",
    "Viaje nocturno zona sur",
    "Traslado aeropuerto - ida y vuelta",
    "Servicio medio dia zona industrial",
    "Pago quincenal contrato corporativo",
    "Viaje especial fin de semana",
    "Servicio paqueteria urgente",
    "Viaje largo carretera interestatal",
    "Servicio nocturno premium",
    "Viaje corto zona centro",
    "Traslado ejecutivo",
    "Pago fin de mes contrato corporativo",
    "Viaje zona residencial",
    "Servicio corporativo medio dia",
    "Viaje aeropuerto terminal 2",
    "Traslado evento empresarial",
    "Servicio dominical zona turistica",
    "Contrato semanal empresa tech",
    "Viaje largo zona metropolitana",
    "Traslado madrugada aeropuerto",
    "Viaje matutino zona norte",
]

DEBIT_TEMPLATES = [
    "Carga de gasolina",
    "Lavado y detallado del vehiculo",
    "Estacionamiento mensual",
    "Servicio mecanico - cambio de aceite y filtros",
    "Peaje y casetas autopista",
    "Pago seguro vehicular mensual",
    "Compra de agua y suministros",
    "Reparacion de frenos y suspension",
    "Cambio de llantas y alineacion",
    "Lavado express del vehiculo",
    "Peaje autopista del sol",
    "Decoracion vehiculo servicio especial",
    "Mantenimiento preventivo general",
    "Recarga de aire acondicionado",
    "Multa de transito",
]

TOTAL_TRANSACTIONS = 45

# Proportions: ~60/40 base split, shifted by scenario
SCENARIO_CONFIG = {
    "income": {"credit_ratio": 0.70, "credit_range": (800, 4500), "debit_range": (90, 600)},
    "expense": {"credit_ratio": 0.35, "credit_range": (400, 1500), "debit_range": (500, 4500)},
}


def _random_date_last_month():
    """Generate a random datetime between now and 30 days ago."""
    now = datetime.now(UTC)
    offset = random.randint(0, 30 * 24 * 60 * 60)  # seconds in ~30 days
    return (now - timedelta(seconds=offset)).replace(microsecond=0)


def _generate_reference(tx_type: str, payment_method: str, dt: datetime) -> str:
    """Generate a reference using the transaction's own datetime as the time component."""
    base = f"{dt.strftime('%H%M%S')}{TYPE_MAP[tx_type]}{PAYMENT_MAP[payment_method]}"
    return f"{base}{calculate_mod11(base)}"


def _build_transactions(scenario):
    config = SCENARIO_CONFIG[scenario]
    credit_count = round(TOTAL_TRANSACTIONS * config["credit_ratio"])
    debit_count = TOTAL_TRANSACTIONS - credit_count

    transactions = []

    transactions.extend(
        {
            "type": "credit",
            "amount": round(random.uniform(*config["credit_range"]), 2),
            "description": random.choice(CREDIT_TEMPLATES),
            "payment_method": random.choice(PAYMENT_METHODS),
            "date": _random_date_last_month(),
        }
        for _ in range(credit_count)
    )

    transactions.extend(
        {
            "type": "debit",
            "amount": round(random.uniform(*config["debit_range"]), 2),
            "description": random.choice(DEBIT_TEMPLATES),
            "payment_method": random.choice(PAYMENT_METHODS),
            "date": _random_date_last_month(),
        }
        for _ in range(debit_count)
    )

    random.shuffle(transactions)
    return transactions


def seed_transactions(scenario):
    transactions = _build_transactions(scenario)
    db = SessionLocal()
    inserted = 0

    try:
        for tx_data in transactions:
            tx = Transaction(
                reference=_generate_reference(tx_data["type"], tx_data["payment_method"], tx_data["date"]),
                date=tx_data["date"],
                amount=tx_data["amount"],
                type=tx_data["type"],
                description=tx_data["description"],
                payment_method=tx_data["payment_method"],
            )
            db.add(tx)
            inserted += 1

        db.commit()

        credit_txs = [t for t in transactions if t["type"] == "credit"]
        debit_txs = [t for t in transactions if t["type"] == "debit"]
        total_credit = sum(t["amount"] for t in credit_txs)
        total_debit = sum(t["amount"] for t in debit_txs)

        print(f"Scenario: {scenario}")
        print(f"Inserted {inserted} transactions.")
        print(f"  Credits: {len(credit_txs)} (${total_credit:,.2f})")
        print(f"  Debits:  {len(debit_txs)} (${total_debit:,.2f})")
        print(f"  Balance: ${total_credit - total_debit:,.2f}")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in SCENARIO_CONFIG:
        print("Usage: python -m scripts.seeds.transactions <income|expense>")
        sys.exit(1)

    seed_transactions(sys.argv[1])
