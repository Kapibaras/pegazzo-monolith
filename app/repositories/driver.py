from sqlalchemy import case, func

from app.enum.balance import SortOrder
from app.enum.crm import DriverSortBy, DriverStatus
from app.errors.database import DBOperationError
from app.models.driver import Driver
from app.utils.logging_config import logger

from .abstract import DBRepository

_SIMILARITY_THRESHOLD = 0.3

_DRIVER_SORT_COLUMNS = {
    DriverSortBy.NAME: Driver.name,
    DriverSortBy.STATUS: Driver.status,
    DriverSortBy.CREATED_AT: Driver.created_at,
}


class DriverRepository(DBRepository):
    """Data-access layer for the Driver entity."""

    def get_by_id(self, driver_id: str) -> Driver | None:
        """Retrieve a driver by id."""
        return self.db.query(Driver).filter(Driver.id == driver_id).first()

    def get_by_identification_number(self, identification_number: str) -> Driver | None:
        """Retrieve a driver by identification number."""
        return self.db.query(Driver).filter(Driver.identification_number == identification_number).first()

    def get_by_license_number(self, license_number: str) -> Driver | None:
        """Retrieve a driver by license number."""
        return self.db.query(Driver).filter(Driver.license_number == license_number).first()

    def create_driver(self, driver: Driver) -> Driver:
        """Persist a new driver to the database."""
        try:
            self.db.add(driver)
            self.db.commit()
            self.db.refresh(driver)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error creating driver %s due to: %s", driver.id, ex, exc_info=True)
            raise DBOperationError("Error creating driver in the database") from ex
        return driver

    def _base_query(self, status: DriverStatus | None, archived: bool):
        """Build a base query with archive and status filters applied."""
        query = self.db.query(Driver)
        query = query.filter(Driver.archived_at.isnot(None)) if archived else query.filter(Driver.archived_at.is_(None))
        if status:
            query = query.filter(Driver.status == status)
        return query

    def _apply_search(self, query, search: str | None):
        """Apply fuzzy search over name, surnames and id.

        Precedence (highest to lowest):
          1. Exact id match (case-insensitive)
          2. Surnames fuzzy match (word_similarity >= threshold)
          3. Name fuzzy match (word_similarity >= threshold)
        """
        if not search:
            return query

        text = search.strip()
        if not text:
            return query

        id_cond = func.lower(Driver.id) == text.lower()
        surnames_sim = func.word_similarity(text, Driver.surnames)
        name_sim = func.word_similarity(text, Driver.name)

        priority = case(
            (id_cond, 3),
            (surnames_sim >= _SIMILARITY_THRESHOLD, 2),
            (name_sim >= _SIMILARITY_THRESHOLD, 1),
            else_=0,
        )

        max_priority = query.with_entities(func.max(priority)).scalar_subquery()

        return query.filter(priority == max_priority)

    def count_drivers(self, status: DriverStatus | None, search: str | None, archived: bool) -> int:
        """Return the total count of drivers matching the given filters."""
        return self._apply_search(self._base_query(status, archived), search).count()

    def list_drivers(
        self,
        status: DriverStatus | None,
        search: str | None,
        archived: bool,
        sort_by: DriverSortBy,
        sort_order: SortOrder,
        limit: int,
        offset: int,
    ) -> list[Driver]:
        """Return a paginated, sorted list of drivers matching the given filters."""
        column = _DRIVER_SORT_COLUMNS.get(sort_by, Driver.created_at)
        order = column.desc() if sort_order == SortOrder.DESC else column.asc()
        return (
            self._apply_search(self._base_query(status, archived), search)
            .order_by(order)
            .offset(offset)
            .limit(limit)
            .all()
        )
