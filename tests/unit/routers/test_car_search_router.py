"""Tests for PGZ-153 fuzzy car search: precedence rules, year filter, and sort_by=year."""

import pytest

from app.models.car import Car
from tests.mocks.car_repository_mock import CarRepositoryMock


def _make_car(car_id: str, make: str, model: str, year: str = "2022") -> Car:
    return Car(
        id=car_id,
        make=make,
        model=model,
        year=year,
        color="White",
        status="ACTIVE",
        vin=f"VIN{car_id}",
        plate=f"PLT-{car_id}",
        body_type="Sedan",
        engine_type="Gasoline",
        transmission="TA",
        engine_serial_number="ENG",
        odometer=0,
        doors_number=4,
        passengers_number=5,
        tire_specification="195/65R15",
        unit_value=200000,
        unit_billing_value=190000,
        bill_number="B1",
        public_vehicle_registry="R1",
        battery_model="BX",
        battery_serial_number="BS1",
        legal_owner_name="Juan",
        legal_owner_surnames="Perez",
        is_financed_liquidated=True,
        features={},
        details={},
        insurance_provider_id=1,
        policy_number="POL",
        policy_type="FULL",
    )


@pytest.mark.usefixtures("client")
class TestCarSearchPrecedence:
    """Verify the search precedence rules in the mock (mirrors production logic)."""

    def setup_method(self):
        self.repo = CarRepositoryMock()
        self.repo.cars = [
            _make_car("NIS-VR-001", "Nissan", "Versa", "2021"),
            _make_car("NIS-SN-001", "Nissan", "Sentra", "2022"),
            _make_car("NIS-MG-001", "Nissan", "Magnite", "2022"),
            _make_car("TOY-CR-001", "Toyota", "Corolla", "2021"),
            _make_car("TOY-YR-001", "Toyota", "Yaris", "2022"),
        ]

    # --- model takes priority over make ---

    def test_model_search_excludes_other_models_same_make(self):
        """Searching 'versa' returns only Versas, not other Nissan models."""
        result = self.repo._filter(None, "versa", None, False)
        assert all(c.model == "Versa" for c in result)
        assert len(result) == 1

    def test_model_search_with_make_prefix_still_model_only(self):
        """'nissan versa' returns only Versa, not Sentra or Magnite."""
        result = self.repo._filter(None, "nissan versa", None, False)
        assert len(result) == 1
        assert result[0].model == "Versa"

    def test_make_search_returns_all_models(self):
        """'nissan' alone returns all Nissan cars regardless of model."""
        result = self.repo._filter(None, "nissan", None, False)
        assert len(result) == 3
        assert all(c.make == "Nissan" for c in result)

    # --- exact id short-circuit ---

    def test_exact_id_match_returns_single_car(self):
        """An exact car ID returns only that car."""
        result = self.repo._filter(None, "NIS-VR-001", None, False)
        assert len(result) == 1
        assert result[0].id == "NIS-VR-001"

    def test_exact_id_case_insensitive(self):
        """ID match is case-insensitive."""
        result = self.repo._filter(None, "nis-vr-001", None, False)
        assert len(result) == 1
        assert result[0].id == "NIS-VR-001"

    # --- year filter ---

    def test_year_param_filters_results(self):
        """Explicit year param filters to that year only."""
        result = self.repo._filter(None, None, "2021", False)
        assert all(c.year == "2021" for c in result)
        assert len(result) == 2

    def test_year_token_in_search_text_is_extracted(self):
        """A 4-digit year in the search text is treated as a year filter."""
        result = self.repo._filter(None, "nissan 2021", None, False)
        assert all(c.make == "Nissan" and c.year == "2021" for c in result)
        assert len(result) == 1

    def test_explicit_year_overrides_text_year_token(self):
        """Explicit year= param wins over a year token in the search text."""
        result = self.repo._filter(None, "nissan 2021", "2022", False)
        assert all(c.year == "2022" for c in result)

    def test_model_plus_year_filters_correctly(self):
        """Model match + year returns only cars with that model AND year."""
        result = self.repo._filter(None, "corolla 2021", None, False)
        assert len(result) == 1
        assert result[0].model == "Corolla" and result[0].year == "2021"

    # --- no match ---

    def test_no_match_returns_empty(self):
        """A term that matches nothing returns an empty list."""
        result = self.repo._filter(None, "BMW", None, False)
        assert result == []

    # --- count / list delegates to _filter ---

    def test_count_cars_reflects_search(self):
        total = self.repo.count_cars(None, "nissan", None, False)
        assert total == 3

    def test_list_cars_sort_by_year_asc(self):
        from app.enum.balance import SortOrder
        from app.enum.crm import CarSortBy

        cars = self.repo.list_cars(None, "nissan", None, False, CarSortBy.YEAR, SortOrder.ASC, 10, 0)
        years = [c.year for c in cars]
        assert years == sorted(years)
