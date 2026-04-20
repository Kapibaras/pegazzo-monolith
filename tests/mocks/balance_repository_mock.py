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
                status="CONFIRMED",
                category="Otro",
            ),
        ]
        self.mapping: dict[tuple[str, int, int | None, int | None], object] = {}

    def reset(self):
        self.transactions = [
            Transaction(
                amount=1000,
                reference="MOCK_REF_001",
                date=datetime.now(timezone.utc),
                type="debit",
                description="Initial mock transaction",
                payment_method="cash",
                status="CONFIRMED",
                category="Otro",
            )
        ]
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

    def count_transactions_in_range(self, start_dt: datetime, end_dt: datetime, status=None) -> int:
        """Count transactions in a given date range (inclusive end)."""
        filtered = [t for t in self.transactions if start_dt <= t.date <= end_dt]
        if status is not None:
            filtered = [t for t in filtered if t.status == status]
        return len(filtered)

    def list_transactions_in_range(
        self,
        start_dt: datetime,
        end_dt: datetime,
        limit: int,
        offset: int,
        sort_by: TransactionSortBy,
        sort_order: SortOrder,
        status=None,
    ) -> list[Transaction]:
        """List transactions in a given date range."""
        filtered = [t for t in self.transactions if start_dt <= t.date <= end_dt]
        if status is not None:
            filtered = [t for t in filtered if t.status == status]

        sort_by_val = sort_by.value if isinstance(sort_by, TransactionSortBy) else sort_by or "date"
        sort_order_val = sort_order.value if isinstance(sort_order, SortOrder) else sort_order or "desc"

        reverse = sort_order_val.lower() == "desc"
        filtered.sort(
            key=lambda t: t.amount if sort_by_val == "amount" else t.reference if sort_by_val == "reference" else t.date,
            reverse=reverse,
        )
        return filtered[offset : offset + limit]
