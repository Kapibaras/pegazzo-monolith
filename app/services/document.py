import uuid

from app.enum.crm import DocumentEntityType
from app.errors.document import DocumentNotFoundException, EntityNotFoundException, InvalidContentTypeException
from app.models.document import Document
from app.repositories.document import DocumentRepository
from app.schemas.document import (
    ALLOWED_CONTENT_TYPES,
    DocumentConfirmSchema,
    DocumentResponseSchema,
    UploadUrlRequestSchema,
    UploadUrlResponseSchema,
)
from app.storage import r2


def _extension_for(content_type: str) -> str:
    extensions = {
        "application/pdf": "pdf",
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    return extensions.get(content_type, "bin")


class DocumentService:
    """Document service class."""

    def __init__(self, repository: DocumentRepository):
        """Initialize the document service with a repository."""
        self.repository = repository

    def request_upload_url(self, data: UploadUrlRequestSchema) -> UploadUrlResponseSchema:
        """Validate the request and return a presigned PUT URL for direct R2 upload."""
        if data.content_type not in ALLOWED_CONTENT_TYPES:
            raise InvalidContentTypeException(data.content_type)

        self._assert_entity_exists(data.entity_type, data.entity_id)

        ext = _extension_for(data.content_type)
        key = f"{data.entity_type}/{data.entity_id}/{uuid.uuid4()}.{ext}"
        upload_url = r2.generate_document_upload_url(key, data.content_type)
        return UploadUrlResponseSchema(upload_url=upload_url, key=key, expires_in=3600)

    def create_document(self, data: DocumentConfirmSchema) -> DocumentResponseSchema:
        """Create a Document record and link it to the target entity."""
        self._assert_entity_exists(data.entity_type, data.entity_id)

        document = Document(
            type=data.type,
            url=data.key,
            category="pending",
            expiry_date=data.expiry_date,
        )
        document = self.repository.create(document)

        self._link_document(document.id, data.entity_type, data.entity_id)

        presigned_url = r2.generate_document_read_url(document.url)
        response = DocumentResponseSchema.model_validate(document)
        response.url = presigned_url
        return response

    def get_document(self, document_id: int) -> DocumentResponseSchema:
        """Return document metadata with a fresh presigned GET URL."""
        document = self.repository.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundException(document_id)

        presigned_url = r2.generate_document_read_url(document.url)
        response = DocumentResponseSchema.model_validate(document)
        response.url = presigned_url
        return response

    def delete_document(self, document_id: int) -> None:
        """Delete a document record from the database."""
        document = self.repository.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundException(document_id)
        self.repository.delete(document)

    def _assert_entity_exists(self, entity_type: DocumentEntityType, entity_id: str) -> None:
        if entity_type == DocumentEntityType.CAR:
            if not self.repository.car_exists(entity_id):
                raise EntityNotFoundException("car", entity_id)
        elif entity_type == DocumentEntityType.DRIVER:
            if not self.repository.driver_exists(entity_id):
                raise EntityNotFoundException("driver", entity_id)
        elif entity_type == DocumentEntityType.GUARANTOR:
            try:
                guarantor_id = int(entity_id)
            except ValueError as err:
                raise EntityNotFoundException("guarantor", entity_id) from err
            if not self.repository.guarantor_exists(guarantor_id):
                raise EntityNotFoundException("guarantor", entity_id)

    def _link_document(self, document_id: int, entity_type: DocumentEntityType, entity_id: str) -> None:
        if entity_type == DocumentEntityType.CAR:
            self.repository.link_to_car(document_id, entity_id)
        elif entity_type == DocumentEntityType.DRIVER:
            self.repository.link_to_driver(document_id, entity_id)
        elif entity_type == DocumentEntityType.GUARANTOR:
            self.repository.link_to_guarantor(document_id, int(entity_id))
