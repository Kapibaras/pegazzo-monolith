import pytest

from app.services.driver_folio import build_driver_folio, driver_initials


class TestDriverInitials:
    """First given name + first and second surname, always 3 uppercase ASCII letters."""

    @pytest.mark.parametrize(
        ("name", "surnames", "expected"),
        [
            ("Juan", "Pérez López", "JPL"),
            ("María José", "Núñez García", "MNG"),
            ("Ángel", "Ruiz", "ARU"),  # single surname -> 2nd letter of it
            ("Ana", "de la Cruz Torres", "ACT"),  # particles are ignored
            ("José", "Del Valle", "JVA"),
            ("  luis  ", "  garcía   lópez ", "LGL"),
            ("Íñigo", "Ñandú Ibáñez", "INI"),
            ("Li", "X", "LXX"),  # single 1-letter surname -> padded
            ("", "", "XXX"),
            ("Ana", "", "AXX"),
        ],
    )
    def test_initials(self, name, surnames, expected):
        assert driver_initials(name, surnames) == expected

    def test_always_three_ascii_letters(self):
        initials = driver_initials("Zoë-Ann", "O'Brien-Smith ñu")
        assert len(initials) == 3
        assert initials.isascii()
        assert initials.isalpha()
        assert initials.isupper()

    def test_only_particles_falls_back_to_original_words(self):
        assert driver_initials("De", "de la") == "DDL"


class TestBuildDriverFolio:
    """Folio composition: CD-{III}-{NNNN}."""

    def test_format_and_fixed_length(self):
        folio = build_driver_folio("Juan", "Pérez López", 7)
        assert folio == "CD-JPL-0007"
        assert len(folio) == 11

    def test_number_is_zero_padded_to_four_digits(self):
        assert build_driver_folio("Juan", "Pérez López", 1).endswith("-0001")
        assert build_driver_folio("Juan", "Pérez López", 9999).endswith("-9999")

    def test_number_grows_past_9999_and_still_fits_the_column(self):
        folio = build_driver_folio("Juan", "Pérez López", 12345)
        assert folio == "CD-JPL-12345"
        assert len(folio) <= 15
