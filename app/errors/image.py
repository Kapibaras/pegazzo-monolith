from fastapi import status

from app.errors import PegazzoException


class InvalidImageTypeException(PegazzoException):
    """Raised when the uploaded file's content type is not an allowed image type."""

    def __init__(self, content_type: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content type '{content_type}' is not allowed. Allowed types: image/jpeg, image/png, image/webp",
        )


class MaxPhotosExceededException(PegazzoException):
    """Raised when adding a photo would exceed the maximum of 4 photos per car."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A car cannot have more than 4 photos.",
        )


class ImageEntityNotFoundException(PegazzoException):
    """Raised when the target entity for an image operation does not exist."""

    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_type.capitalize()} with id '{entity_id}' was not found",
        )


class PhotoNotFoundException(PegazzoException):
    """Raised when a photo URL to remove is not found in the car's photos list."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The specified photo URL was not found in this car's photos.",
        )
