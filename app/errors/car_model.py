from fastapi import HTTPException, status


class CarModelAlreadyExistsException(HTTPException):
    """Exception raised when a (make, model) pair already exists in the catalog."""

    def __init__(self, make: str, model: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A catalog entry for '{make} {model}' already exists.",
        )


class CarModelByIdNotFoundException(HTTPException):
    """Exception raised when a CarModel entry is not found by id."""

    def __init__(self, car_model_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Car model with id '{car_model_id}' was not found.",
        )
