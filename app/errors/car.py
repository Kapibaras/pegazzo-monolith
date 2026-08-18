from fastapi import HTTPException, status


class CarNotFoundException(HTTPException):
    """Exception raised when a car is not found."""

    def __init__(self, car_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Car with id '{car_id}' was not found",
        )


class CarIdAlreadyExistsException(HTTPException):
    """Exception raised when a car id already exists."""

    def __init__(self, car_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A car with id '{car_id}' already exists",
        )


class CarVinAlreadyExistsException(HTTPException):
    """Exception raised when a car VIN already exists."""

    def __init__(self, vin: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A car with VIN '{vin}' already exists",
        )


class CarPlateAlreadyExistsException(HTTPException):
    """Exception raised when a car plate already exists."""

    def __init__(self, plate: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A car with plate '{plate}' already exists",
        )


class PolicyExpirationDateInPastException(HTTPException):
    """Exception raised when the policy expiration date is in the past."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Policy expiration date must not be in the past",
        )


class InsuranceProviderNotFoundException(HTTPException):
    """Exception raised when the insurance provider does not exist."""

    def __init__(self, insurance_provider_id: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insurance provider with id '{insurance_provider_id}' was not found",
        )


class AssociateNotFoundException(HTTPException):
    """Exception raised when the associate does not exist."""

    def __init__(self, associate_id: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Associate with id '{associate_id}' was not found",
        )


class CarModelNotFoundException(HTTPException):
    """Exception raised when the (make, model) pair is not found in the CarModel catalog."""

    def __init__(self, make: str, model: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Make/model combination '{make} {model}' is not registered in the catalog. Register it first before computing a folio.",
        )
