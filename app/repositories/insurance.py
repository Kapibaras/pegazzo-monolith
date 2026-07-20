from app.errors.database import DBOperationError
from app.models.car import Car, Insurance
from app.utils.logging_config import logger

from .abstract import DBRepository


class InsuranceRepository(DBRepository):
    """Insurance repository class."""

    def get_by_id(self, insurance_id: int) -> Insurance | None:
        """Retrieve an insurance provider by id."""
        return self.db.query(Insurance).filter(Insurance.id == insurance_id).first()

    def get_by_name(self, name: str) -> Insurance | None:
        """Retrieve an insurance provider by name."""
        return self.db.query(Insurance).filter(Insurance.name == name).first()

    def list_all(self, search: str | None = None) -> list[Insurance]:
        """List all insurance providers, optionally filtered by name."""
        query = self.db.query(Insurance)
        if search:
            query = query.filter(Insurance.name.ilike(f"%{search}%"))
        return query.all()

    def is_referenced_by_car(self, insurance_id: int) -> bool:
        """Check whether any car references this insurance provider."""
        return self.db.query(Car).filter(Car.insurance_provider_id == insurance_id).first() is not None

    def create(self, insurance: Insurance) -> Insurance:
        """Create a new insurance provider."""
        try:
            self.db.add(insurance)
            self.db.commit()
            self.db.refresh(insurance)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error creating insurance provider due to: %s", ex, exc_info=True)
            raise DBOperationError("Error creating insurance provider in the database") from ex
        return insurance

    def update(self, insurance: Insurance) -> Insurance:
        """Update an existing insurance provider."""
        try:
            self.db.commit()
            self.db.refresh(insurance)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error updating insurance provider %s due to: %s", insurance.id, ex, exc_info=True)
            raise DBOperationError("Error updating insurance provider in the database") from ex
        return insurance

    def delete(self, insurance: Insurance) -> None:
        """Delete an insurance provider."""
        try:
            self.db.delete(insurance)
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error("Error deleting insurance provider %s due to: %s", insurance.id, ex, exc_info=True)
            raise DBOperationError("Error deleting insurance provider in the database") from ex
