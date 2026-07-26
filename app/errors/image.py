from fastapi import HTTPException, status


class InvalidImageTypeException(HTTPException):
    """Raised when the uploaded file's content type is not an allowed image type."""

    def __init__(self, content_type: str):
        """Initialize with the rejected content type."""
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content type '{content_type}' is not allowed. Allowed types: image/jpeg, image/png, image/webp",
        )


class MaxPhotosExceededException(HTTPException):
    """Raised when adding a photo would exceed the maximum of 4 photos per car."""

    def __init__(self):
        """Initialize with a fixed detail message."""
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A car cannot have more than 4 photos.",
        )


class ImageEntityNotFoundException(HTTPException):
    """Raised when the target entity for an image operation does not exist."""

    def __init__(self, entity_type: str, entity_id: str):
        """Initialize with the entity type and ID that were not found."""
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_type.capitalize()} with id '{entity_id}' was not found",
        )


class PhotoNotFoundException(HTTPException):
    """Raised when a photo URL to remove is not found in the car's photos list."""

    def __init__(self):
        """Initialize with a fixed detail message."""
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The specified photo URL was not found in this car's photos.",
        )
