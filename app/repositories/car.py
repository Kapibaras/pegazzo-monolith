import re
from datetime import UTC, datetime

from sqlalchemy import Integer, case, func

from app.enum.balance import SortOrder
from app.enum.crm import CarSortBy, CarStatus
from app.errors.database import DBOperationError
from app.models.balance import Transaction
from app.models.car import Associate, Car, Insurance, OwnerAssociate, associate_car, car_document_table
from app.models.contract import Contract
from app.models.document import Document
from app.models.driver import driver_document_table, guarantor_document_table, reference_document_table
from app.models.event import Event, event_document_table
from app.models.incidence import Incidence, incidence_document_table
from app.utils.logging_config import logger

from .abstract import DBRepository

_CAR_SORT_COLUMNS = {
    CarSortBy.MAKE: Car.make,
    CarSortBy.PLATE: Car.plate,
    CarSortBy.STATUS: Car.status,
    CarSortBy.YEAR: func.cast(Car.year, Integer),
    CarSortBy.CREATED_AT: Car.created_at,
}

_SIMILARITY_THRESHOLD = 0.3
_YEAR_RE = re.compile(r"\b(\d{4})\b")


class CarRepository(DBRepository):
    """Car repository class."""

    def get_by_id(self, car_id: str) -> Car | None:
        """Retrieve a car by id."""
        return self.db.query(Car).filter(Car.id == car_id).first()

    def get_by_vin(self, vin: str, exclude_id: str | None = None) -> Car | None:
        """Retrieve a car by VIN, optionally ignoring the car with `exclude_id`."""
        query = self.db.query(Car).filter(Car.vin == vin)
        if exclude_id:
            query = query.filter(Car.id != exclude_id)
        return query.first()

    def get_by_plate(self, plate: str, exclude_id: str | None = None) -> Car | None:
        """Retrieve a car by plate, optionally ignoring the car with `exclude_id`."""
        query = self.db.query(Car).filter(Car.plate == plate)
        if exclude_id:
            query = query.filter(Car.id != exclude_id)
        return query.first()

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

    def update_car(self, car: Car) -> Car:
        """Persist the pending changes of an already loaded car."""
        try:
            self.db.commit()
            self.db.refresh(car)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error updating car %s due to: %s", car.id, ex, exc_info=True)
            raise DBOperationError("Error updating car in the database") from ex

        return car

    def set_archived(self, car: Car, archived_at: datetime | None) -> Car:
        """Set (archive) or clear (unarchive) the archived_at marker of a car."""
        car.archived_at = archived_at
        return self.update_car(car)

    def has_history(self, car_id: str) -> bool:
        """Return True if the car is referenced by any contract, transaction, event or incidence."""
        return any(
            self.db.query(model.car_id).filter(model.car_id == car_id).first() is not None
            for model in (Contract, Transaction, Event, Incidence)
        )

    def soft_delete_car(self, car: Car) -> Car:
        """Mark the car as deleted while keeping its data (used when the car has history)."""
        car.deleted_at = datetime.now(tz=UTC)
        return self.update_car(car)

    def _document_is_shared(self, document_id: int) -> bool:
        """Return True if the document is linked to an entity other than a car."""
        return any(
            self.db.query(table.c.document_id).filter(table.c.document_id == document_id).first() is not None
            for table in (
                driver_document_table,
                guarantor_document_table,
                reference_document_table,
                event_document_table,
                incidence_document_table,
            )
        )

    def hard_delete_car(self, car: Car) -> list[str]:
        """Permanently delete the car with its links and exclusive documents.

        Returns the storage keys of the deleted documents so the caller can clean up storage.
        """
        try:
            document_keys: list[str] = []
            for document in self.get_car_documents(car.id):
                self.db.execute(
                    car_document_table.delete().where(
                        car_document_table.c.car_id == car.id,
                        car_document_table.c.document_id == document.id,
                    ),
                )
                if not self._document_is_shared(document.id) and not self._document_has_other_cars(document.id):
                    document_keys.append(document.url)
                    self.db.delete(document)
            self.db.execute(associate_car.delete().where(associate_car.c.car_id == car.id))
            self.db.delete(car)
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error("Error deleting car %s due to: %s", car.id, ex, exc_info=True)
            raise DBOperationError("Error deleting car from the database") from ex

        return document_keys

    def _document_has_other_cars(self, document_id: int) -> bool:
        """Return True if the document is still linked to some car."""
        return (
            self.db.query(car_document_table.c.car_id).filter(car_document_table.c.document_id == document_id).first()
        ) is not None

    def _base_query(self, status: CarStatus | None, archived: bool):
        """Build a base query with archive and status filters applied (soft-deleted cars are always hidden)."""
        query = self.db.query(Car).filter(Car.deleted_at.is_(None))
        query = query.filter(Car.archived_at.isnot(None)) if archived else query.filter(Car.archived_at.is_(None))
        if status:
            query = query.filter(Car.status == status)
        return query

    def _apply_search(self, query, search: str | None, year: str | None):
        """Apply fuzzy search and year filter in a single SQL query.

        Precedence (highest to lowest), resolved via CASE in a single pass:
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
        model_sim = func.word_similarity(text, Car.model)
        make_sim = func.word_similarity(text, Car.make)

        priority = case(
            (id_cond, 3),
            (model_sim >= _SIMILARITY_THRESHOLD, 2),
            (make_sim >= _SIMILARITY_THRESHOLD, 1),
            else_=0,
        )

        max_priority = query.with_entities(func.max(priority)).scalar_subquery()

        return query.filter(priority == max_priority)

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
        return (self.db.query(OwnerAssociate).filter(OwnerAssociate.associate_id == associate_id).first()) is not None

    def count_cars_for_associate(self, associate_id: int) -> int:
        """Return the number of cars linked to the given associate."""
        return self.db.query(associate_car).filter(associate_car.c.associate_id == associate_id).count()

    def get_open_contract_for_car(self, car_id: str) -> Contract | None:
        """Return a contract that is active today or starts in the future, or None."""
        today = datetime.now(tz=UTC).date()
        return self.db.query(Contract).filter(Contract.car_id == car_id, Contract.end_date >= today).first()

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
