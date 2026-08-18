import re
from datetime import UTC, datetime

from app.enum.balance import SortOrder
from app.enum.crm import CarSortBy, CarStatus
from app.models.car import Associate, Car, Insurance
from app.models.contract import Contract
from app.models.document import Document

_YEAR_RE = re.compile(r"\b(\d{4})\b")

_DEFAULT_INSURANCE = Insurance(id=1, name="AXA", telephones=["+521234567890"])
_DEFAULT_ASSOCIATE = Associate(id=1, name="Juan", surnames="Pérez", telephones=["+521234567890"])


class CarRepositoryMock:
    """Car repository mock class."""

    def __init__(self):
        """Initialize the mock with default insurance and associate data."""
        self.cars: list[Car] = []
        self.insurances: list[Insurance] = [_DEFAULT_INSURANCE]
        self.associates: list[Associate] = [_DEFAULT_ASSOCIATE]
        self.us_associate_ids: set[int] = set()
        self.car_documents: dict[str, list[Document]] = {}
        self.contracts: list[Contract] = []

    def reset(self):
        """Reset the mock state to its initial values."""
        self.cars = []
        self.insurances = [_DEFAULT_INSURANCE]
        self.associates = [_DEFAULT_ASSOCIATE]
        self.us_associate_ids = set()
        self.car_documents = {}
        self.contracts = []

    def get_by_id(self, car_id: str) -> Car | None:
        """Return the car with the given ID, or None."""
        return next((c for c in self.cars if c.id == car_id), None)

    def get_by_vin(self, vin: str) -> Car | None:
        """Return the car with the given VIN, or None."""
        return next((c for c in self.cars if c.vin == vin), None)

    def get_by_plate(self, plate: str) -> Car | None:
        """Return the car with the given plate, or None."""
        return next((c for c in self.cars if c.plate == plate), None)

    def get_insurance_by_id(self, insurance_id: int) -> Insurance | None:
        """Return the insurance provider with the given ID, or None."""
        return next((i for i in self.insurances if i.id == insurance_id), None)

    def get_associate_by_id(self, associate_id: int) -> Associate | None:
        """Return the associate with the given ID, or None."""
        return next((a for a in self.associates if a.id == associate_id), None)

    def create_car(self, car: Car, _associate: Associate | None) -> Car:
        """Append the car to the in-memory list and return it."""
        self.cars.append(car)
        return car

    def _filter(self, status: CarStatus | None, search: str | None, year: str | None, archived: bool) -> list[Car]:
        """Return cars matching the given filters with fuzzy-search precedence."""
        result = [
            c for c in self.cars
            if not (archived and c.archived_at is None)
            and not (not archived and c.archived_at is not None)
            and (not status or c.status == status)
        ]

        effective_year = year
        text = search or ""

        if search:
            m = _YEAR_RE.search(search)
            if m:
                effective_year = effective_year or m.group(1)
                text = _YEAR_RE.sub("", search).strip()

        if effective_year:
            result = [c for c in result if c.year == effective_year]

        if not text:
            return result

        t = text.lower()

        id_matches = [c for c in result if c.id.lower() == t]
        if id_matches:
            return id_matches

        model_matches = [c for c in result if t in c.model.lower()]
        if model_matches:
            return model_matches

        return [c for c in result if t in c.make.lower()]

    def count_cars(self, status: CarStatus | None, search: str | None, year: str | None, archived: bool) -> int:
        """Return the total count of cars matching the given filters."""
        return len(self._filter(status, search, year, archived))

    def get_car_documents(self, car_id: str) -> list[Document]:
        """Return documents linked to the car."""
        return self.car_documents.get(car_id, [])

    def is_us_owner(self, associate_id: int) -> bool:
        """Return True if the associate is in the US-owner set."""
        return associate_id in self.us_associate_ids

    def count_cars_for_associate(self, associate_id: int) -> int:
        """Return the number of cars whose associate list contains the given associate_id."""
        return sum(
            1 for c in self.cars if any(a.id == associate_id for a in (c.associate or []))
        )

    def get_active_contract_for_car(self, car_id: str) -> Contract | None:
        """Return the active contract for the car, or None."""
        today = datetime.now(tz=UTC).date()
        return next(
            (
                c
                for c in self.contracts
                if c.car_id == car_id and c.start_date <= today <= c.end_date
            ),
            None,
        )

    def list_cars(
        self,
        status: CarStatus | None,
        search: str | None,
        year: str | None,
        archived: bool,
        sort_by: CarSortBy,
        sort_order: SortOrder,
        limit: int,
        offset: int,
    ) -> list[Car]:
        """Return a paginated, sorted list of cars matching the given filters."""
        cars = self._filter(status, search, year, archived)
        reverse = sort_order == SortOrder.DESC
        cars.sort(key=lambda c: getattr(c, sort_by, "") or "", reverse=reverse)
        return cars[offset : offset + limit]
