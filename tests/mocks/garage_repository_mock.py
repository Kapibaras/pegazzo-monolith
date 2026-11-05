from datetime import UTC, datetime

from app.models.driver import DriverGarage


class GarageRepositoryMock:
    """In-memory mock for GarageRepository."""

    def __init__(self):
        self.garages: list[DriverGarage] = []
        self._next_id = 1
        self.document_keys: dict[int, list[str]] = {}

    def reset(self):
        self.__init__()

    def get_by_id(self, garage_id: int) -> DriverGarage | None:
        return next((g for g in self.garages if g.id == garage_id), None)

    def create(self, garage: DriverGarage) -> DriverGarage:
        now = datetime.now(UTC)
        garage.id = self._next_id
        self._next_id += 1
        garage.created_at = now
        garage.updated_at = now
        self.garages.append(garage)
        return garage

    def update(self, garage: DriverGarage) -> DriverGarage:
        garage.updated_at = datetime.now(UTC)
        return garage

    def delete_with_documents(self, garage: DriverGarage) -> list[str]:
        self.garages = [g for g in self.garages if g.id != garage.id]
        return self.document_keys.pop(garage.id, [])
