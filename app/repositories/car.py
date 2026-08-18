import re
from datetime import UTC, datetime

from sqlalchemy import func

from app.enum.balance import SortOrder
from app.enum.crm import CarSortBy, CarStatus
from app.errors.database import DBOperationError
from app.models.car import Associate, Car, Insurance, OwnerAssociate, associate_car, car_document_table
from app.models.contract import Contract
from app.models.document import Document
from app.utils.logging_config import logger

from .abstract import DBRepository

_CAR_SORT_COLUMNS = {
    CarSortBy.MAKE: Car.make,
    CarSortBy.PLATE: Car.plate,
    CarSortBy.STATUS: Car.status,
    CarSortBy.YEAR: Car.year,
    CarSortBy.CREATED_AT: Car.created_at,
}

_SIMILARITY_THRESHOLD = 0.3
_YEAR_RE = re.compile(r"\b(\d{4})\b")


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

    def _base_query(self, status: CarStatus | None, archived: bool):
        """Build a base query with archive and status filters applied."""
        query = self.db.query(Car)
        query = query.filter(Car.archived_at.isnot(None)) if archived else query.filter(Car.archived_at.is_(None))
        if status:
            query = query.filter(Car.status == status)
        return query

    def _apply_search(self, query, search: str | None, year: str | None):
        """Apply fuzzy search and year filter.

        Precedence (highest to lowest):
          1. Exact id match (case-insensitive)
          2. Model fuzzy match  (word_similarity >= threshold)
          3. Make fuzzy match   (word_similarity >= threshold)

        A 4-digit token inside *search* is extracted as a year filter
        unless *year* is already supplied explicitly.
        """
        effective_year = year
        text = search or ""

        if search:
            m = _YEAR_RE.search(search)
            if m:
                effective_year = effective_year or m.group(1)
                text = _YEAR_RE.sub("", search).strip()

        if effective_year:
            query = query.filter(Car.year == effective_year)

        if not text:
            return query

        id_cond = func.lower(Car.id) == text.lower()
        model_cond = func.word_similarity(text, Car.model) >= _SIMILARITY_THRESHOLD
        make_cond = func.word_similarity(text, Car.make) >= _SIMILARITY_THRESHOLD

        if query.filter(id_cond).first():
            return query.filter(id_cond)
        if query.filter(model_cond).first():
            return query.filter(model_cond)
        return query.filter(make_cond)

    def count_cars(self, status: CarStatus | None, search: str | None, year: str | None, archived: bool) -> int:
        """Return the total count of cars matching the given filters."""
        return self._apply_search(self._base_query(status, archived), search, year).count()

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
        column = _CAR_SORT_COLUMNS.get(sort_by, Car.created_at)
        order = column.desc() if sort_order == SortOrder.DESC else column.asc()
        return (
            self._apply_search(self._base_query(status, archived), search, year)
            .order_by(order)
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_car_documents(self, car_id: str) -> list[Document]:
        """Return all documents linked to the given car."""
        return (
            self.db.query(Document)
            .join(car_document_table, Document.id == car_document_table.c.document_id)
            .filter(car_document_table.c.car_id == car_id)
            .all()
        )

    def is_us_owner(self, associate_id: int) -> bool:
        """Return True if the associate is registered in the owner_associate table."""
        return (
            self.db.query(OwnerAssociate)
            .filter(OwnerAssociate.associate_id == associate_id)
            .first()
        ) is not None

    def count_cars_for_associate(self, associate_id: int) -> int:
        """Return the number of cars linked to the given associate."""
        return (
            self.db.query(associate_car)
            .filter(associate_car.c.associate_id == associate_id)
            .count()
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
