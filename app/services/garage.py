from app.errors.driver import DriverNotFoundException
from app.errors.garage import GarageNotFoundException
from app.models.driver import DriverGarage
from app.repositories.driver import DriverRepository
from app.repositories.garage import GarageRepository
from app.schemas.address import AddressFieldsSchema, format_address
from app.schemas.garage import GarageCreateSchema, GaragePatchSchema
from app.storage import r2


class GarageService:
    """Business logic for the garages of a driver."""

    def __init__(self, repository: GarageRepository, driver_repository: DriverRepository):
        self.repository = repository
        self.driver_repository = driver_repository

    @staticmethod
    def _apply_address(garage: DriverGarage, fields: AddressFieldsSchema) -> None:
        garage.address = format_address(fields)
        garage.address_fields = fields.model_dump()

    def _get_owned(self, driver_id: str, garage_id: int) -> DriverGarage:
        if not self.driver_repository.get_by_id(driver_id):
            raise DriverNotFoundException(driver_id)

        garage = self.repository.get_by_id(garage_id)
        # A garage of another driver is reported as not found so ids of other drivers are not revealed.
        if not garage or garage.driver_id != driver_id:
            raise GarageNotFoundException(garage_id)
        return garage

    def create_garage(self, driver_id: str, data: GarageCreateSchema) -> DriverGarage:
        """Create a garage for the given driver."""
        if not self.driver_repository.get_by_id(driver_id):
            raise DriverNotFoundException(driver_id)

        garage = DriverGarage(driver_id=driver_id)
        self._apply_address(garage, data.address_fields)
        return self.repository.create(garage)

    def update_garage(self, driver_id: str, garage_id: int, data: GaragePatchSchema) -> DriverGarage:
        """Replace the address of a garage. If it changed, its address proof is deleted."""
        garage = self._get_owned(driver_id, garage_id)
        address_changed = format_address(data.address_fields) != garage.address
        self._apply_address(garage, data.address_fields)
        updated = self.repository.update(garage)
        if address_changed:
            # The proof of the old address is no longer valid: a new one has to be uploaded.
            r2.soft_delete_documents_best_effort(self.repository.delete_address_proof(garage_id))
        return updated

    def delete_garage(self, driver_id: str, garage_id: int) -> None:
        """Delete a garage with its documents; their files move to the `deleted/` prefix (best effort)."""
        garage = self._get_owned(driver_id, garage_id)
        document_keys = self.repository.delete_with_documents(garage)
        r2.soft_delete_documents_best_effort(document_keys)
