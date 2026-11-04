"""Transactions are linked to cars by their string id (the internal folio), not by an integer."""

from datetime import UTC, datetime

from app.schemas.balance import TransactionResponseSchema


def _payload(**overrides):
    return {
        "amount": 100.0,
        "reference": "0014052011",
        "date": datetime.now(UTC),
        "type": "credit",
        "description": "Rent",
        "payment_method": "cash",
        "status": "CONFIRMED",
        **overrides,
    }


def test_transaction_response_accepts_string_car_id():
    schema = TransactionResponseSchema(**_payload(car_id="US-GDR-MZ2(TA)-07"))

    assert schema.car_id == "US-GDR-MZ2(TA)-07"


def test_transaction_response_car_id_is_optional():
    assert TransactionResponseSchema(**_payload()).car_id is None
