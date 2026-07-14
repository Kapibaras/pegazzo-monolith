from app.errors.database import DBOperationError
from app.models.car import Car, car_document_table
from app.models.document import Document
from app.models.driver import Driver, Guarantor, driver_document_table, guarantor_document_table
from app.utils.logging_config import logger

from .abstract import DBRepository


class DocumentRepository(DBRepository):
    """Document repository class."""

    def get_by_id(self, document_id: int) -> Document | None:
        return self.db.query(Document).filter_by(id=document_id).first()

    def car_exists(self, car_id: str) -> bool:
        return self.db.query(Car).filter_by(id=car_id).first() is not None

    def driver_exists(self, driver_id: str) -> bool:
        return self.db.query(Driver).filter_by(id=driver_id).first() is not None

    def guarantor_exists(self, guarantor_id: int) -> bool:
        return self.db.query(Guarantor).filter_by(id=guarantor_id).first() is not None

    def create(self, document: Document) -> Document:
        try:
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
        except Exception as ex:
            self.db.rollback()
            logger.error(f"Error creating document due to: {ex}")
            raise DBOperationError("Error creating document in the database")
        return document

    def link_to_car(self, document_id: int, car_id: str) -> None:
        try:
            self.db.execute(car_document_table.insert().values(car_id=car_id, document_id=document_id))
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error(f"Error linking document {document_id} to car {car_id}: {ex}")
            raise DBOperationError("Error linking document to car")

    def link_to_driver(self, document_id: int, driver_id: str) -> None:
        try:
            self.db.execute(driver_document_table.insert().values(driver_id=driver_id, document_id=document_id))
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error(f"Error linking document {document_id} to driver {driver_id}: {ex}")
            raise DBOperationError("Error linking document to driver")

    def link_to_guarantor(self, document_id: int, guarantor_id: int) -> None:
        try:
            self.db.execute(guarantor_document_table.insert().values(guarantor_id=guarantor_id, document_id=document_id))
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error(f"Error linking document {document_id} to guarantor {guarantor_id}: {ex}")
            raise DBOperationError("Error linking document to guarantor")

    def delete(self, document: Document) -> None:
        try:
            self.db.delete(document)
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error(f"Error deleting document {document.id}: {ex}")
            raise DBOperationError("Error deleting document from the database")
