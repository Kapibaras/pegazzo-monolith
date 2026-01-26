from datetime import datetime, timezone

from app.models.balance import Transaction


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

    def reset(self):
        self.transactions = self.transactions[:1]

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
