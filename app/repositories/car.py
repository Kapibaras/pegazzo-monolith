from app.errors.database import DBOperationError
from app.models.car import Associate, Car, Insurance
from app.utils.logging_config import logger

from .abstract import DBRepository


class CarRepository(DBRepository):
    """Car repository class."""

    def get_by_id(self, car_id: str) -> Car | None:
        """Retrieve a car by id."""
        return self.db.query(Car).filter(Car.id == car_id).first()

    def get_by_vin(self, vin: str) -> Car | None:
        """Retrieve a car by VIN."""
        return self.db.query(Car).filter(Car.vin == vin).first()

    def get_by_plate(self, plate: str) -> Car | None:
        """Retrieve a car by plate."""
        return self.db.query(Car).filter(Car.plate == plate).first()

    def get_insurance_by_id(self, insurance_id: int) -> Insurance | None:
        """Retrieve an insurance provider by id."""
        return self.db.query(Insurance).filter(Insurance.id == insurance_id).first()

    def get_associate_by_id(self, associate_id: int) -> Associate | None:
        """Retrieve an associate by id."""
        return self.db.query(Associate).filter(Associate.id == associate_id).first()

    def create_car(self, car: Car, associate: Associate | None) -> Car:
        """Create a new car, optionally linking an associate."""
        try:
            if associate:
                car.associate.append(associate)
            self.db.add(car)
            self.db.commit()
            self.db.refresh(car)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error creating car %s due to: %s", car.id, ex, exc_info=True)
            raise DBOperationError("Error creating car in the database") from ex

        return car
