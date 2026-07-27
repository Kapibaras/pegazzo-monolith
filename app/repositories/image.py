from app.errors.database import DBOperationError
from app.models.car import Car
from app.models.driver import Driver
from app.utils.logging_config import logger

from .abstract import DBRepository


class ImageRepository(DBRepository):
    """Image repository class — manages image URL fields on Car and Driver."""

    def get_car_by_id(self, car_id: str) -> Car | None:
        """Return a car by its primary key."""
        return self.db.query(Car).filter_by(id=car_id).first()

    def get_driver_by_id(self, driver_id: str) -> Driver | None:
        """Return a driver by its primary key."""
        return self.db.query(Driver).filter_by(id=driver_id).first()

    def set_car_agency_image(self, car: Car, url: str) -> Car:
        """Set or replace the car agency image URL."""
        try:
            car.agency_image = url
            self.db.commit()
            self.db.refresh(car)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error setting agency image for car %s: %s", car.id, ex)
            raise DBOperationError("Error updating car agency image") from ex
        return car

    def add_car_photo(self, car: Car, url: str) -> Car:
        """Append a photo URL to the car photos array."""
        try:
            current = list(car.photos or [])
            current.append(url)
            car.photos = current
            self.db.commit()
            self.db.refresh(car)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error adding photo to car %s: %s", car.id, ex)
            raise DBOperationError("Error adding photo to car") from ex
        return car

    def remove_car_photo(self, car: Car, url: str) -> Car:
        """Remove a photo URL from the car photos array."""
        try:
            car.photos = [p for p in (car.photos or []) if p != url]
            self.db.commit()
            self.db.refresh(car)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error removing photo from car %s: %s", car.id, ex)
            raise DBOperationError("Error removing photo from car") from ex
        return car

    def set_driver_photo(self, driver: Driver, url: str) -> Driver:
        """Set or replace the driver profile photo URL."""
        try:
            driver.photo = url
            self.db.commit()
            self.db.refresh(driver)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error setting photo for driver %s: %s", driver.id, ex)
            raise DBOperationError("Error updating driver photo") from ex
        return driver
