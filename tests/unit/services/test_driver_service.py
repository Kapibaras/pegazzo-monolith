from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError

from app.enum.crm import DriverStatus
from app.errors.database import DBOperationError
from app.errors.driver import (
    DriverIdAlreadyExistsException,
    IdentificationNumberAlreadyExistsException,
    LicenseNumberAlreadyExistsException,
)
from app.models.driver import Driver
from app.repositories.driver import DriverRepository
from app.schemas.driver import DriverCreateSchema, DriverPatchSchema
from app.services.driver import DriverService


class _DriverError(Exception):
    """Stand-in for a DBAPI error, optionally exposing psycopg2's `diag`."""

    def __init__(self, message: str, diag=None):
        super().__init__(message)
        if diag is not None:
            self.diag = diag


def _integrity_error(message: str, diag=None) -> IntegrityError:
    return IntegrityError("INSERT INTO driver ...", {}, _DriverError(message, diag))


@pytest.fixture
def driver_service_test_setup(request):
    """Set up DriverService with a mocked repository where no duplicates exist."""
    mock_repository = Mock(spec=DriverRepository)
    mock_repository.get_by_id.return_value = None
    mock_repository.get_by_identification_number.return_value = None
    mock_repository.get_by_license_number.return_value = None
    mock_repository.next_folio_number.return_value = 7
    request.cls.service = DriverService(repository=mock_repository)
    request.cls.mock_repo = mock_repository
    request.cls.data = DriverCreateSchema(
        name="Carlos",
        surnames="Ramírez Vega",
        status=DriverStatus.ACTIVE,
        telephones=["+525551234567"],
        license_number="LICNEW",
        license_validity=datetime.now(UTC) + timedelta(days=365),
        identification_number="NEWW010101HDFXXX01",
        address_fields={
            "street": "Calle Nueva",
            "exterior_number": "10",
            "neighborhood": "Centro",
            "postal_code": "06000",
            "municipality": "Cuauhtémoc",
            "state": "CDMX",
        },
    )


@pytest.mark.usefixtures("driver_service_test_setup")
class TestCreateDriverIntegrityError:
    """Race-condition fallback when the unique constraint fires on commit."""

    def test_message_detail_none_falls_back_to_error_text(self):
        self.mock_repo.create_driver.side_effect = _integrity_error(
            'duplicate key value violates unique constraint "ix_driver_license_number"',
            diag=SimpleNamespace(message_detail=None),
        )
        with pytest.raises(LicenseNumberAlreadyExistsException):
            self.service.create_driver(self.data)

    def test_message_detail_identifies_license_number(self):
        self.mock_repo.create_driver.side_effect = _integrity_error(
            "duplicate key",
            diag=SimpleNamespace(message_detail="Key (license_number)=(LICNEW) already exists."),
        )
        with pytest.raises(LicenseNumberAlreadyExistsException):
            self.service.create_driver(self.data)

    def test_without_diag_identifies_identification_number(self):
        self.mock_repo.create_driver.side_effect = _integrity_error(
            "UNIQUE constraint failed: driver.identification_number",
        )
        with pytest.raises(IdentificationNumberAlreadyExistsException):
            self.service.create_driver(self.data)

    def test_unknown_constraint_maps_to_driver_id(self):
        self.mock_repo.create_driver.side_effect = _integrity_error(
            'duplicate key value violates unique constraint "driver_pkey"',
            diag=SimpleNamespace(message_detail="Key (id)=(DRV-NEW) already exists."),
        )
        with pytest.raises(DriverIdAlreadyExistsException):
            self.service.create_driver(self.data)


@pytest.mark.usefixtures("driver_service_test_setup")
class TestUpdateDriverIntegrityError:
    """Race-condition fallback when the unique constraint fires on an update commit."""

    def _given_existing_driver(self):
        self.mock_repo.get_by_id.return_value = Driver(
            id="DRV-001",
            license_number="LIC001",
            identification_number="ID001",
            license_validity=datetime.now(UTC) + timedelta(days=365),
        )

    def test_message_detail_none_falls_back_to_error_text(self):
        self._given_existing_driver()
        self.mock_repo.update.side_effect = _integrity_error(
            'duplicate key value violates unique constraint "ix_driver_license_number"',
            diag=SimpleNamespace(message_detail=None),
        )
        with pytest.raises(LicenseNumberAlreadyExistsException):
            self.service.update_driver("DRV-001", DriverPatchSchema(license_number="LIC999"))

    def test_without_diag_identifies_identification_number(self):
        self._given_existing_driver()
        self.mock_repo.update.side_effect = _integrity_error(
            "UNIQUE constraint failed: driver.identification_number",
        )
        with pytest.raises(IdentificationNumberAlreadyExistsException):
            self.service.update_driver("DRV-001", DriverPatchSchema(identification_number="ZZZZ010101HDFXXX99"))

    def test_unknown_constraint_raises_db_operation_error(self):
        self._given_existing_driver()
        self.mock_repo.update.side_effect = _integrity_error(
            'violates check constraint "ck_driver_something"',
            diag=SimpleNamespace(message_detail=None),
        )
        with pytest.raises(DBOperationError):
            self.service.update_driver("DRV-001", DriverPatchSchema(name="Pedro"))
