from app.errors.database import DBOperationError
from app.models.car import Associate, associate_car
from app.utils.logging_config import logger

from .abstract import DBRepository


class AssociateRepository(DBRepository):
    """Associate repository class."""

    def get_by_id(self, associate_id: int) -> Associate | None:
        """Retrieve an associate by id."""
        return self.db.query(Associate).filter(Associate.id == associate_id).first()

    def list_all(self, search: str | None = None) -> list[Associate]:
        """List all associates, optionally filtered by name or surnames."""
        query = self.db.query(Associate)
        if search:
            query = query.filter(
                Associate.name.ilike(f"%{search}%") | Associate.surnames.ilike(f"%{search}%"),
            )
        return query.all()

    def has_linked_cars(self, associate_id: int) -> bool:
        """Check whether an associate has linked cars."""
        result = self.db.execute(
            associate_car.select().where(associate_car.c.associate_id == associate_id),
        ).first()
        return result is not None

    def create(self, associate: Associate) -> Associate:
        """Create a new associate."""
        try:
            self.db.add(associate)
            self.db.commit()
            self.db.refresh(associate)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error creating associate due to: %s", ex, exc_info=True)
            raise DBOperationError("Error creating associate in the database") from ex
        return associate

    def update(self, associate: Associate) -> Associate:
        """Update an existing associate."""
        try:
            self.db.commit()
            self.db.refresh(associate)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error updating associate %s due to: %s", associate.id, ex, exc_info=True)
            raise DBOperationError("Error updating associate in the database") from ex
        return associate

    def delete(self, associate: Associate) -> None:
        """Delete an associate."""
        try:
            self.db.delete(associate)
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error("Error deleting associate %s due to: %s", associate.id, ex, exc_info=True)
            raise DBOperationError("Error deleting associate in the database") from ex
