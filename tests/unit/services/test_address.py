import pytest
from pydantic import ValidationError

from app.schemas.address import AddressFieldsSchema, format_address

_FIELDS = {
    "street": "Av. Reforma",
    "exterior_number": "100",
    "neighborhood": "Centro",
    "postal_code": "06000",
    "municipality": "Cuauhtémoc",
    "state": "CDMX",
}


class TestFormatAddress:
    """The fields are joined into the single text stored in the legacy `address` columns."""

    def test_without_interior_number(self):
        text = format_address(AddressFieldsSchema(**_FIELDS))
        assert text == "Av. Reforma 100, Col. Centro, C.P. 06000, Cuauhtémoc, CDMX"

    def test_with_interior_number(self):
        text = format_address(AddressFieldsSchema(**_FIELDS, interior_number="4B"))
        assert text == "Av. Reforma 100 Int. 4B, Col. Centro, C.P. 06000, Cuauhtémoc, CDMX"

    def test_blank_interior_number_is_ignored(self):
        text = format_address(AddressFieldsSchema(**_FIELDS, interior_number="   "))
        assert "Int." not in text

    def test_values_are_trimmed(self):
        text = format_address(AddressFieldsSchema(**{**_FIELDS, "street": "  Av. Reforma  "}))
        assert text.startswith("Av. Reforma 100,")

    def test_the_longest_possible_address_fits_the_255_character_columns(self):
        fields = AddressFieldsSchema(
            street="a" * 70,
            exterior_number="1" * 10,
            interior_number="2" * 10,
            neighborhood="b" * 50,
            postal_code="12345",
            municipality="c" * 40,
            state="d" * 30,
        )
        assert len(format_address(fields)) <= 255


class TestAddressValidation:
    """Postal code and required fields."""

    @pytest.mark.parametrize("postal_code", ["1234", "123456", "abcde", "12 45"])
    def test_postal_code_must_be_five_digits(self, postal_code):
        with pytest.raises(ValidationError):
            AddressFieldsSchema(**{**_FIELDS, "postal_code": postal_code})

    @pytest.mark.parametrize("field", ["street", "exterior_number", "neighborhood", "municipality", "state"])
    def test_blank_required_fields_are_rejected(self, field):
        with pytest.raises(ValidationError):
            AddressFieldsSchema(**{**_FIELDS, field: "  "})
