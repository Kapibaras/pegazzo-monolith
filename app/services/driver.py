import math
from datetime import UTC, datetime

from app.errors.driver import (
    DriverIdAlreadyExistsException,
    IdentificationNumberAlreadyExistsException,
    LicenseNumberAlreadyExistsException,
    LicenseValidityInPastException,
)
from app.models.driver import Driver
from app.repositories.driver import DriverRepository
from app.schemas.car import PaginationSchema
from app.schemas.driver import DriverCreateSchema, DriverListQuerySchema, DriverListResponseSchema


class DriverService:
    """Business logic for driver operations."""

    def __init__(self, repository: DriverRepository):
        self.repository = repository

    def list_drivers(self, params: DriverListQuerySchema) -> DriverListResponseSchema:
        """Return a paginated, filtered and sorted list of drivers."""
        offset = (params.page - 1) * params.limit
        total = self.repository.count_drivers(
            status=params.status,
            search=params.search,
            archived=params.archived,
        )
        drivers = self.repository.list_drivers(
            status=params.status,
            search=params.search,
            archived=params.archived,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            limit=params.limit,
            offset=offset,
        )
        return DriverListResponseSchema(
            drivers=drivers,
            pagination=PaginationSchema(
                page=params.page,
                limit=params.limit,
                total=total,
                total_pages=0 if total == 0 else math.ceil(total / params.limit),
            ),
        )

    def create_driver(self, data: DriverCreateSchema) -> Driver:
        """Create a new driver with validations."""
        if self.repository.get_by_id(data.id):
            raise DriverIdAlreadyExistsException(data.id)

        if self.repository.get_by_identification_number(data.identification_number):
            raise IdentificationNumberAlreadyExistsException(data.identification_number)

        if self.repository.get_by_license_number(data.license_number):
            raise LicenseNumberAlreadyExistsException(data.license_number)

        if data.license_validity <= datetime.now(UTC):
            raise LicenseValidityInPastException

        driver = Driver(
            id=data.id,
            name=data.name,
            surnames=data.surnames,
            status=data.status,
            telephones=data.telephones,
            license_number=data.license_number,
            license_validity=data.license_validity,
            identification_number=data.identification_number,
            address=data.address,
            garage_address=data.garage_address,
        )

        return self.repository.create_driver(driver)
