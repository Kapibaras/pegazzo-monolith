from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError

from app.enum.crm import DriverStatus
from app.errors.driver import (
    DriverIdAlreadyExistsException,
    IdentificationNumberAlreadyExistsException,
    LicenseNumberAlreadyExistsException,
)
from app.repositories.driver import DriverRepository
from app.schemas.driver import DriverCreateSchema
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
    request.cls.service = DriverService(repository=mock_repository)
    request.cls.mock_repo = mock_repository
    request.cls.data = DriverCreateSchema(
        id="DRV-NEW",
        name="Carlos",
        surnames="Ramírez Vega",
        status=DriverStatus.ACTIVE,
        telephones=["+525551234567"],
        license_number="LICNEW",
        license_validity=datetime.now(UTC) + timedelta(days=365),
        identification_number="IDNEW",
        address="Calle Nueva #10",
        garage_address=["Calle Garage #20"],
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
