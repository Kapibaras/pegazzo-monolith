from sqlalchemy import func

from app.errors.database import DBOperationError
from app.models.driver import Guarantor, driver_guarantor_table
from app.utils.logging_config import logger

from .abstract import DBRepository


class GuarantorRepository(DBRepository):
    """Data-access layer for the Guarantor entity."""

    def get_by_id(self, guarantor_id: int) -> Guarantor | None:
        """Retrieve a guarantor by id."""
        return self.db.query(Guarantor).filter(Guarantor.id == guarantor_id).first()

    def create(self, guarantor: Guarantor) -> Guarantor:
        """Persist a new guarantor to the database."""
        try:
            self.db.add(guarantor)
            self.db.commit()
            self.db.refresh(guarantor)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error creating guarantor due to: %s", ex, exc_info=True)
            raise DBOperationError("Error creating guarantor in the database") from ex
        return guarantor

    def update(self, guarantor: Guarantor) -> Guarantor:
        """Update an existing guarantor."""
        try:
            self.db.commit()
            self.db.refresh(guarantor)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error updating guarantor %s due to: %s", guarantor.id, ex, exc_info=True)
            raise DBOperationError("Error updating guarantor in the database") from ex
        return guarantor

    def delete(self, guarantor: Guarantor) -> None:
        """Delete a guarantor."""
        try:
            self.db.delete(guarantor)
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error("Error deleting guarantor %s due to: %s", guarantor.id, ex, exc_info=True)
            raise DBOperationError("Error deleting guarantor in the database") from ex

    def link_to_driver(self, driver_id: str, guarantor_id: int) -> None:
        """Insert a row into the driver_guarantor M2M table.

        A guarantor is scoped to a single driver. Although the M2M table
        technically allows many-to-many, business rules restrict each
        guarantor to exactly one driver. This guard prevents accidental
        sharing if a future endpoint attempts to reuse an existing guarantor.
        """
        if self.count_linked_drivers(guarantor_id) > 0:
            msg = f"Guarantor {guarantor_id} is already linked to a driver"
            raise DBOperationError(msg)

        try:
            self.db.execute(
                driver_guarantor_table.insert().values(driver_id=driver_id, guarantor_id=guarantor_id),
            )
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error("Error linking guarantor %s to driver %s: %s", guarantor_id, driver_id, ex, exc_info=True)
            raise DBOperationError("Error linking guarantor to driver") from ex

    def unlink_from_driver(self, driver_id: str, guarantor_id: int) -> None:
        """Remove the M2M link between a driver and a guarantor."""
        try:
            self.db.execute(
                driver_guarantor_table.delete().where(
                    (driver_guarantor_table.c.driver_id == driver_id)
                    & (driver_guarantor_table.c.guarantor_id == guarantor_id),
                ),
            )
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error("Error unlinking guarantor %s from driver %s: %s", guarantor_id, driver_id, ex, exc_info=True)
            raise DBOperationError("Error unlinking guarantor from driver") from ex

    def is_linked_to_driver(self, driver_id: str, guarantor_id: int) -> bool:
        """Check whether a guarantor is linked to a specific driver."""
        result = self.db.execute(
            driver_guarantor_table.select().where(
                (driver_guarantor_table.c.driver_id == driver_id)
                & (driver_guarantor_table.c.guarantor_id == guarantor_id),
            ),
        ).first()
        return result is not None

    def count_guarantors_for_driver(self, driver_id: str) -> int:
        """Return how many guarantors are linked to this driver."""
        return (
            self.db.query(func.count())
            .select_from(driver_guarantor_table)
            .filter(driver_guarantor_table.c.driver_id == driver_id)
            .scalar()
        )

    def count_linked_drivers(self, guarantor_id: int) -> int:
        """Return how many drivers are linked to this guarantor."""
        return (
            self.db.query(func.count())
            .select_from(driver_guarantor_table)
            .filter(driver_guarantor_table.c.guarantor_id == guarantor_id)
            .scalar()
        )
