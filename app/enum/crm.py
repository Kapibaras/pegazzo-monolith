from enum import StrEnum


class CarStatus(StrEnum):
    """Enum for car operational status."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    IN_MAINTENANCE = "IN_MAINTENANCE"


class DriverStatus(StrEnum):
    """Enum for driver operational status."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
