import pytest

from app.errors.car import AssociateNotFoundException, CarModelNotFoundException
from app.models.car import Associate
from app.models.car_model import CarModel
from app.schemas.car_folio import CarFolioRequestSchema
from app.services.car_folio import CarFolioService, _associate_initials, _owner_prefix
from tests.mocks.car_model_repository_mock import CarModelRepositoryMock
from tests.mocks.car_repository_mock import CarRepositoryMock

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_associate(associate_id: int, name: str, surnames: str) -> Associate:
    return Associate(id=associate_id, name=name, surnames=surnames, telephones=[])


def _make_car_model(make: str, model: str, abbreviation: str) -> CarModel:
    return CarModel(id=1, make=make, model=model, abbreviation=abbreviation)


def _make_service(car_repo: CarRepositoryMock, car_model_repo: CarModelRepositoryMock) -> CarFolioService:
    return CarFolioService(car_repo, car_model_repo)


def _request(
    associate_id: int = 1,
    legal_owner_is_pegazzo: bool = False,
    make: str = "Mazda",
    model: str = "2",
    transmission: str = "TA",
) -> CarFolioRequestSchema:
    return CarFolioRequestSchema(
        associateId=associate_id,
        legalOwnerIsPegazzo=legal_owner_is_pegazzo,
        make=make,
        model=model,
        transmission=transmission,
    )


# ---------------------------------------------------------------------------
# Unit tests — _owner_prefix
# ---------------------------------------------------------------------------

class TestOwnerPrefix:
    """Tests for the _owner_prefix helper function."""

    def test_legal_owner_is_pegazzo_returns_pg(self):
        assert _owner_prefix(is_us_owner=False, legal_owner_is_pegazzo=True) == "PG"

    def test_legal_owner_is_pegazzo_overrides_us_owner(self):
        assert _owner_prefix(is_us_owner=True, legal_owner_is_pegazzo=True) == "PG"

    def test_us_owner_returns_us(self):
        assert _owner_prefix(is_us_owner=True, legal_owner_is_pegazzo=False) == "US"

    def test_regular_associate_returns_s(self):
        assert _owner_prefix(is_us_owner=False, legal_owner_is_pegazzo=False) == "S"


# ---------------------------------------------------------------------------
# Unit tests — _associate_initials
# ---------------------------------------------------------------------------

class TestAssociateInitials:
    """Tests for the _associate_initials helper function."""

    def test_standard_two_surnames(self):
        assert _associate_initials("Gabriela Lizeth", "Duran Rios") == "GDR"

    def test_single_given_name_two_surnames(self):
        assert _associate_initials("Juan", "Perez Garcia") == "JPG"

    def test_single_surname(self):
        assert _associate_initials("Juan", "Perez") == "JP"

    def test_uppercase_normalization(self):
        assert _associate_initials("ana", "torres ramos") == "ATR"

    def test_only_first_given_name_used(self):
        assert _associate_initials("Maria Jose", "Lopez Cruz") == "MLC"


# ---------------------------------------------------------------------------
# Unit tests — CarFolioService.compute_folio
# ---------------------------------------------------------------------------

class TestCarFolioService:
    """Integration tests for CarFolioService.compute_folio."""

    def setup_method(self):
        self.car_repo = CarRepositoryMock()
        self.car_model_repo = CarModelRepositoryMock()
        self.service = _make_service(self.car_repo, self.car_model_repo)

    def _add_associate(self, associate_id: int = 1, name: str = "Juan", surnames: str = "Perez Garcia"):
        associate = _make_associate(associate_id, name, surnames)
        self.car_repo.associates = [a for a in self.car_repo.associates if a.id != associate_id]
        self.car_repo.associates.append(associate)
        return associate

    def _add_car_model(self, make: str = "Mazda", model: str = "2", abbreviation: str = "MZ2"):
        cm = _make_car_model(make, model, abbreviation)
        self.car_model_repo.car_models.append(cm)
        return cm

    # --- happy path ---

    def test_regular_associate_folio(self):
        self._add_associate(name="Juan", surnames="Perez Garcia")
        self._add_car_model()
        result = self.service.compute_folio(_request())
        assert result.folio == "S-JPG-MZ2(TA)-01"

    def test_us_owner_folio(self):
        self._add_associate(name="Gabriela", surnames="Duran Rios")
        self.car_repo.us_associate_ids.add(1)
        self._add_car_model()
        result = self.service.compute_folio(_request())
        assert result.folio == "US-GDR-MZ2(TA)-01"

    def test_legal_owner_is_pegazzo_folio(self):
        self._add_associate(name="Juan", surnames="Perez Garcia")
        self._add_car_model()
        result = self.service.compute_folio(_request(legal_owner_is_pegazzo=True))
        assert result.folio == "PG-JPG-MZ2(TA)-01"

    def test_legal_owner_is_pegazzo_overrides_us_owner(self):
        self._add_associate(name="Gabriela", surnames="Duran Rios")
        self.car_repo.us_associate_ids.add(1)
        self._add_car_model()
        result = self.service.compute_folio(_request(legal_owner_is_pegazzo=True))
        assert result.folio.startswith("PG-")

    def test_transmission_tm(self):
        self._add_associate()
        self._add_car_model()
        result = self.service.compute_folio(_request(transmission="TM"))
        assert "(TM)" in result.folio

    # --- consecutive ---

    def test_consecutive_starts_at_01_when_no_cars(self):
        self._add_associate()
        self._add_car_model()
        result = self.service.compute_folio(_request())
        assert result.folio.endswith("-01")

    def test_consecutive_increments_with_existing_cars(self):
        associate = self._add_associate()
        self._add_car_model()
        from app.models.car import Car
        for i in range(2):
            car = Car(
                id=f"CAR-00{i}",
                make="Mazda", model="2", year="2022", color="White",
                status="ACTIVE", vin=f"VIN{i:017d}", plate=f"PLT-00{i}",
                body_type="Sedan", engine_type="Gasoline", transmission="TA",
                engine_serial_number="ENG", odometer=0, doors_number=4,
                passengers_number=5, tire_specification="195/65R15",
                unit_value=200000, unit_billing_value=190000,
                bill_number="B1", public_vehicle_registry="R1",
                battery_model="BX", battery_serial_number="BS1",
                legal_owner_name="Juan", legal_owner_surnames="Perez",
                financed_status="PAID", features={}, details={},
                insurance_provider_id=1, policy_number="POL", policy_type="FULL",
            )
            car.associate = [associate]
            self.car_repo.cars.append(car)

        result = self.service.compute_folio(_request())
        assert result.folio.endswith("-03")

    def test_consecutive_zero_padded(self):
        self._add_associate()
        self._add_car_model()
        result = self.service.compute_folio(_request())
        parts = result.folio.split("-")
        assert len(parts[-1]) == 2

    # --- error cases ---

    def test_associate_not_found_raises_400(self):
        self._add_car_model()
        with pytest.raises(AssociateNotFoundException):
            self.service.compute_folio(_request(associate_id=9999))

    def test_car_model_not_found_raises_400(self):
        self._add_associate()
        with pytest.raises(CarModelNotFoundException):
            self.service.compute_folio(_request(make="Unknown", model="X"))
