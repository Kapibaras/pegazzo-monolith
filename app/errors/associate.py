from fastapi import HTTPException, status


class AssociateNotFoundException(HTTPException):
    """Exception raised when an associate is not found."""

    def __init__(self, associate_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Associate with id '{associate_id}' was not found",
        )


class AssociateInUseException(HTTPException):
    """Exception raised when trying to delete an associate that has linked cars."""

    def __init__(self, associate_id: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Associate '{associate_id}' cannot be deleted because it has linked cars",
        )
