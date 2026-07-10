from app.errors.associate import AssociateInUseException, AssociateNotFoundException
from app.models.car import Associate
from app.repositories.associate import AssociateRepository
from app.schemas.associate import AssociatePatchSchema, AssociateSchema


class AssociateService:
    """Associate service class."""

    def __init__(self, repository: AssociateRepository):
        self.repository = repository

    def create(self, data: AssociateSchema) -> Associate:
        """Create a new associate."""
        associate = Associate(
            name=data.name,
            surnames=data.surnames,
            telephones=data.telephones or [],
        )
        return self.repository.create(associate)

    def list_all(self, search: str | None = None) -> list[Associate]:
        """List all associates."""
        return self.repository.list_all(search=search)

    def update(self, associate_id: int, data: AssociatePatchSchema) -> Associate:
        """Partially update an associate."""
        associate = self.repository.get_by_id(associate_id)
        if not associate:
            raise AssociateNotFoundException(associate_id)

        if data.name is not None:
            associate.name = data.name
        if data.surnames is not None:
            associate.surnames = data.surnames
        if data.telephones is not None:
            associate.telephones = data.telephones

        return self.repository.update(associate)

    def delete(self, associate_id: int) -> None:
        """Delete an associate if not linked to any cars."""
        associate = self.repository.get_by_id(associate_id)
        if not associate:
            raise AssociateNotFoundException(associate_id)

        if self.repository.has_linked_cars(associate_id):
            raise AssociateInUseException(associate_id)

        self.repository.delete(associate)
