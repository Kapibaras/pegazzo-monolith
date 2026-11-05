from app.errors.database import DBOperationError
from app.models.document import Document
from app.models.driver import DriverGarage, garage_document_table
from app.utils.logging_config import logger

from .abstract import DBRepository
from .owned_documents import delete_address_proofs


class GarageRepository(DBRepository):
    """Data-access layer for the driver garages."""

    def get_by_id(self, garage_id: int) -> DriverGarage | None:
        """Retrieve a garage by id."""
        return self.db.query(DriverGarage).filter(DriverGarage.id == garage_id).first()

    def create(self, garage: DriverGarage) -> DriverGarage:
        """Persist a new garage."""
        try:
            self.db.add(garage)
            self.db.commit()
            self.db.refresh(garage)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error creating garage for driver %s: %s", garage.driver_id, ex, exc_info=True)
            raise DBOperationError("Error creating garage in the database") from ex
        return garage

    def delete_address_proof(self, garage_id: int) -> list[str]:
        """Delete the garage's address proof (its address changed). Returns the storage keys of the deleted files."""
        return delete_address_proofs(self.db, garage_document_table, "garage_id", garage_id)

    def update(self, garage: DriverGarage) -> DriverGarage:
        """Update an existing garage."""
        try:
            self.db.commit()
            self.db.refresh(garage)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error updating garage %s due to: %s", garage.id, ex, exc_info=True)
            raise DBOperationError("Error updating garage in the database") from ex
        return garage

    def delete_with_documents(self, garage: DriverGarage) -> list[str]:
        """Delete a garage and its documents in one transaction.

        Returns the storage keys of the deleted documents so the caller can clean up storage after the commit.
        """
        document_keys: list[str] = []
        try:
            documents = (
                self.db.query(Document)
                .join(garage_document_table, Document.id == garage_document_table.c.document_id)
                .filter(garage_document_table.c.garage_id == garage.id)
                .all()
            )
            self.db.execute(garage_document_table.delete().where(garage_document_table.c.garage_id == garage.id))
            for doc in documents:
                document_keys.append(doc.url)
                self.db.delete(doc)
            self.db.expire(garage)
            self.db.delete(garage)
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error("Error deleting garage %s: %s", garage.id, ex, exc_info=True)
            raise DBOperationError("Error deleting garage") from ex
        return document_keys
