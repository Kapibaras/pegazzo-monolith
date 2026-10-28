import math
from datetime import UTC, datetime

from app.errors.driver import (
    DriverIdAlreadyExistsException,
    DriverNotFoundException,
    IdentificationNumberAlreadyExistsException,
    LicenseNumberAlreadyExistsException,
    LicenseValidityInPastException,
)
from app.models.driver import Driver
from app.repositories.driver import DriverRepository
from app.schemas.car import DocumentDetailSchema, PaginationSchema
from app.schemas.driver import (
    AssignedCarSchema,
    DriverCreateSchema,
    DriverDetailResponseSchema,
    DriverListQuerySchema,
    DriverListResponseSchema,
    GuarantorDetailSchema,
)
from app.storage import r2
from app.utils.dates import compute_expiry_status


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

    def get_driver(self, driver_id: str) -> DriverDetailResponseSchema:
        """Return the full detail for a single driver, or raise 404 if not found."""
        driver = self.repository.get_by_id(driver_id)
        if not driver:
            raise DriverNotFoundException(driver_id)

        documents = [
            DocumentDetailSchema(
                id=doc.id,
                type=doc.type,
                category=doc.category,
                expiry_date=doc.expiry_date,
                url=r2.generate_document_read_url(doc.url),
                expiry_status=compute_expiry_status(doc.expiry_date),
            )
            for doc in self.repository.get_driver_documents(driver_id)
        ]

        guarantors = [
            GuarantorDetailSchema(
                id=g.id,
                name=g.name,
                surnames=g.surnames,
                telephones=g.telephones,
                address=g.address,
                relation=g.relation,
                documents=[
                    DocumentDetailSchema(
                        id=doc.id,
                        type=doc.type,
                        category=doc.category,
                        expiry_date=doc.expiry_date,
                        url=r2.generate_document_read_url(doc.url),
                        expiry_status=compute_expiry_status(doc.expiry_date),
                    )
                    for doc in g.documents
                ],
            )
            for g in driver.guarantors
        ]

        assigned_car = None
        contract = self.repository.get_active_contract_for_driver(driver_id)
        if contract and contract.car:
            car = contract.car
            assigned_car = AssignedCarSchema(
                id=car.id,
                make=car.make,
                model=car.model,
                plate=car.plate,
                agency_image=car.agency_image,
            )

        return DriverDetailResponseSchema(
            id=driver.id,
            name=driver.name,
            surnames=driver.surnames,
            status=driver.status,
            telephones=driver.telephones,
            license_number=driver.license_number,
            license_validity=driver.license_validity,
            identification_number=driver.identification_number,
            address=driver.address,
            garage_address=driver.garage_address,
            photo=driver.photo,
            archived_at=driver.archived_at,
            created_at=driver.created_at,
            updated_at=driver.updated_at,
            documents=documents,
            guarantors=guarantors,
            assigned_car=assigned_car,
        )
