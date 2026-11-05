"""Seed dummy cars into the database to manually test update / archive / delete.

Usage:
    python -m scripts.seeds.cars clean      # Cars without history  -> update, status, archive, unarchive, HARD delete
    python -m scripts.seeds.cars history    # Cars with transactions -> SOFT delete
    python -m scripts.seeds.cars contract   # Car with active contract -> archive blocked (400)

Run `pipenv run seeders` first (needs the base associates). The script is idempotent:
existing cars (same id) are re-armed (archived/deleted markers cleared, status ACTIVE) so tests can be repeated.
"""

import sys
from datetime import UTC, datetime, timedelta

from app.database.session import SessionLocal
from app.models.balance import Transaction
from app.models.car import Associate, Car, Insurance
from app.models.contract import Contract
from app.models.driver import Driver
from app.utils.reference import PAYMENT_MAP, TYPE_MAP, calculate_mod11

ASSOCIATE_ID = 1
INSURANCE_NAME = "Seguro Demo"

SCENARIOS = {
    "clean": [
        {"id": "DEMO-CLEAN-01", "vin": "DEMOCLEAN0000001A", "plate": "DCL-001"},
        {"id": "DEMO-CLEAN-02", "vin": "DEMOCLEAN0000002B", "plate": "DCL-002"},
    ],
    "history": [
        {"id": "DEMO-HIST-01", "vin": "DEMOHIST00000001C", "plate": "DHI-001"},
    ],
    "contract": [
        {"id": "DEMO-CONTR-01", "vin": "DEMOCONTR0000001D", "plate": "DCO-001"},
    ],
}

DEMO_DRIVER_ID = "DEMO-DRIVER-01"
DEMO_CONTRACT_ID = "DEMO-CONTR-01"


def _get_or_create_insurance(db) -> Insurance:
    insurance = db.query(Insurance).filter_by(name=INSURANCE_NAME).first()
    if not insurance:
        insurance = Insurance(name=INSURANCE_NAME, telephones=["+52 55 0000 0003"])
        db.add(insurance)
        db.flush()
    return insurance


def _build_car(spec: dict, insurance: Insurance, associate: Associate) -> Car:
    now = datetime.now(UTC)
    car = Car(
        id=spec["id"],
        status="ACTIVE",
        make="Mazda",
        model="3",
        year="2024",
        color="Rojo",
        body_type="Sedan",
        engine_type="Gasolina",
        transmission="AT",
        vin=spec["vin"],
        engine_serial_number="ENG-DEMO-0001",
        plate=spec["plate"],
        odometer=15000,
        doors_number=4,
        passengers_number=5,
        unit_value=350000,
        unit_billing_value=350000,
        bill_number="BILL-DEMO-001",
        public_vehicle_registry="REG-DEMO-001",
        alta_public_vehicle_registry=now,
        tire_specification="205/55R16",
        features={},
        details={},
        legal_owner_name="Gaby",
        legal_owner_surnames="Flores",
        battery_model="BAT-DEMO",
        battery_serial_number="BAT-SN-0001",
        battery_date=now,
        policy_number="POL-DEMO-001",
        insurance_provider_id=insurance.id,
        policy_expiration_date=now + timedelta(days=365),
        policy_type="Amplia",
        is_financed_liquidated=True,
    )
    car.associate.append(associate)
    return car


def _add_transactions(db, car_id: str) -> int:
    """Link a few transactions to the car so it counts as having history."""
    now = datetime.now(UTC).replace(microsecond=0)
    specs = [("credit", "cash", 1500.00), ("debit", "personal_transfer", 320.50), ("debit", "pegazzo_transfer", 180.00)]
    for i, (tx_type, method, amount) in enumerate(specs, start=1):
        dt = now - timedelta(hours=i)
        base = f"{dt.strftime('%H%M%S')}{TYPE_MAP[tx_type]}{PAYMENT_MAP[method]}"
        db.add(
            Transaction(
                reference=f"{base}{calculate_mod11(base)}",
                date=dt,
                amount=amount,
                type=tx_type,
                description=f"Demo {tx_type} {car_id}",
                payment_method=method,
                car_id=car_id,
            ),
        )
    return len(specs)


def _add_active_contract(db, car_id: str) -> None:
    """Create a driver and a contract that is active today for the car."""
    now = datetime.now(UTC)
    if not db.query(Driver).filter_by(id=DEMO_DRIVER_ID).first():
        db.add(
            Driver(
                id=DEMO_DRIVER_ID,
                status="ACTIVE",
                name="Demo",
                surnames="Driver",
                telephones=["+52 55 0000 0004"],
                license_number="LIC-DEMO-001",
                license_validity=now + timedelta(days=365),
                identification_number="DEMO010101HDFXXX01",
                address="Calle Demo 123, Col. Centro, C.P. 06000, Cuauhtémoc, CDMX",
            ),
        )
        db.flush()
    if not db.query(Contract).filter_by(id=DEMO_CONTRACT_ID).first():
        today = now.date()
        db.add(
            Contract(
                id=DEMO_CONTRACT_ID,
                start_date=today - timedelta(days=30),
                end_date=today + timedelta(days=30),
                type="weekly",
                amount=3500,
                guarantee_amount=10000,
                car_id=car_id,
                driver_id=DEMO_DRIVER_ID,
            ),
        )


def seed_cars(scenario: str) -> None:
    """Insert the demo cars (and related rows) for the given scenario."""
    db = SessionLocal()
    created = []
    skipped = []

    try:
        associate = db.query(Associate).filter_by(id=ASSOCIATE_ID).first()
        if not associate:
            print("Associate 1 not found. Run `pipenv run seeders` first.")
            sys.exit(1)

        insurance = _get_or_create_insurance(db)
        extra = 0

        for spec in SCENARIOS[scenario]:
            existing = db.query(Car).filter_by(id=spec["id"]).first()
            if existing:
                existing.archived_at = None
                existing.deleted_at = None
                existing.status = "ACTIVE"
                skipped.append(spec)
                continue
            db.add(_build_car(spec, insurance, associate))
            db.flush()
            created.append(spec)

            if scenario == "history":
                extra += _add_transactions(db, spec["id"])
            elif scenario == "contract":
                _add_active_contract(db, spec["id"])

        db.commit()

        print(f"Scenario: {scenario}")
        for spec in created:
            print(f"  Created: id={spec['id']} vin={spec['vin']} plate={spec['plate']}")
        for spec in skipped:
            print(f"  Reset (already exists): id={spec['id']}")
        if scenario == "history":
            print(f"  Transactions linked: {extra}")
        if scenario == "contract" and created:
            print(f"  Active contract: {DEMO_CONTRACT_ID} (driver {DEMO_DRIVER_ID})")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in SCENARIOS:
        print("Usage: python -m scripts.seeds.cars <clean|history|contract>")
        sys.exit(1)

    seed_cars(sys.argv[1])
