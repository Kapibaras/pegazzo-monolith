from enum import StrEnum


class ImageEntityType(StrEnum):
    """Enum for image target entity types."""

    CAR_AGENCY_IMAGE = "car_agency_image"
    CAR_PHOTO = "car_photo"
    DRIVER_PHOTO = "driver_photo"


class DocumentEntityType(StrEnum):
    """Enum for document target entity types."""

    CAR = "car"
    DRIVER = "driver"
    GUARANTOR = "guarantor"


class CarStatus(StrEnum):
    """Enum for car operational status."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    IN_MAINTENANCE = "IN_MAINTENANCE"


class CarSortBy(StrEnum):
    """Enum for car list sort fields."""

    MAKE = "make"
    PLATE = "plate"
    STATUS = "status"
    CREATED_AT = "created_at"


class DriverStatus(StrEnum):
    """Enum for driver operational status."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
