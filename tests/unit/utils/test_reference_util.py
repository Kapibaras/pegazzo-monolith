from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.utils.reference import PAYMENT_MAP, TYPE_MAP, calculate_mod11, generate_reference


def test_calculate_mod11_basic():
    """Test that Mod11 returns correct digit for a known value."""
    assert calculate_mod11("123456") == "0"


@pytest.mark.parametrize("value", ["006", "023", "037"])
def test_calculate_mod11_returns_x_when_10(value):
    assert calculate_mod11(value) == "X"


def test_generate_reference_structure():
    """Test that generated reference has correct structure and components."""

    fake_now = datetime(2025, 1, 1, 12, 34, 56, tzinfo=timezone.utc)

    with patch("app.utils.reference.datetime") as mock_datetime:
        mock_datetime.now.return_value = fake_now

        reference = generate_reference("cargo", "efectivo")

    assert reference.startswith("123456")
    assert reference[6] == TYPE_MAP["cargo"]
    assert reference[7:9] == PAYMENT_MAP["efectivo"]

    dv = reference[-1]
    assert len(reference) == 10

    base = reference[:-1]
    assert dv == calculate_mod11(base)


def test_generate_reference_different_maps():
    """Test reference generation with other valid type/payment combinations."""

    fake_now = datetime(2025, 1, 1, 10, 0, 30, tzinfo=timezone.utc)

    with patch("app.utils.reference.datetime") as mock_datetime:
        mock_datetime.now.return_value = fake_now

        reference = generate_reference("abono", "transferencia pegazzo")

    assert reference.startswith("100030")
    assert reference[6] == TYPE_MAP["abono"]
    assert reference[7:9] == PAYMENT_MAP["transferencia pegazzo"]
    assert reference[-1] == calculate_mod11(reference[:-1])


def test_generate_reference_invalid_type():
    """Should raise KeyError if type is not found in TYPE_MAP."""
    with patch("app.utils.reference.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime.now(timezone.utc)

        with pytest.raises(KeyError):
            generate_reference("invalido", "efectivo")


def test_generate_reference_invalid_payment_method():
    """Should raise KeyError if payment method not in PAYMENT_MAP."""
    with patch("app.utils.reference.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime.now(timezone.utc)

        with pytest.raises(KeyError):
            generate_reference("cargo", "nopago")
