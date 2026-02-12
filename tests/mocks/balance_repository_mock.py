from datetime import datetime, timezone

from app.enum.balance import SortOrder, TransactionSortBy
from app.models.balance import Transaction
from app.utils.periods import PeriodKey


class BalanceRepositoryMock:
    """Balance repository mock class."""

    def __init__(self):
        """Initialize the balance repository mock."""
        self.transactions = [
            Transaction(
                amount=1000,
                reference="MOCK_REF_001",
                date=datetime.now(timezone.utc),
                type="debit",
                description="Initial mock transaction",
                payment_method="cash",
            ),
        ]
        self.mapping: dict[tuple[str, int, int | None, int | None], object] = {}

    def reset(self):
        self.transactions = self.transactions[:1]
        self.mapping.clear()

    def get_by_reference(self, reference: str):
        return next((t for t in self.transactions if t.reference == reference), None)

    def create_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)
        return transaction

    def update_transaction(self, transaction: Transaction):
        for idx, t in enumerate(self.transactions):
            if t.reference == transaction.reference:
                self.transactions[idx] = transaction
                return transaction

        return None

    def delete_transaction(self, transaction: Transaction):
        self.transactions = [t for t in self.transactions if t.reference != transaction.reference]

    def get_month_year_metrics(
        self,
        _month: int | None = None,
        _year: int | None = None,
        **_kwargs,
    ):
        return None

    def get_period_metrics(self, *, period_type: str, year: int, month=None, week=None):
        return self.mapping.get((period_type, year, month, week))

    def get_metrics_for_keys(self, period_type: str, keys: list[PeriodKey]):
        """Return rows for bulk key lookup (trend endpoint)."""
        return [row for k in keys if (row := self.mapping.get((period_type, k.year, k.month, k.week)))]

    def count_transactions_in_range(self, start_dt: datetime, end_dt: datetime) -> int:
        """Count transactions in a given date range (inclusive end)."""
        return sum(1 for t in self.transactions if start_dt <= t.date <= end_dt)

    def list_transactions_in_range(
        self,
        start_dt: datetime,
        end_dt: datetime,
        limit: int,
        offset: int,
        sort_by: TransactionSortBy,
        sort_order: SortOrder,
    ) -> list[Transaction]:
        """List transactions in a given date range."""
        filtered = [t for t in self.transactions if start_dt <= t.date <= end_dt]

        sort_by_val = getattr(sort_by, "value", sort_by) or "date"
        sort_order_val = getattr(sort_order, "value", sort_order) or "desc"

        def sort_key(t: Transaction):
            match sort_by_val:
                case "amount":
                    return t.amount
                case "reference":
                    return t.reference
                case _:
                    return t.date

        reverse = str(sort_order_val).lower() == "desc"
        filtered.sort(key=sort_key, reverse=reverse)

        return filtered[offset : offset + limit]
