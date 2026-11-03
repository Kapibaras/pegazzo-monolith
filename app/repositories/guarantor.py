from sqlalchemy import func

from app.errors.database import DBOperationError
from app.models.document import Document
from app.models.driver import Driver, Guarantor, driver_guarantor_table, guarantor_document_table
from app.utils.logging_config import logger

from .abstract import DBRepository


class GuarantorRepository(DBRepository):
    """Data-access layer for the Guarantor entity."""

    def get_by_id(self, guarantor_id: int) -> Guarantor | None:
        """Retrieve a guarantor by id."""
        return self.db.query(Guarantor).filter(Guarantor.id == guarantor_id).first()

    def create_and_link(self, guarantor: Guarantor, driver_id: str) -> Guarantor:
        """Create a guarantor and link it to a driver in one transaction."""
        try:
            self.db.add(guarantor)
            self.db.flush()
            self.db.execute(
                driver_guarantor_table.insert().values(driver_id=driver_id, guarantor_id=guarantor.id),
            )
            self.db.commit()
            self.db.refresh(guarantor)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error creating guarantor for driver %s: %s", driver_id, ex, exc_info=True)
            raise DBOperationError("Error creating guarantor in the database") from ex
        return guarantor

    def update(self, guarantor: Guarantor) -> Guarantor:
        """Update an existing guarantor."""
        try:
            self.db.commit()
            self.db.refresh(guarantor)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error updating guarantor %s due to: %s", guarantor.id, ex, exc_info=True)
            raise DBOperationError("Error updating guarantor in the database") from ex
        return guarantor

    def unlink_and_delete_if_orphan(self, driver_id: str, guarantor: Guarantor) -> list[str]:
        """Unlink a guarantor from a driver and delete it with its documents if no driver is left.

        Runs in a single transaction. Returns the storage keys of the deleted documents so the
        caller can clean up storage after the commit.
        """
        document_keys: list[str] = []
        try:
            self.db.execute(
                driver_guarantor_table.delete().where(
                    (driver_guarantor_table.c.driver_id == driver_id) & (driver_guarantor_table.c.guarantor_id == guarantor.id),
                ),
            )
            if self._count_linked_drivers(guarantor.id) == 0:
                documents = (
                    self.db.query(Document)
                    .join(guarantor_document_table, Document.id == guarantor_document_table.c.document_id)
                    .filter(guarantor_document_table.c.guarantor_id == guarantor.id)
                    .all()
                )
                self.db.execute(
                    guarantor_document_table.delete().where(guarantor_document_table.c.guarantor_id == guarantor.id),
                )
                for doc in documents:
                    document_keys.append(doc.url)
                    self.db.delete(doc)
                self.db.expire(guarantor)
                self.db.delete(guarantor)
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error("Error removing guarantor %s from driver %s: %s", guarantor.id, driver_id, ex, exc_info=True)
            raise DBOperationError("Error removing guarantor from driver") from ex
        return document_keys

    def link_to_driver(self, driver_id: str, guarantor_id: int) -> None:
        """Insert a row into the driver_guarantor M2M table."""
        try:
            self.db.execute(
                driver_guarantor_table.insert().values(driver_id=driver_id, guarantor_id=guarantor_id),
            )
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error("Error linking guarantor %s to driver %s: %s", guarantor_id, driver_id, ex, exc_info=True)
            raise DBOperationError("Error linking guarantor to driver") from ex

    def is_linked_to_driver(self, driver_id: str, guarantor_id: int) -> bool:
        """Check whether a guarantor is linked to a specific driver."""
        result = self.db.execute(
            driver_guarantor_table.select().where(
                (driver_guarantor_table.c.driver_id == driver_id) & (driver_guarantor_table.c.guarantor_id == guarantor_id),
            ),
        ).first()
        return result is not None

    def count_guarantors_for_driver(self, driver_id: str, *, lock: bool = False) -> int:
        """Return how many guarantors are linked to this driver.

        Pass lock=True to lock the driver row (FOR UPDATE) so concurrent creations are serialized.
        PostgreSQL does not allow FOR UPDATE on an aggregate, and a driver without guarantors has
        no link rows to lock, so the lock is taken on the driver itself.
        """
        if lock:
            self.db.query(Driver).filter(Driver.id == driver_id).with_for_update().first()
        return (
            self.db.query(func.count())
            .select_from(driver_guarantor_table)
            .filter(driver_guarantor_table.c.driver_id == driver_id)
            .scalar()
        )

    def _count_linked_drivers(self, guarantor_id: int) -> int:
        """Return how many drivers are linked to this guarantor."""
        return (
            self.db.query(func.count())
            .select_from(driver_guarantor_table)
            .filter(driver_guarantor_table.c.guarantor_id == guarantor_id)
            .scalar()
        )
