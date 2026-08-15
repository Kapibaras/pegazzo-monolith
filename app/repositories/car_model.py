from app.errors.database import DBOperationError
from app.models.car_model import CarModel
from app.utils.logging_config import logger

from .abstract import DBRepository


class CarModelRepository(DBRepository):
    """CarModel repository class."""

    def get_by_id(self, car_model_id: int) -> CarModel | None:
        """Retrieve a car model entry by id."""
        return self.db.query(CarModel).filter(CarModel.id == car_model_id).first()

    def get_by_make_and_model(self, make: str, model: str) -> CarModel | None:
        """Retrieve a car model entry by make and model (case-sensitive)."""
        return (
            self.db.query(CarModel)
            .filter(CarModel.make == make, CarModel.model == model)
            .first()
        )

    def list_all(self) -> list[CarModel]:
        """Return all car model catalog entries ordered by make then model."""
        return self.db.query(CarModel).order_by(CarModel.make, CarModel.model).all()

    def create(self, car_model: CarModel) -> CarModel:
        """Create a new car model catalog entry."""
        try:
            self.db.add(car_model)
            self.db.commit()
            self.db.refresh(car_model)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error creating car model due to: %s", ex, exc_info=True)
            raise DBOperationError("Error creating car model in the database") from ex
        return car_model

    def delete(self, car_model: CarModel) -> None:
        """Delete a car model catalog entry."""
        try:
            self.db.delete(car_model)
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error("Error deleting car model %s due to: %s", car_model.id, ex, exc_info=True)
            raise DBOperationError("Error deleting car model from the database") from ex
