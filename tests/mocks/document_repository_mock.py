from datetime import datetime, timezone

from app.enum.crm import DocumentEntityType
from app.errors.database import DBOperationError
from app.models.document import Document


class DocumentRepositoryMock:
    """Mock implementation of DocumentRepository for testing purposes."""

    def __init__(self):
        self._next_id = 1
        self.documents: list[Document] = [
            Document(
                id=1,
                type="contract",
                url="car/ABC123/doc-uuid.pdf",
                category="pending",
                confidence=None,
                extracted_fields=None,
                expiry_date=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        ]
        self._next_id = 2
        self.existing_cars: set[str] = {"ABC123DEF456789"}
        self.existing_drivers: set[str] = {"DRV001"}
        self.existing_guarantors: set[int] = {1}
        self.links: list[dict] = []
        self.raise_on_create = False

    def reset(self):
        self.__init__()

    def get_by_id(self, document_id: int) -> Document | None:
        return next((d for d in self.documents if d.id == document_id), None)

    def car_exists(self, car_id: str) -> bool:
        return car_id in self.existing_cars

    def driver_exists(self, driver_id: str) -> bool:
        return driver_id in self.existing_drivers

    def guarantor_exists(self, guarantor_id: int) -> bool:
        return guarantor_id in self.existing_guarantors

    def create(self, document: Document) -> Document:
        if self.raise_on_create:
            raise DBOperationError("Error creating document in the database")
        document.id = self._next_id
        self._next_id += 1
        document.created_at = datetime.now(timezone.utc)
        document.updated_at = datetime.now(timezone.utc)
        self.documents.append(document)
        return document

    def link_to_car(self, document_id: int, car_id: str) -> None:
        self.links.append({"entity_type": DocumentEntityType.CAR, "entity_id": car_id, "document_id": document_id})

    def link_to_driver(self, document_id: int, driver_id: str) -> None:
        self.links.append({"entity_type": DocumentEntityType.DRIVER, "entity_id": driver_id, "document_id": document_id})

    def link_to_guarantor(self, document_id: int, guarantor_id: int) -> None:
        self.links.append({"entity_type": DocumentEntityType.GUARANTOR, "entity_id": guarantor_id, "document_id": document_id})

    def delete(self, document: Document) -> None:
        self.documents = [d for d in self.documents if d.id != document.id]
