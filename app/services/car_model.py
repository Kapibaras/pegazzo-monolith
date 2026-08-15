from app.errors.car_model import CarModelAlreadyExistsException, CarModelByIdNotFoundException
from app.models.car_model import CarModel
from app.repositories.car_model import CarModelRepository
from app.schemas.car_model import CarModelCreateSchema, CarModelGroupSchema, CarModelItemSchema


class CarModelService:
    """Service for the CarModel catalog."""

    def __init__(self, repository: CarModelRepository):
        """Initialize with a CarModelRepository."""
        self.repository = repository

    def list_grouped(self) -> list[CarModelGroupSchema]:
        """Return all catalog entries grouped by make, ordered alphabetically."""
        entries = self.repository.list_all()
        groups: dict[str, list[CarModelItemSchema]] = {}
        for entry in entries:
            groups.setdefault(entry.make, []).append(
                CarModelItemSchema(id=entry.id, model=entry.model, abbreviation=entry.abbreviation)
            )
        return [CarModelGroupSchema(make=make, models=models) for make, models in sorted(groups.items())]

    def create(self, data: CarModelCreateSchema) -> CarModel:
        """Create a new catalog entry, rejecting duplicate (make, model) pairs."""
        if self.repository.get_by_make_and_model(data.make, data.model):
            raise CarModelAlreadyExistsException(data.make, data.model)
        return self.repository.create(CarModel(make=data.make, model=data.model, abbreviation=data.abbreviation))

    def delete(self, car_model_id: int) -> None:
        """Delete a catalog entry by id."""
        car_model = self.repository.get_by_id(car_model_id)
        if not car_model:
            raise CarModelByIdNotFoundException(car_model_id)
        self.repository.delete(car_model)
