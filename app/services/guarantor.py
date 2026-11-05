from app.config.constants import GuarantorConfig
from app.errors.driver import DriverNotFoundException
from app.errors.guarantor import GuarantorLimitReachedException, GuarantorNotFoundException, GuarantorNotLinkedToDriverException
from app.models.driver import Guarantor
from app.repositories.driver import DriverRepository
from app.repositories.guarantor import GuarantorRepository
from app.schemas.address import format_address
from app.schemas.guarantor import GuarantorCreateSchema, GuarantorPatchSchema
from app.storage import r2


class GuarantorService:
    """Business logic for guarantor operations."""

    def __init__(self, repository: GuarantorRepository, driver_repository: DriverRepository):
        self.repository = repository
        self.driver_repository = driver_repository

    def create_guarantor(self, driver_id: str, data: GuarantorCreateSchema) -> Guarantor:
        """Create a new guarantor and link it to the given driver."""
        if not self.driver_repository.get_by_id(driver_id):
            raise DriverNotFoundException(driver_id)

        if self.repository.count_guarantors_for_driver(driver_id, lock=True) >= GuarantorConfig.MAX_PER_DRIVER:
            raise GuarantorLimitReachedException(driver_id, GuarantorConfig.MAX_PER_DRIVER)

        guarantor = Guarantor(
            name=data.name,
            surnames=data.surnames,
            telephones=data.telephones,
            address=format_address(data.address_fields),
            address_fields=data.address_fields.model_dump(),
            relation=data.relation,
        )
        return self.repository.create_and_link(guarantor, driver_id)

    def update_guarantor(self, driver_id: str, guarantor_id: int, data: GuarantorPatchSchema) -> Guarantor:
        """Update a guarantor scoped to a driver."""
        if not self.driver_repository.get_by_id(driver_id):
            raise DriverNotFoundException(driver_id)

        guarantor = self.repository.get_by_id(guarantor_id)
        if not guarantor:
            raise GuarantorNotFoundException(guarantor_id)

        if not self.repository.is_linked_to_driver(driver_id, guarantor_id):
            raise GuarantorNotLinkedToDriverException(guarantor_id, driver_id)

        if data.name is not None:
            guarantor.name = data.name
        if data.surnames is not None:
            guarantor.surnames = data.surnames
        if data.telephones is not None:
            guarantor.telephones = data.telephones
        if data.address_fields is not None:
            guarantor.address = format_address(data.address_fields)
            guarantor.address_fields = data.address_fields.model_dump()
        if data.relation is not None:
            guarantor.relation = data.relation

        return self.repository.update(guarantor)

    def delete_guarantor(self, driver_id: str, guarantor_id: int) -> None:
        """Unlink a guarantor from a driver; delete the guarantor if it becomes an orphan.

        The unlink and the orphan delete share one transaction. Files of deleted documents are
        moved to the `deleted/` storage prefix afterwards (best effort).
        """
        if not self.driver_repository.get_by_id(driver_id):
            raise DriverNotFoundException(driver_id)

        guarantor = self.repository.get_by_id(guarantor_id)
        if not guarantor:
            raise GuarantorNotFoundException(guarantor_id)

        if not self.repository.is_linked_to_driver(driver_id, guarantor_id):
            raise GuarantorNotLinkedToDriverException(guarantor_id, driver_id)

        document_keys = self.repository.unlink_and_delete_if_orphan(driver_id, guarantor)
        r2.soft_delete_documents_best_effort(document_keys)
