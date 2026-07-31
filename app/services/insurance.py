from app.errors.insurance import (
    InsuranceInUseException,
    InsuranceNameAlreadyExistsException,
    InsuranceNotFoundException,
)
from app.models.car import Insurance
from app.repositories.insurance import InsuranceRepository
from app.schemas.insurance import InsurancePatchSchema, InsuranceSchema


class InsuranceService:
    """Insurance service class."""

    def __init__(self, repository: InsuranceRepository):
        self.repository = repository

    def create(self, data: InsuranceSchema) -> Insurance:
        """Create a new insurance provider."""
        if self.repository.get_by_name(data.name):
            raise InsuranceNameAlreadyExistsException(data.name)

        insurance = Insurance(
            name=data.name,
            telephones=data.telephones or [],
        )
        return self.repository.create(insurance)

    def list_all(self, search: str | None = None) -> list[Insurance]:
        """List all insurance providers."""
        return self.repository.list_all(search=search)

    def update(self, insurance_id: int, data: InsurancePatchSchema) -> Insurance:
        """Update an insurance provider partially."""
        insurance = self.repository.get_by_id(insurance_id)
        if not insurance:
            raise InsuranceNotFoundException(insurance_id)

        if data.name is not None and data.name != insurance.name:
            if self.repository.get_by_name(data.name):
                raise InsuranceNameAlreadyExistsException(data.name)
            insurance.name = data.name

        if data.telephones is not None:
            insurance.telephones = data.telephones

        return self.repository.update(insurance)

    def delete(self, insurance_id: int) -> None:
        """Delete an insurance provider if not in use."""
        insurance = self.repository.get_by_id(insurance_id)
        if not insurance:
            raise InsuranceNotFoundException(insurance_id)

        if self.repository.is_referenced_by_car(insurance_id):
            raise InsuranceInUseException(insurance_id)

        self.repository.delete(insurance)
