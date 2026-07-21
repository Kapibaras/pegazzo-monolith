from fastapi import HTTPException, status


class DocumentNotFoundException(HTTPException):
    """Raised when a document is not found by its ID."""

    def __init__(self, document_id: int):
        """Initialize with the missing document ID."""
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document with id '{document_id}' was not found")


class InvalidContentTypeException(HTTPException):
    """Raised when the uploaded file's content type is not allowed."""

    def __init__(self, content_type: str):
        """Initialize with the rejected content type."""
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content type '{content_type}' is not allowed. Allowed types: application/pdf, image/jpeg, image/png, image/webp",
        )


class EntityNotFoundException(HTTPException):
    """Raised when the target entity (car, driver, or guarantor) does not exist."""

    def __init__(self, entity_type: str, entity_id: str):
        """Initialize with the entity type and ID that were not found."""
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_type.capitalize()} with id '{entity_id}' was not found",
        )
