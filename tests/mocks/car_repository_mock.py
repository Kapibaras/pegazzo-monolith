from typing import Optional

from app.enum.balance import SortOrder
from app.enum.crm import CarSortBy, CarStatus
from app.models.car import Associate, Car, Insurance

_DEFAULT_INSURANCE = Insurance(id=1, name="AXA", telephones=["+521234567890"])
_DEFAULT_ASSOCIATE = Associate(id=1, name="Juan", surnames="Pérez", telephones=["+521234567890"])


class CarRepositoryMock:
    """Car repository mock class."""

    def __init__(self):
        """Initialize the mock with default insurance and associate data."""
        self.cars: list[Car] = []
        self.insurances: list[Insurance] = [_DEFAULT_INSURANCE]
        self.associates: list[Associate] = [_DEFAULT_ASSOCIATE]

    def reset(self):
        """Reset the mock state to its initial values."""
        self.cars = []
        self.insurances = [_DEFAULT_INSURANCE]
        self.associates = [_DEFAULT_ASSOCIATE]

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

    def _filter(self, status: Optional[CarStatus], search: Optional[str], archived: bool) -> list[Car]:
        """Return cars matching the given filters."""
        result = []
        for car in self.cars:
            if archived and car.archived_at is None:
                continue
            if not archived and car.archived_at is not None:
                continue
            if status and car.status != status:
                continue
            if search:
                s = search.lower()
                if not (s in car.plate.lower() or s in car.make.lower() or s in car.model.lower()):
                    continue
            result.append(car)
        return result

    def count_cars(self, status: Optional[CarStatus], search: Optional[str], archived: bool) -> int:
        """Return the total count of cars matching the given filters."""
        return len(self._filter(status, search, archived))

    def list_cars(
        self,
        status: Optional[CarStatus],
        search: Optional[str],
        archived: bool,
        sort_by: CarSortBy,
        sort_order: SortOrder,
        limit: int,
        offset: int,
    ) -> list[Car]:
        """Return a paginated, sorted list of cars matching the given filters."""
        cars = self._filter(status, search, archived)
        reverse = sort_order == SortOrder.DESC
        cars.sort(key=lambda c: getattr(c, sort_by, "") or "", reverse=reverse)
        return cars[offset : offset + limit]
