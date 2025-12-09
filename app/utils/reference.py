from datetime import datetime, timezone

TYPE_MAP = {
    "debit": "1",
    "credit": "2",
}

PAYMENT_MAP = {
    "cash": "01",
    "personal_transfer": "02",
    "pegazzo_transfer": "03",
}


def calculate_mod11(numbers: str) -> str:
    """Calculate a Mod11 check digit.

    Uses repeating weights from 2 to 7 and returns 'X' when the result equals 10.
    """

    weights = [2, 3, 4, 5, 6, 7]
    total = 0
    reversed_digits = numbers[::-1]

    for idx, digit in enumerate(reversed_digits):
        total += int(digit) * weights[idx % len(weights)]

    remainder = total % 11
    check_digit = (11 - remainder) % 11

    if check_digit == 10:
        return "X"
    return str(check_digit)


def generate_reference(type_value: str, payment_method: str) -> str:
    """Generate a payment reference.

    The reference uses the pattern:
    `[HHMMSS][TYPE][PAYMENT][DV]`, where DV is a Mod11 check digit.
    """

    now = datetime.now(timezone.utc)

    time_part = now.strftime("%H%M%S")
    type_digit = TYPE_MAP[type_value]
    payment_digit = PAYMENT_MAP[payment_method]

    base = f"{time_part}{type_digit}{payment_digit}"
    dv = calculate_mod11(base)

    return f"{base}{dv}"
