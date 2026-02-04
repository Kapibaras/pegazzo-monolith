from typing import Optional, Set, Tuple

from sqlalchemy import tuple_

from app.errors.database import DBOperationError
from app.models.balance import Transaction
from app.models.transaction_metrics import TransactionMetrics
from app.utils.logging_config import logger
from app.utils.periods import PeriodKey

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

    def get_period_metrics(
        self,
        period_type: str,
        year: int,
        month: int | None = None,
        week: int | None = None,
    ) -> Optional[TransactionMetrics]:
        """Get stored metrics for a given period key from transaction_metrics table."""

        q = self.db.query(TransactionMetrics).filter(
            TransactionMetrics.period_type == period_type,
            TransactionMetrics.year == year,
        )

        if period_type == "week":
            if week is None:
                return None
            q = q.filter(TransactionMetrics.week == week)

        elif period_type == "month":
            if month is None:
                return None
            q = q.filter(TransactionMetrics.month == month)

        elif period_type == "year":
            pass

        else:
            return None

        return q.first()

    def get_metrics_for_keys(self, period_type: str, keys: list[PeriodKey]) -> list[TransactionMetrics]:
        """Fetch precomputed transaction_metrics rows for the provided PeriodKeys."""
        if not keys:
            return []

        period_type = (period_type or "").strip().lower()

        q = self.db.query(TransactionMetrics).filter(TransactionMetrics.period_type == period_type)

        if period_type == "year":
            years: Set[int] = {k.year for k in keys}
            q = q.filter(TransactionMetrics.year.in_(years))

        elif period_type == "month":
            pairs: Set[Tuple[int, int]] = {(k.year, k.month) for k in keys if k.month is not None}
            if not pairs:
                return []

            q = q.filter(tuple_(TransactionMetrics.year, TransactionMetrics.month).in_(pairs))

        elif period_type == "week":
            triples: Set[Tuple[int, int, int]] = {
                (k.year, k.month, k.week) for k in keys if k.month is not None and k.week is not None
            }
            if not triples:
                return []

            q = q.filter(tuple_(TransactionMetrics.year, TransactionMetrics.month, TransactionMetrics.week).in_(triples))

        else:
            return []

        return q.all()
