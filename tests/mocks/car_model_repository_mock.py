from app.models.car_model import CarModel


class CarModelRepositoryMock:
    """CarModel repository mock class."""

    def __init__(self):
        """Initialize with an empty catalog."""
        self.car_models: list[CarModel] = []
        self._next_id: int = 1

    def reset(self):
        """Reset the mock state."""
        self.car_models = []
        self._next_id = 1

    def get_by_id(self, car_model_id: int) -> CarModel | None:
        """Return the catalog entry with the given id, or None."""
        return next((cm for cm in self.car_models if cm.id == car_model_id), None)

    def get_by_make_and_model(self, make: str, model: str) -> CarModel | None:
        """Return the catalog entry matching (make, model), or None."""
        return next(
            (cm for cm in self.car_models if cm.make == make and cm.model == model),
            None,
        )

    def list_all(self) -> list[CarModel]:
        """Return all entries ordered by make then model."""
        return sorted(self.car_models, key=lambda cm: (cm.make, cm.model))

    def create(self, car_model: CarModel) -> CarModel:
        """Assign an id and append to the in-memory list."""
        car_model.id = self._next_id
        self._next_id += 1
        self.car_models.append(car_model)
        return car_model

    def delete(self, car_model: CarModel) -> None:
        """Remove the entry from the in-memory list."""
        self.car_models = [cm for cm in self.car_models if cm.id != car_model.id]
