from fastapi import HTTPException, status


class DocumentNotFoundException(HTTPException):
    def __init__(self, document_id: int):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document with id '{document_id}' was not found")


class InvalidContentTypeException(HTTPException):
    def __init__(self, content_type: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content type '{content_type}' is not allowed. Allowed types: application/pdf, image/jpeg, image/png, image/webp",
        )


class EntityNotFoundException(HTTPException):
    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_type.capitalize()} with id '{entity_id}' was not found",
        )
