from app.database.base import Base
from app.errors.database import DBOperationError
from app.models.car import Car, car_document_table
from app.models.document import Document
from app.models.driver import (
    Driver,
    DriverGarage,
    Guarantor,
    driver_document_table,
    garage_document_table,
    guarantor_document_table,
)
from app.utils.logging_config import logger

from .abstract import DBRepository


class DocumentRepository(DBRepository):
    """Document repository class."""

    def get_by_id(self, document_id: int) -> Document | None:
        """Return a document by its primary key."""
        return self.db.query(Document).filter_by(id=document_id).first()

    def car_exists(self, car_id: str) -> bool:
        """Return True if a non-deleted car with the given ID exists."""
        return self.db.query(Car).filter(Car.id == car_id, Car.deleted_at.is_(None)).first() is not None

    def driver_exists(self, driver_id: str) -> bool:
        """Return True if a non-deleted driver with the given ID exists."""
        return self.db.query(Driver).filter(Driver.id == driver_id, Driver.deleted_at.is_(None)).first() is not None

    def guarantor_exists(self, guarantor_id: int) -> bool:
        """Return True if a guarantor with the given ID exists."""
        return self.db.query(Guarantor).filter_by(id=guarantor_id).first() is not None

    def garage_exists(self, garage_id: int) -> bool:
        """Return True if a garage with the given ID exists."""
        return self.db.query(DriverGarage).filter_by(id=garage_id).first() is not None

    def create(self, document: Document) -> Document:
        """Persist a new document and return it with its generated ID."""
        try:
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
        except Exception as ex:
            self.db.rollback()
            logger.error(f"Error creating document due to: {ex}")
            raise DBOperationError("Error creating document in the database") from ex
        return document

    def link_to_car(self, document_id: int, car_id: str) -> None:
        """Insert a row in the car_document M2M table."""
        try:
            self.db.execute(car_document_table.insert().values(car_id=car_id, document_id=document_id))
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error(f"Error linking document {document_id} to car {car_id}: {ex}")
            raise DBOperationError("Error linking document to car") from ex

    def link_to_driver(self, document_id: int, driver_id: str) -> None:
        """Insert a row in the driver_document M2M table."""
        try:
            self.db.execute(driver_document_table.insert().values(driver_id=driver_id, document_id=document_id))
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error(f"Error linking document {document_id} to driver {driver_id}: {ex}")
            raise DBOperationError("Error linking document to driver") from ex

    def link_to_guarantor(self, document_id: int, guarantor_id: int) -> None:
        """Insert a row in the guarantor_document M2M table."""
        try:
            self.db.execute(guarantor_document_table.insert().values(guarantor_id=guarantor_id, document_id=document_id))
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error(f"Error linking document {document_id} to guarantor {guarantor_id}: {ex}")
            raise DBOperationError("Error linking document to guarantor") from ex

    def link_to_garage(self, document_id: int, garage_id: int) -> None:
        """Insert a row in the garage_document M2M table."""
        try:
            self.db.execute(garage_document_table.insert().values(garage_id=garage_id, document_id=document_id))
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error(f"Error linking document {document_id} to garage {garage_id}: {ex}")
            raise DBOperationError("Error linking document to garage") from ex

    def delete(self, document: Document) -> None:
        """Remove a document record and its links to cars, drivers, guarantors, etc. in one transaction.

        The M2M link tables have plain foreign keys (no ON DELETE CASCADE), so their rows must go first or the
        delete fails with an integrity error. Every table that references ``document.id`` is cleaned, so new link
        tables are covered automatically.
        """
        try:
            document_id = document.id
            for table in Base.metadata.sorted_tables:
                if table is Document.__table__:
                    continue
                for foreign_key in table.foreign_keys:
                    if foreign_key.column.table is Document.__table__ and foreign_key.column.name == "id":
                        self.db.execute(table.delete().where(foreign_key.parent == document_id))
            # Expire so the ORM does not try to remove link rows (already gone) when the collections were loaded.
            self.db.expire_all()
            self.db.delete(self.db.get(Document, document_id))
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error(f"Error deleting document {document.id}: {ex}")
            raise DBOperationError("Error deleting document from the database") from ex
