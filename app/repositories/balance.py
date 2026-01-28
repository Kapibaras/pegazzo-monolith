from app.errors.database import DBOperationError
from app.models.balance import Transaction
from app.models.transaction_metrics import TransactionMetrics
from app.utils.logging_config import logger

from .abstract import DBRepository


class BalanceRepository(DBRepository):
    """Balance repository class."""

    def create_transaction(self, transaction: Transaction):
        """Create a new transaction."""
        try:
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
        except Exception as ex:
            self.db.rollback()
            logger.error(f"Error creating transaction {transaction.reference} due to: {ex}")
            raise DBOperationError(f"Failed to create transaction with reference {transaction.reference}") from ex

        return transaction

    def get_by_reference(self, reference: str):
        """Retrieve a transaction by their reference.

        Args: username (str): The username of the user to retrieve.
        """
        return self.db.query(Transaction).filter(Transaction.reference == reference).first()

    def delete_transaction(self, transaction: Transaction):
        """Delete a transaction."""
        try:
            self.db.delete(transaction)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise DBOperationError("Error deleting transaction") from e

    def update_transaction(self, transaction: Transaction):
        """Update a transaction."""

        try:
            self.db.commit()
            self.db.refresh(transaction)
        except Exception as ex:
            self.db.rollback()
            logger.error(f"Error updating transaction {transaction.reference} due to: {ex}")
            raise DBOperationError("Error updating transaction in the database")

        return self.get_by_reference(transaction.reference)

    def get_month_year_metrics(self, month: int, year: int):
        """Get metrics for a specific month."""
        return (
            self.db.query(TransactionMetrics).filter(TransactionMetrics.month == month, TransactionMetrics.year == year).first()
        )
