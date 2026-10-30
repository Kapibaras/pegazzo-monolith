from datetime import UTC, datetime

from sqlalchemy import case, func

from app.enum.balance import SortOrder
from app.enum.crm import DriverSortBy, DriverStatus
from app.errors.database import DBOperationError
from app.models.contract import Contract
from app.models.document import Document
from app.models.driver import Driver, Reference, driver_document_table, driver_reference_table
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

    def get_driver_documents(self, driver_id: str) -> list[Document]:
        """Return all documents linked to the given driver."""
        return (
            self.db.query(Document)
            .join(driver_document_table, Document.id == driver_document_table.c.document_id)
            .filter(driver_document_table.c.driver_id == driver_id)
            .all()
        )

    def get_active_contract_for_driver(self, driver_id: str) -> Contract | None:
        """Return the currently active contract for the driver, or None."""
        today = datetime.now(tz=UTC).date()
        return (
            self.db.query(Contract)
            .filter(
                Contract.driver_id == driver_id,
                Contract.start_date <= today,
                Contract.end_date >= today,
            )
            .first()
        )

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

    def archive_driver(self, driver: Driver) -> Driver:
        """Set archived_at on the driver."""
        try:
            driver.archived_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(driver)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error archiving driver %s: %s", driver.id, ex, exc_info=True)
            raise DBOperationError("Error archiving driver") from ex
        return driver

    def unarchive_driver(self, driver: Driver) -> Driver:
        """Clear archived_at on the driver."""
        try:
            driver.archived_at = None
            self.db.commit()
            self.db.refresh(driver)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error unarchiving driver %s: %s", driver.id, ex, exc_info=True)
            raise DBOperationError("Error unarchiving driver") from ex
        return driver

    def delete_driver(self, driver: Driver) -> None:
        """Permanently delete a driver record."""
        try:
            self.db.delete(driver)
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error("Error deleting driver %s: %s", driver.id, ex, exc_info=True)
            raise DBOperationError("Error deleting driver") from ex

    def delete_driver_documents_m2m(self, driver_id: str) -> list[Document]:
        """Remove all M2M links and delete the linked document records."""
        documents = self.get_driver_documents(driver_id)
        try:
            self.db.execute(
                driver_document_table.delete().where(driver_document_table.c.driver_id == driver_id),
            )
            for doc in documents:
                self.db.delete(doc)
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error("Error deleting documents for driver %s: %s", driver_id, ex, exc_info=True)
            raise DBOperationError("Error deleting driver documents") from ex
        return documents

    def delete_driver_references(self, driver_id: str) -> None:
        """Remove M2M links and delete orphaned references for the driver."""
        try:
            ref_ids = [
                row.reference_id
                for row in self.db.execute(
                    driver_reference_table.select().where(driver_reference_table.c.driver_id == driver_id),
                ).fetchall()
            ]
            self.db.execute(
                driver_reference_table.delete().where(driver_reference_table.c.driver_id == driver_id),
            )
            for ref_id in ref_ids:
                other_links = (
                    self.db.query(func.count())
                    .select_from(driver_reference_table)
                    .filter(driver_reference_table.c.reference_id == ref_id)
                    .scalar()
                )
                if other_links == 0:
                    ref = self.db.query(Reference).filter(Reference.id == ref_id).first()
                    if ref:
                        self.db.delete(ref)
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error("Error deleting references for driver %s: %s", driver_id, ex, exc_info=True)
            raise DBOperationError("Error deleting driver references") from ex

    def clear_photo(self, driver: Driver) -> str | None:
        """Clear the driver's photo reference and return the old URL."""
        old_photo = driver.photo
        try:
            driver.photo = None
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error("Error clearing photo for driver %s: %s", driver.id, ex, exc_info=True)
            raise DBOperationError("Error clearing driver photo") from ex
        return old_photo

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
