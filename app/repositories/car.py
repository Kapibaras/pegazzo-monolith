from datetime import UTC, datetime

from sqlalchemy import or_

from app.enum.balance import SortOrder
from app.enum.crm import CarSortBy, CarStatus
from app.errors.database import DBOperationError
from app.models.car import Associate, Car, Insurance, car_document_table
from app.models.contract import Contract
from app.models.document import Document
from app.utils.logging_config import logger

from .abstract import DBRepository

_CAR_SORT_COLUMNS = {
    CarSortBy.MAKE: Car.make,
    CarSortBy.PLATE: Car.plate,
    CarSortBy.STATUS: Car.status,
    CarSortBy.CREATED_AT: Car.created_at,
}


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

    def _base_query(self, status: CarStatus | None, search: str | None, archived: bool):
        """Build a base query with the common filters applied."""
        query = self.db.query(Car)
        query = query.filter(Car.archived_at.isnot(None)) if archived else query.filter(Car.archived_at.is_(None))
        if status:
            query = query.filter(Car.status == status)
        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    Car.plate.ilike(term),
                    Car.make.ilike(term),
                    Car.model.ilike(term),
                ),
            )
        return query

    def count_cars(self, status: CarStatus | None, search: str | None, archived: bool) -> int:
        """Return the total count of cars matching the given filters."""
        return self._base_query(status, search, archived).count()

    def list_cars(
        self,
        status: CarStatus | None,
        search: str | None,
        archived: bool,
        sort_by: CarSortBy,
        sort_order: SortOrder,
        limit: int,
        offset: int,
    ) -> list[Car]:
        """Return a paginated, sorted list of cars matching the given filters."""
        column = _CAR_SORT_COLUMNS.get(sort_by, Car.created_at)
        order = column.desc() if sort_order == SortOrder.DESC else column.asc()
        return self._base_query(status, search, archived).order_by(order).offset(offset).limit(limit).all()

    def get_car_documents(self, car_id: str) -> list[Document]:
        """Return all documents linked to the given car."""
        return (
            self.db.query(Document)
            .join(car_document_table, Document.id == car_document_table.c.document_id)
            .filter(car_document_table.c.car_id == car_id)
            .all()
        )

    def get_active_contract_for_car(self, car_id: str) -> Contract | None:
        """Return the currently active contract for the car, or None."""
        today = datetime.now(tz=UTC).date()
        return (
            self.db.query(Contract)
            .filter(
                Contract.car_id == car_id,
                Contract.start_date <= today,
                Contract.end_date >= today,
            )
            .first()
        )
