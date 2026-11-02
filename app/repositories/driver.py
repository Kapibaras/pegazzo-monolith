from datetime import UTC, datetime

from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload

from app.enum.balance import SortOrder
from app.enum.crm import DriverSortBy, DriverStatus
from app.errors.database import DBOperationError
from app.models.contract import Contract
from app.models.document import Document
from app.models.driver import (
    Driver,
    Guarantor,
    Reference,
    driver_document_table,
    driver_guarantor_table,
    driver_reference_table,
    guarantor_document_table,
    reference_document_table,
)
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
        """Retrieve a driver by id with eager-loaded relationships."""
        return (
            self.db.query(Driver)
            .options(
                selectinload(Driver.documents),
                selectinload(Driver.guarantors).selectinload(Guarantor.documents),
            )
            .filter(Driver.id == driver_id)
            .first()
        )

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
        except IntegrityError:
            self.db.rollback()
            raise
        except Exception as ex:
            self.db.rollback()
            logger.error("Error creating driver %s due to: %s", driver.id, ex, exc_info=True)
            raise DBOperationError("Error creating driver in the database") from ex
        return driver

    def get_active_contract_for_driver(self, driver_id: str) -> Contract | None:
        """Return the currently active contract for the driver, or None."""
        today = datetime.now(tz=UTC).date()
        return (
            self.db.query(Contract)
            .options(joinedload(Contract.car))
            .filter(
                Contract.driver_id == driver_id,
                Contract.start_date <= today,
                Contract.end_date >= today,
            )
            .order_by(Contract.start_date.desc())
            .first()
        )

    def has_pending_contracts(self, driver_id: str) -> bool:
        """Check if the driver has any active or future contract."""
        today = datetime.now(tz=UTC).date()
        return (
            self.db.query(Contract)
            .filter(
                Contract.driver_id == driver_id,
                Contract.end_date >= today,
            )
            .first()
        ) is not None

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

        return query.filter(priority > 0, priority == max_priority)

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

    def _delete_documents(self, document_ids: list[int]) -> list[str]:
        """Delete the given documents and return their storage keys."""
        if not document_ids:
            return []
        keys = [url for (url,) in self.db.query(Document.url).filter(Document.id.in_(document_ids)).all()]
        self.db.query(Document).filter(Document.id.in_(document_ids)).delete(synchronize_session=False)
        return keys

    def cascade_delete_driver(self, driver: Driver) -> list[str]:
        """Delete a driver and all dependent data in a single transaction.

        Cascade order:
        1. Unlink guarantors → delete guarantor docs → delete orphan guarantors
        2. Unlink driver documents → delete document records
        3. Unlink references → delete ref docs → delete orphan references
        4. Nullify contract FK references
        5. Delete driver record

        Objects are expired before `db.delete` so the ORM does not try to remove link rows that the
        Core DELETEs above already removed (StaleDataError when the collections were eager loaded).

        Returns the storage keys of the deleted documents so the caller can clean up storage.
        """
        driver_id = driver.id
        document_keys: list[str] = []
        try:
            guarantor_ids = [
                row.guarantor_id
                for row in self.db.execute(
                    driver_guarantor_table.select().where(driver_guarantor_table.c.driver_id == driver_id),
                ).fetchall()
            ]
            self.db.execute(
                driver_guarantor_table.delete().where(driver_guarantor_table.c.driver_id == driver_id),
            )
            if guarantor_ids:
                still_linked = select(driver_guarantor_table.c.guarantor_id).where(
                    driver_guarantor_table.c.guarantor_id.in_(guarantor_ids),
                )
                orphan_guarantors = (
                    self.db.query(Guarantor).filter(Guarantor.id.in_(guarantor_ids), Guarantor.id.not_in(still_linked)).all()
                )
                for g in orphan_guarantors:
                    g_doc_ids = [
                        row.document_id
                        for row in self.db.execute(
                            guarantor_document_table.select().where(
                                guarantor_document_table.c.guarantor_id == g.id,
                            ),
                        ).fetchall()
                    ]
                    self.db.execute(
                        guarantor_document_table.delete().where(
                            guarantor_document_table.c.guarantor_id == g.id,
                        ),
                    )
                    document_keys.extend(self._delete_documents(g_doc_ids))
                    self.db.expire(g)
                    self.db.delete(g)

            doc_ids = [
                row.document_id
                for row in self.db.execute(
                    driver_document_table.select().where(driver_document_table.c.driver_id == driver_id),
                ).fetchall()
            ]
            self.db.execute(
                driver_document_table.delete().where(driver_document_table.c.driver_id == driver_id),
            )
            document_keys.extend(self._delete_documents(doc_ids))

            ref_ids = [
                row.reference_id
                for row in self.db.execute(
                    driver_reference_table.select().where(driver_reference_table.c.driver_id == driver_id),
                ).fetchall()
            ]
            self.db.execute(
                driver_reference_table.delete().where(driver_reference_table.c.driver_id == driver_id),
            )
            if ref_ids:
                still_linked_refs = select(driver_reference_table.c.reference_id).where(
                    driver_reference_table.c.reference_id.in_(ref_ids),
                )
                orphan_refs = (
                    self.db.query(Reference).filter(Reference.id.in_(ref_ids), Reference.id.not_in(still_linked_refs)).all()
                )
                for ref in orphan_refs:
                    ref_doc_ids = [
                        row.document_id
                        for row in self.db.execute(
                            reference_document_table.select().where(
                                reference_document_table.c.reference_id == ref.id,
                            ),
                        ).fetchall()
                    ]
                    self.db.execute(
                        reference_document_table.delete().where(
                            reference_document_table.c.reference_id == ref.id,
                        ),
                    )
                    document_keys.extend(self._delete_documents(ref_doc_ids))
                    self.db.expire(ref)
                    self.db.delete(ref)

            self.db.query(Contract).filter(Contract.driver_id == driver_id).update(
                {Contract.driver_id: None},
                synchronize_session=False,
            )

            self.db.expire(driver)
            self.db.delete(driver)
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error("Error cascade-deleting driver %s: %s", driver_id, ex, exc_info=True)
            raise DBOperationError("Error deleting driver") from ex
        return document_keys

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
            .order_by(order, Driver.id)
            .offset(offset)
            .limit(limit)
            .all()
        )
