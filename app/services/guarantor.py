from app.config.constants import MAX_GUARANTORS_PER_DRIVER
from app.errors.driver import DriverNotFoundException
from app.errors.guarantor import GuarantorLimitReachedException, GuarantorNotFoundException, GuarantorNotLinkedToDriverException
from app.models.driver import Guarantor
from app.repositories.driver import DriverRepository
from app.repositories.guarantor import GuarantorRepository
from app.schemas.guarantor import GuarantorCreateSchema, GuarantorPatchSchema


class GuarantorService:
    """Business logic for guarantor operations."""

    def __init__(self, repository: GuarantorRepository, driver_repository: DriverRepository):
        self.repository = repository
        self.driver_repository = driver_repository

    def create_guarantor(self, driver_id: str, data: GuarantorCreateSchema) -> Guarantor:
        """Create a new guarantor and link it to the given driver."""
        if not self.driver_repository.get_by_id(driver_id):
            raise DriverNotFoundException(driver_id)

        if self.repository.count_guarantors_for_driver(driver_id) >= MAX_GUARANTORS_PER_DRIVER:
            raise GuarantorLimitReachedException(driver_id, MAX_GUARANTORS_PER_DRIVER)

        guarantor = Guarantor(
            name=data.name,
            surnames=data.surnames,
            telephones=data.telephones,
            address=data.address,
            relation=data.relation,
        )
        guarantor = self.repository.create(guarantor)
        self.repository.link_to_driver(driver_id, guarantor.id)
        return guarantor

    def update_guarantor(self, guarantor_id: int, data: GuarantorPatchSchema) -> Guarantor:
        """Update a guarantor partially."""
        guarantor = self.repository.get_by_id(guarantor_id)
        if not guarantor:
            raise GuarantorNotFoundException(guarantor_id)

        if data.name is not None:
            guarantor.name = data.name
        if data.surnames is not None:
            guarantor.surnames = data.surnames
        if data.telephones is not None:
            guarantor.telephones = data.telephones
        if data.address is not None:
            guarantor.address = data.address
        if data.relation is not None:
            guarantor.relation = data.relation

        return self.repository.update(guarantor)

    def delete_guarantor(self, driver_id: str, guarantor_id: int) -> None:
        """Unlink a guarantor from a driver; delete the guarantor if it becomes an orphan."""
        if not self.driver_repository.get_by_id(driver_id):
            raise DriverNotFoundException(driver_id)

        guarantor = self.repository.get_by_id(guarantor_id)
        if not guarantor:
            raise GuarantorNotFoundException(guarantor_id)

        if not self.repository.is_linked_to_driver(driver_id, guarantor_id):
            raise GuarantorNotLinkedToDriverException(guarantor_id, driver_id)

        self.repository.unlink_from_driver(driver_id, guarantor_id)

        if self.repository.count_linked_drivers(guarantor_id) == 0:
            self.repository.delete(guarantor)
