from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from app.enum.crm import ImageEntityType
from app.errors.database import DBOperationError
from app.errors.driver import (
    DriverHasActiveContractException,
    DriverIdAlreadyExistsException,
    DriverNotArchivedException,
    DriverNotFoundException,
    IdentificationNumberAlreadyExistsException,
    LicenseNumberAlreadyExistsException,
    LicenseValidityInPastException,
)
from app.models.driver import Driver
from app.repositories.driver import DriverRepository
from app.schemas.address import format_address
from app.schemas.car import DocumentDetailSchema, PaginationSchema
from app.schemas.driver import (
    AssignedCarSchema,
    DriverCreateSchema,
    DriverDetailResponseSchema,
    DriverListQuerySchema,
    DriverListResponseSchema,
    DriverPatchSchema,
    DriverResponseSchema,
    DriverStatusSchema,
    GarageDetailSchema,
    GuarantorDetailSchema,
)
from app.schemas.user import ActionSuccess
from app.services.driver_folio import build_driver_folio
from app.storage import r2
from app.utils.dates import compute_expiry_status
from app.utils.logging_config import logger

_FOLIO_ATTEMPTS = 5


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
            pagination=PaginationSchema.build(params.page, params.limit, total),
        )

    def create_driver(self, data: DriverCreateSchema) -> Driver:
        """Create a new driver with validations."""
        if data.license_validity.date() < datetime.now(UTC).date():
            raise LicenseValidityInPastException

        if self.repository.get_by_identification_number(data.identification_number):
            raise IdentificationNumberAlreadyExistsException(data.identification_number)

        if self.repository.get_by_license_number(data.license_number):
            raise LicenseNumberAlreadyExistsException(data.license_number)

        folio = self._next_free_folio(data.name, data.surnames)

        driver = Driver(
            id=folio,
            name=data.name,
            surnames=data.surnames,
            status=data.status,
            telephones=data.telephones,
            license_number=data.license_number,
            license_validity=data.license_validity,
            identification_number=data.identification_number,
            address=format_address(data.address_fields),
            address_fields=data.address_fields.model_dump(),
        )

        try:
            return self.repository.create_driver(driver)
        except IntegrityError as ex:
            diag = getattr(ex.orig, "diag", None)
            detail = getattr(diag, "message_detail", None) or str(ex)
            if "license_number" in detail:
                raise LicenseNumberAlreadyExistsException(data.license_number) from ex
            if "identification_number" in detail:
                raise IdentificationNumberAlreadyExistsException(data.identification_number) from ex
            raise DriverIdAlreadyExistsException(folio) from ex

    def _next_free_folio(self, name: str, surnames: str) -> str:
        """Build the next folio from the global sequence, skipping ids already taken (including soft-deleted)."""
        for _ in range(_FOLIO_ATTEMPTS):
            folio = build_driver_folio(name, surnames, self.repository.next_folio_number())
            if not self.repository.get_by_id(folio, include_deleted=True):
                return folio
        raise DBOperationError("Could not generate a unique driver folio")

    @staticmethod
    def _to_document_detail(doc) -> DocumentDetailSchema:
        return DocumentDetailSchema(
            id=doc.id,
            type=doc.type,
            category=doc.category,
            expiry_date=doc.expiry_date,
            url=r2.generate_document_read_url(doc.url),
            expiry_status=compute_expiry_status(doc.expiry_date),
        )

    def get_driver(self, driver_id: str) -> DriverDetailResponseSchema:
        """Return the full detail for a single driver, or raise 404 if not found."""
        driver = self.repository.get_by_id(driver_id)
        if not driver:
            raise DriverNotFoundException(driver_id)

        documents = [self._to_document_detail(doc) for doc in driver.documents]

        guarantors = [
            GuarantorDetailSchema(
                id=g.id,
                name=g.name,
                surnames=g.surnames,
                telephones=g.telephones,
                address=g.address,
                address_fields=g.address_fields,
                relation=g.relation,
                documents=[self._to_document_detail(doc) for doc in g.documents],
            )
            for g in driver.guarantors
        ]

        garages = [
            GarageDetailSchema(
                id=garage.id,
                address=garage.address,
                address_fields=garage.address_fields,
                documents=[self._to_document_detail(doc) for doc in garage.documents],
            )
            for garage in driver.garages
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
            **DriverResponseSchema.model_validate(driver).model_dump(),
            documents=documents,
            guarantors=guarantors,
            garages=garages,
            assigned_car=assigned_car,
        )

    def update_driver(self, driver_id: str, data: DriverPatchSchema) -> Driver:
        """Update a driver's fields partially (excludes status)."""
        driver = self.repository.get_by_id(driver_id)
        if not driver:
            raise DriverNotFoundException(driver_id)

        if (
            data.license_validity is not None
            and data.license_validity != driver.license_validity
            and data.license_validity.date() < datetime.now(UTC).date()
        ):
            raise LicenseValidityInPastException

        if (
            data.identification_number is not None
            and data.identification_number != driver.identification_number
            and self.repository.get_by_identification_number(data.identification_number)
        ):
            raise IdentificationNumberAlreadyExistsException(data.identification_number)

        if (
            data.license_number is not None
            and data.license_number != driver.license_number
            and self.repository.get_by_license_number(data.license_number)
        ):
            raise LicenseNumberAlreadyExistsException(data.license_number)

        changes = data.model_dump(exclude_unset=True)
        if data.address_fields is not None:
            changes.pop("address_fields")
            driver.address = format_address(data.address_fields)
            driver.address_fields = data.address_fields.model_dump()
        for field, value in changes.items():
            setattr(driver, field, value)

        try:
            return self.repository.update(driver)
        except IntegrityError as ex:
            diag = getattr(ex.orig, "diag", None)
            detail = getattr(diag, "message_detail", None) or str(ex)
            if "license_number" in detail:
                raise LicenseNumberAlreadyExistsException(data.license_number) from ex
            if "identification_number" in detail:
                raise IdentificationNumberAlreadyExistsException(data.identification_number) from ex
            raise DBOperationError("Error updating driver in the database") from ex

    def change_driver_status(self, driver_id: str, data: DriverStatusSchema) -> Driver:
        """Change a driver's operational status."""
        driver = self.repository.get_by_id(driver_id)
        if not driver:
            raise DriverNotFoundException(driver_id)

        if driver.status == data.status:
            return driver

        driver.status = data.status
        return self.repository.update(driver)

    def archive_driver(self, driver_id: str) -> Driver:
        """Archive a driver by setting archived_at."""
        driver = self.repository.get_by_id(driver_id)
        if not driver:
            raise DriverNotFoundException(driver_id)

        if driver.archived_at is not None:
            return driver

        if self.repository.has_pending_contracts(driver_id):
            raise DriverHasActiveContractException(driver_id)

        return self.repository.archive_driver(driver)

    def unarchive_driver(self, driver_id: str) -> Driver:
        """Restore an archived driver."""
        driver = self.repository.get_by_id(driver_id)
        if not driver:
            raise DriverNotFoundException(driver_id)

        return self.repository.unarchive_driver(driver)

    def delete_driver(self, driver_id: str) -> ActionSuccess:
        """Delete an archived driver.

        Drivers with history (contracts, events or incidences) are soft-deleted and keep all their
        data. Drivers without history are permanently deleted with cascade cleanup; the files of
        their deleted documents are moved to the `deleted/` storage prefix (best effort).
        """
        driver = self.repository.get_by_id(driver_id)
        if not driver:
            raise DriverNotFoundException(driver_id)

        if driver.archived_at is None:
            raise DriverNotArchivedException(driver_id)

        if self.repository.has_history(driver_id):
            self.repository.soft_delete_driver(driver)
            return ActionSuccess(message=f"Driver '{driver_id}' was deleted (history preserved)")

        photo = driver.photo
        document_keys = self.repository.cascade_delete_driver(driver)
        r2.soft_delete_documents_best_effort(document_keys)
        self._cleanup_photo(driver_id, photo)
        return ActionSuccess(message=f"Driver '{driver_id}' was deleted")

    @staticmethod
    def _cleanup_photo(driver_id: str, photo: str | None) -> None:
        """Move the driver's photo to `deleted/` (best effort). Only files under the driver's own folder are touched."""
        if not photo:
            return
        own_prefix = r2.get_image_public_url(f"{ImageEntityType.DRIVER_PHOTO}/{driver_id}/")
        if not photo.startswith(own_prefix):
            logger.warning(
                "Skipping photo '%s' of driver '%s': it is not stored under the driver's own folder",
                photo,
                driver_id,
            )
            return
        try:
            r2.soft_delete_image(photo)
        except Exception as ex:  # noqa: BLE001, RUF100 - best-effort cleanup must never fail the request
            logger.error("Storage cleanup failed for '%s': %s", photo, ex, exc_info=True)
