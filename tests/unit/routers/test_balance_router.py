from datetime import datetime, timezone
from decimal import Decimal

from app.models.balance import Transaction
from app.models.transaction_metrics import TransactionMetrics
from app.schemas.balance import (
    BalanceMetricsDetailedResponseSchema,
    BalanceMetricsSimpleResponseSchema,
    BalanceTransactionsResponseSchema,
    BalanceTrendResponseSchema,
    TransactionResponseSchema,
)
from app.schemas.user import ActionSuccess


class TestBalanceRouter:
    """Tests for Balance Router endpoints (with auth required)."""

    def test_update_transaction_amount(self, authorized_client):
        """Test updating transaction amount."""

        reference = "MOCK_REF_001"
        update_data = {
            "amount": 2500,
        }

        response = authorized_client.patch(
            f"/pegazzo/management/balance/transaction/{reference}",
            json=update_data,
        )

        assert response.status_code == 200

        data = response.json()
        assert data["reference"] == reference
        assert data["amount"] == 2500

    def test_update_transaction_not_found(self, authorized_client):
        """Test updating a non-existing transaction."""

        reference = "TX-999"
        update_data = {"amount": 1000}

        response = authorized_client.patch(
            f"/pegazzo/management/balance/transaction/{reference}",
            json=update_data,
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == f"Transaction with reference '{reference}' was not found"

    def test_update_transaction_description_and_payment_method(self, authorized_client):
        """Test updating transaction description and payment method."""

        reference = "MOCK_REF_001"
        update_data = {
            "description": "Pago actualizado",
            "payment_method": "cash",
        }

        response = authorized_client.patch(
            f"/pegazzo/management/balance/transaction/{reference}",
            json=update_data,
        )

        assert response.status_code == 200

        data = response.json()
        assert data["reference"] == reference
        assert data["description"] == "Pago actualizado"
        assert data["paymentMethod"] == "cash"

    def test_get_transaction_success(self, authorized_client):
        """Authenticated user can get an existing transaction."""

        create_response = authorized_client.post(
            "/pegazzo/management/balance/transaction",
            json={
                "amount": 1500,
                "type": "debit",
                "description": "Pago de material",
                "payment_method": "cash",
                "category": "Materiales",
            },
        )
        assert create_response.status_code == 201
        reference = create_response.json()["reference"]

        response = authorized_client.get(f"/pegazzo/management/balance/transaction/{reference}")

        assert response.status_code == 200
        assert TransactionResponseSchema.model_validate(response.json())

    def test_get_transaction_unauthorized(self, client):
        """Unauthenticated user cannot get a transaction."""

        response = client.get("/pegazzo/management/balance/transaction/ANYREF")

        assert response.status_code == 401

    def test_get_transaction_not_found(self, authorized_client):
        """Authenticated user gets 404 for invalid reference."""

        response = authorized_client.get("/pegazzo/management/balance/transaction/INVALID_REF")

        assert response.status_code == 404
        assert response.json()["detail"] == "Transaction with reference 'INVALID_REF' was not found"

    def test_create_transaction_success(self, authorized_client):
        """Authenticated user can create a transaction."""

        response = authorized_client.post(
            "/pegazzo/management/balance/transaction",
            json={
                "amount": 1500,
                "date": "2025-01-01T10:30:00Z",
                "type": "debit",
                "description": "Pago de material",
                "payment_method": "cash",
                "category": "Materiales",
            },
        )

        assert response.status_code == 201
        assert TransactionResponseSchema.model_validate(response.json())

    def test_create_transaction_unauthorized(self, client):
        """Unauthenticated user cannot create a transaction."""

        response = client.post(
            "/pegazzo/management/balance/transaction",
            json={
                "amount": 100,
                "type": "debit",
                "description": "No auth",
                "payment_method": "cash",
            },
        )

        assert response.status_code == 401

    def test_create_transaction_invalid_body(self, authorized_client):
        """Authenticated user but invalid payload."""

        response = authorized_client.post(
            "/pegazzo/management/balance/transaction",
            json={
                "amount": "NOT_A_NUMBER",
            },
        )

        assert response.status_code == 422

    def test_delete_transaction_success(self, authorized_client):
        """Authenticated user can delete a transaction."""

        create_response = authorized_client.post(
            "/pegazzo/management/balance/transaction",
            json={
                "amount": 500,
                "type": "debit",
                "description": "To delete",
                "payment_method": "cash",
                "category": "Otro",
            },
        )
        reference = create_response.json()["reference"]

        response = authorized_client.delete(f"/pegazzo/management/balance/transaction/{reference}")

        assert response.status_code == 200
        assert ActionSuccess.model_validate(response.json())

    def test_delete_transaction_not_found(self, authorized_client):
        """Authenticated user deleting non-existent transaction."""

        response = authorized_client.delete("/pegazzo/management/balance/transaction/NO_EXIST")

        assert response.status_code == 404
        assert response.json()["detail"] == "Transaction with reference 'NO_EXIST' was not found"

    def test_delete_transaction_unauthorized(self, client):
        """Unauthenticated user cannot delete a transaction."""

        response = client.delete("/pegazzo/management/balance/transaction/ANYREF")

        assert response.status_code == 401

    def test_get_simple_metrics_default_current_month(self, authorized_client):
        """Should return metrics for current month when no params are provided."""

        response = authorized_client.get(
            "/pegazzo/management/balance/metrics/simple",
        )

        assert response.status_code == 200

        data = response.json()
        assert BalanceMetricsSimpleResponseSchema.model_validate(data)

        now = datetime.now(timezone.utc)
        assert data["period"]["month"] == now.month
        assert data["period"]["year"] == now.year

    def test_get_simple_metrics_with_month_and_year(self, authorized_client):
        """Should return metrics for a specific month and year."""

        response = authorized_client.get(
            "/pegazzo/management/balance/metrics/simple?month=1&year=2025",
        )

        assert response.status_code == 200

        data = response.json()
        assert BalanceMetricsSimpleResponseSchema.model_validate(data)

        assert data["period"]["month"] == 1
        assert data["period"]["year"] == 2025

    def test_get_simple_metrics_missing_month(self, authorized_client):
        """Should return 400 if year is provided without month."""

        response = authorized_client.get("/pegazzo/management/balance/metrics/simple?year=2025")
        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Invalid metrics period or missing required parameters. "
            "Valid periods are 'week', 'month', or 'year', with their corresponding parameters."
        )

    def test_get_simple_metrics_missing_year(self, authorized_client):
        response = authorized_client.get("/pegazzo/management/balance/metrics/simple?month=1")
        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Invalid metrics period or missing required parameters. "
            "Valid periods are 'week', 'month', or 'year', with their corresponding parameters."
        )

    def test_get_simple_metrics_invalid_month(self, authorized_client):
        """Should return 422 if month is outside valid range."""

        response = authorized_client.get(
            "/pegazzo/management/balance/metrics/simple?month=13&year=2025",
        )

        assert response.status_code == 422

    def test_get_simple_metrics_unauthorized(self, client):
        """Unauthenticated user cannot access metrics."""

        response = client.get(
            "/pegazzo/management/balance/metrics/simple",
        )

        assert response.status_code == 401

    def test_get_management_metrics_week_success(self, authorized_client):
        authorized_client.balance_repo.mapping[("week", 2026, 1, 5)] = TransactionMetrics(
            period_type="week",
            year=2026,
            month=1,
            week=5,
            total_income=Decimal("500"),
            total_expense=Decimal("200"),
            balance=Decimal("300"),
            transaction_count=3,
            payment_method_breakdown={
                "credit": {"amounts": {"cash": 200}, "percentages": {"cash": 100}},
                "debit": {"amounts": {"transfer": 300}, "percentages": {"transfer": 100}},
            },
            weekly_average_income=Decimal("125"),
            weekly_average_expense=Decimal("50"),
            income_expense_ratio=Decimal("2.5"),
        )

        r = authorized_client.get("/pegazzo/management/balance/metrics?period=week&week=5&month=1&year=2026")
        assert r.status_code == 200
        BalanceMetricsDetailedResponseSchema.model_validate(r.json())

    def test_get_management_metrics_month_success(self, authorized_client):
        authorized_client.balance_repo.mapping[("month", 2026, 1, None)] = TransactionMetrics(
            period_type="month",
            year=2026,
            month=1,
            total_income=Decimal("800"),
            total_expense=Decimal("300"),
            balance=Decimal("500"),
            transaction_count=5,
            payment_method_breakdown={},
            weekly_average_income=Decimal("200"),
            weekly_average_expense=Decimal("75"),
            income_expense_ratio=Decimal("2.66"),
        )

        r = authorized_client.get("/pegazzo/management/balance/metrics?period=month&month=1&year=2026")
        assert r.status_code == 200
        BalanceMetricsDetailedResponseSchema.model_validate(r.json())

    def test_get_management_metrics_year_success(self, authorized_client):
        authorized_client.balance_repo.mapping[("year", 2026, None, None)] = TransactionMetrics(
            period_type="year",
            year=2026,
            total_income=Decimal("1200"),
            total_expense=Decimal("400"),
            balance=Decimal("800"),
            transaction_count=12,
            payment_method_breakdown={},
            weekly_average_income=Decimal("100"),
            weekly_average_expense=Decimal("33"),
            income_expense_ratio=Decimal("3.0"),
        )

        r = authorized_client.get("/pegazzo/management/balance/metrics?period=year&year=2026")
        assert r.status_code == 200
        BalanceMetricsDetailedResponseSchema.model_validate(r.json())

    def test_get_management_metrics_invalid_period_422(self, authorized_client):
        response = authorized_client.get("/pegazzo/management/balance/metrics?period=INVALID&year=2026")

        assert response.status_code == 422
        detail = response.json()["detail"]
        assert isinstance(detail, list)
        assert detail[0]["msg"] == "Input should be 'week', 'month' or 'year'"
        assert detail[0]["loc"] == ["query", "period"]

    def test_get_management_metrics_week_missing_params_400(self, authorized_client):
        """Week requires week + year (and your schema also requires month)."""

        response = authorized_client.get(
            "/pegazzo/management/balance/metrics?period=week&year=2026",
        )

        assert response.status_code == 400
        assert "Invalid metrics period" in response.json()["detail"]

    def test_get_management_metrics_month_missing_params_400(self, authorized_client):
        """Month requires month + year."""

        response = authorized_client.get(
            "/pegazzo/management/balance/metrics?period=month&month=1",
        )

        assert response.status_code == 400
        assert "Invalid metrics period" in response.json()["detail"]

    def test_get_management_metrics_year_missing_params_400(self, authorized_client):
        """Year requires year."""

        response = authorized_client.get(
            "/pegazzo/management/balance/metrics?period=year",
        )

        assert response.status_code == 400
        assert "Invalid metrics period" in response.json()["detail"]

    def test_get_management_metrics_invalid_week_422(self, authorized_client):
        """Pydantic should reject invalid week range."""

        response = authorized_client.get(
            "/pegazzo/management/balance/metrics?period=week&week=60&month=1&year=2026",
        )
        assert response.status_code == 422

    def test_get_management_metrics_invalid_month_422(self, authorized_client):
        """Pydantic should reject invalid month range."""

        response = authorized_client.get(
            "/pegazzo/management/balance/metrics?period=month&month=13&year=2026",
        )
        assert response.status_code == 422

    def test_get_management_metrics_unauthorized(self, client):
        """Unauthenticated user cannot access detailed metrics."""

        response = client.get(
            "/pegazzo/management/balance/metrics?period=year&year=2026",
        )

        assert response.status_code == 401

    def test_get_trend_month_default_limit_success(self, authorized_client):
        """Default month limit = 6, returns chronological data and fills missing periods with zeros."""

        authorized_client.balance_repo.mapping[("month", 2026, 1, None)] = TransactionMetrics(
            period_type="month",
            year=2026,
            month=1,
            total_income=Decimal("4500"),
            total_expense=Decimal("2200"),
        )

        r = authorized_client.get("/pegazzo/management/balance/metrics/trend?period=month")
        assert r.status_code == 200

        payload = r.json()
        assert BalanceTrendResponseSchema.model_validate(payload)

        assert payload["periodType"] == "month"
        assert len(payload["data"]) == 6

        starts = [item["periodStart"] for item in payload["data"]]
        assert starts == sorted(starts)

        incomes = [item["totalIncome"] for item in payload["data"]]
        expenses = [item["totalExpense"] for item in payload["data"]]
        assert any(v == 0 for v in incomes)
        assert any(v == 0 for v in expenses)
        assert any(v > 0 for v in incomes)

    def test_get_trend_month_custom_limit_success(self, authorized_client):
        """User can override limit; still chronological and length matches limit."""

        authorized_client.balance_repo.mapping[("month", 2025, 12, None)] = TransactionMetrics(
            period_type="month",
            year=2025,
            month=12,
            total_income=Decimal("5000"),
            total_expense=Decimal("2500"),
        )

        r = authorized_client.get("/pegazzo/management/balance/metrics/trend?period=month&limit=3")
        assert r.status_code == 200

        payload = r.json()
        assert BalanceTrendResponseSchema.model_validate(payload)

        assert payload["periodType"] == "month"
        assert len(payload["data"]) == 3

        starts = [item["periodStart"] for item in payload["data"]]
        assert starts == sorted(starts)

    def test_get_trend_week_default_limit_success(self, authorized_client):
        """Default week limit = 8."""

        authorized_client.balance_repo.mapping[("week", 2026, 1, 5)] = TransactionMetrics(
            period_type="week",
            year=2026,
            month=1,
            week=5,
            total_income=Decimal("500"),
            total_expense=Decimal("200"),
        )

        r = authorized_client.get("/pegazzo/management/balance/metrics/trend?period=week")
        assert r.status_code == 200

        payload = r.json()
        assert BalanceTrendResponseSchema.model_validate(payload)

        assert payload["periodType"] == "week"
        assert len(payload["data"]) == 8

        starts = [item["periodStart"] for item in payload["data"]]
        assert starts == sorted(starts)

    def test_get_trend_year_default_limit_success(self, authorized_client):
        """Default year limit = 3."""

        authorized_client.balance_repo.mapping[("year", 2026, None, None)] = TransactionMetrics(
            period_type="year",
            year=2026,
            total_income=Decimal("12000"),
            total_expense=Decimal("4000"),
        )

        r = authorized_client.get("/pegazzo/management/balance/metrics/trend?period=year")
        assert r.status_code == 200

        payload = r.json()
        assert BalanceTrendResponseSchema.model_validate(payload)

        assert payload["periodType"] == "year"
        assert len(payload["data"]) == 3

        starts = [item["periodStart"] for item in payload["data"]]
        assert starts == sorted(starts)

    def test_get_trend_invalid_period_422(self, authorized_client):
        """Pydantic should reject invalid enum value."""

        r = authorized_client.get("/pegazzo/management/balance/metrics/trend?period=INVALID")
        assert r.status_code == 422

        detail = r.json()["detail"]
        assert isinstance(detail, list)
        assert detail[0]["loc"] == ["query", "period"]
        assert "week" in detail[0]["msg"]
        assert "month" in detail[0]["msg"]
        assert "year" in detail[0]["msg"]

    def test_get_trend_invalid_limit_low_422(self, authorized_client):
        """Limit < 1 should be rejected by schema."""
        r = authorized_client.get("/pegazzo/management/balance/metrics/trend?period=month&limit=0")
        assert r.status_code == 422

    def test_get_trend_invalid_limit_high_422(self, authorized_client):
        """Limit > 100 should be rejected by schema."""
        r = authorized_client.get("/pegazzo/management/balance/metrics/trend?period=month&limit=101")
        assert r.status_code == 422

    def test_get_trend_unauthorized(self, client):
        """Unauthenticated user cannot access trend metrics."""
        r = client.get("/pegazzo/management/balance/metrics/trend?period=month")
        assert r.status_code == 401

    def test_get_transactions_month_success_default_sort_date_desc(self, authorized_client):
        """Month success: default page=1, limit=10, sort_by=date desc."""
        authorized_client.balance_repo.reset()

        authorized_client.balance_repo.transactions = [
            Transaction(
                amount=100,
                reference="TRX-001",
                date=datetime(2026, 1, 5, 10, 30, tzinfo=timezone.utc),
                type="debit",
                description="Tx 1",
                payment_method="cash",
                status="CONFIRMED",
                category="Otro",
            ),
            Transaction(
                amount=200,
                reference="TRX-002",
                date=datetime(2026, 1, 10, 10, 30, tzinfo=timezone.utc),
                type="debit",
                description="Tx 2",
                payment_method="cash",
                status="CONFIRMED",
                category="Otro",
            ),
            Transaction(
                amount=300,
                reference="TRX-003",
                date=datetime(2026, 1, 1, 10, 30, tzinfo=timezone.utc),
                type="debit",
                description="Tx 3",
                payment_method="cash",
                status="CONFIRMED",
                category="Otro",
            ),
        ]

        r = authorized_client.get("/pegazzo/management/balance/transactions?period=month&month=1&year=2026")
        assert r.status_code == 200

        payload = r.json()
        assert BalanceTransactionsResponseSchema.model_validate(payload)

        assert payload["pagination"]["page"] == 1
        assert payload["pagination"]["limit"] == 10
        assert payload["pagination"]["total"] == 3
        assert payload["pagination"]["totalPages"] == 1

        refs = [t["reference"] for t in payload["transactions"]]
        assert refs == ["TRX-002", "TRX-001", "TRX-003"]

    def test_get_transactions_month_pagination_second_page(self, authorized_client):
        """Pagination: total=15, limit=10 => page=2 returns 5."""
        authorized_client.balance_repo.reset()

        txs: list[Transaction] = []
        txs = [
            Transaction(
                amount=100 + i,
                reference=f"TRX-{i:03d}",
                date=datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
                type="debit",
                description="Bulk",
                payment_method="cash",
                status="CONFIRMED",
                category="Otro",
            )
            for i in range(15)
        ]

        authorized_client.balance_repo.transactions = txs

        r = authorized_client.get(
            "/pegazzo/management/balance/transactions?period=month&month=1&year=2026&page=2&limit=10",
        )
        assert r.status_code == 200

        payload = r.json()
        assert BalanceTransactionsResponseSchema.model_validate(payload)

        assert payload["pagination"]["page"] == 2
        assert payload["pagination"]["limit"] == 10
        assert payload["pagination"]["total"] == 15
        assert payload["pagination"]["totalPages"] == 2
        assert len(payload["transactions"]) == 5

    def test_get_transactions_month_sort_by_amount_asc(self, authorized_client):
        """Sorting by amount asc."""
        authorized_client.balance_repo.reset()

        authorized_client.balance_repo.transactions = [
            Transaction(
                amount=100,
                reference="MID",
                date=datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc),
                type="debit",
                description="",
                payment_method="cash",
                status="CONFIRMED",
                category="Otro",
            ),
            Transaction(
                amount=150,
                reference="HIGH",
                date=datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc),
                type="debit",
                description="",
                payment_method="cash",
                status="CONFIRMED",
                category="Otro",
            ),
            Transaction(
                amount=50,
                reference="LOW",
                date=datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc),
                type="debit",
                description="",
                payment_method="cash",
                status="CONFIRMED",
                category="Otro",
            ),
        ]

        r = authorized_client.get(
            "/pegazzo/management/balance/transactions?period=month&month=1&year=2026&sort_by=amount&sort_order=asc",
        )
        assert r.status_code == 200

        payload = r.json()
        assert BalanceTransactionsResponseSchema.model_validate(payload)

        refs = [t["reference"] for t in payload["transactions"]]
        assert refs == ["LOW", "MID", "HIGH"]

    def test_get_transactions_month_sort_by_reference_desc(self, authorized_client):
        """Sorting by reference desc."""
        authorized_client.balance_repo.reset()

        authorized_client.balance_repo.transactions = [
            Transaction(
                amount=10,
                reference="A-100",
                date=datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc),
                type="debit",
                description="",
                payment_method="cash",
                status="CONFIRMED",
                category="Otro",
            ),
            Transaction(
                amount=10,
                reference="Z-100",
                date=datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc),
                type="debit",
                description="",
                payment_method="cash",
                status="CONFIRMED",
                category="Otro",
            ),
            Transaction(
                amount=10,
                reference="B-100",
                date=datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc),
                type="debit",
                description="",
                payment_method="cash",
                status="CONFIRMED",
                category="Otro",
            ),
        ]

        r = authorized_client.get(
            "/pegazzo/management/balance/transactions?period=month&month=1&year=2026&sort_by=reference&sort_order=desc",
        )
        assert r.status_code == 200

        payload = r.json()
        assert BalanceTransactionsResponseSchema.model_validate(payload)

        refs = [t["reference"] for t in payload["transactions"]]
        assert refs == ["Z-100", "B-100", "A-100"]

    def test_get_transactions_empty_result_returns_zero_pages(self, authorized_client):
        """No matching transactions -> [], total=0, totalPages=0."""
        authorized_client.balance_repo.reset()
        authorized_client.balance_repo.transactions = []

        r = authorized_client.get("/pegazzo/management/balance/transactions?period=year&year=2099")
        assert r.status_code == 200

        payload = r.json()
        assert BalanceTransactionsResponseSchema.model_validate(payload)

        assert payload["transactions"] == []
        assert payload["pagination"]["total"] == 0
        assert payload["pagination"]["totalPages"] == 0

    def test_get_transactions_week_missing_params_400(self, authorized_client):
        """Week requires week + month + year."""
        r = authorized_client.get("/pegazzo/management/balance/transactions?period=week&year=2026")
        assert r.status_code == 400
        assert "Invalid metrics period" in r.json()["detail"]

    def test_get_transactions_month_missing_params_400(self, authorized_client):
        """Month requires month + year."""
        r = authorized_client.get("/pegazzo/management/balance/transactions?period=month&month=1")
        assert r.status_code == 400
        assert "Invalid metrics period" in r.json()["detail"]

    def test_get_transactions_year_missing_params_400(self, authorized_client):
        """Year requires year."""
        r = authorized_client.get("/pegazzo/management/balance/transactions?period=year")
        assert r.status_code == 400
        assert "Invalid metrics period" in r.json()["detail"]

    def test_get_transactions_invalid_period_422(self, authorized_client):
        r = authorized_client.get("/pegazzo/management/balance/transactions?period=INVALID&year=2026")
        assert r.status_code == 422
        detail = r.json()["detail"]
        assert isinstance(detail, list)
        assert detail[0]["loc"] == ["query", "period"]

    def test_get_transactions_invalid_limit_422(self, authorized_client):
        r = authorized_client.get("/pegazzo/management/balance/transactions?period=year&year=2026&limit=101")
        assert r.status_code == 422

    def test_get_transactions_invalid_page_422(self, authorized_client):
        r = authorized_client.get("/pegazzo/management/balance/transactions?period=year&year=2026&page=0")
        assert r.status_code == 422

    def test_get_transactions_invalid_sort_by_422(self, authorized_client):
        r = authorized_client.get(
            "/pegazzo/management/balance/transactions?period=year&year=2026&sort_by=BAD",
        )
        assert r.status_code == 422

    def test_get_transactions_invalid_sort_order_422(self, authorized_client):
        r = authorized_client.get(
            "/pegazzo/management/balance/transactions?period=year&year=2026&sort_order=BAD",
        )
        assert r.status_code == 422

    def test_get_transactions_unauthorized(self, client):
        r = client.get("/pegazzo/management/balance/transactions?period=year&year=2026")
        assert r.status_code == 401

    def test_get_transactions_with_status_filter(self, authorized_client):
        """Transactions list accepts optional status filter."""
        r = authorized_client.get(
            "/pegazzo/management/balance/transactions?period=year&year=2026&status=CONFIRMED",
        )
        assert r.status_code == 200
        data = r.json()
        assert "transactions" in data

    def test_get_transactions_invalid_status_422(self, authorized_client):
        """Invalid status value returns 422."""
        r = authorized_client.get(
            "/pegazzo/management/balance/transactions?period=year&year=2026&status=INVALID",
        )
        assert r.status_code == 422

    # Authorization endpoint tests

    def test_authorize_transaction_owner_confirms(self, authorized_client):
        """Owner can confirm a PENDING transaction."""
        reference = "MOCK_REF_001"
        authorized_client.balance_repo.transactions[0].status = "PENDING"

        r = authorized_client.post(
            f"/pegazzo/management/balance/transaction/{reference}/authorization",
            json={"status": "CONFIRMED"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "CONFIRMED"

    def test_authorize_transaction_owner_rejects(self, authorized_client):
        """Owner can reject a PENDING transaction."""
        reference = "MOCK_REF_001"
        authorized_client.balance_repo.transactions[0].status = "PENDING"

        r = authorized_client.post(
            f"/pegazzo/management/balance/transaction/{reference}/authorization",
            json={"status": "REJECTED"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "REJECTED"

    def test_authorize_transaction_not_found(self, authorized_client):
        """Returns 404 when reference does not exist."""
        r = authorized_client.post(
            "/pegazzo/management/balance/transaction/NOEXIST/authorization",
            json={"status": "CONFIRMED"},
        )
        assert r.status_code == 404

    def test_authorize_transaction_invalid_status_422(self, authorized_client):
        """Returns 422 for invalid status value."""
        r = authorized_client.post(
            "/pegazzo/management/balance/transaction/MOCK_REF_001/authorization",
            json={"status": "INVALID"},
        )
        assert r.status_code == 422

    def test_authorize_transaction_unauthorized(self, client):
        """Unauthenticated request returns 401."""
        r = client.post(
            "/pegazzo/management/balance/transaction/MOCK_REF_001/authorization",
            json={"status": "CONFIRMED"},
        )
        assert r.status_code == 401

    def test_authorize_transaction_admin_resubmits_rejected(self, admin_authorized_client):
        """Admin can resubmit a REJECTED transaction to PENDING."""
        reference = "MOCK_REF_001"
        admin_authorized_client.balance_repo.transactions[0].status = "REJECTED"

        r = admin_authorized_client.post(
            f"/pegazzo/management/balance/transaction/{reference}/authorization",
            json={"status": "PENDING"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "PENDING"

    def test_authorize_transaction_admin_cannot_confirm_403(self, admin_authorized_client):
        """Admin cannot confirm a transaction."""
        reference = "MOCK_REF_001"
        admin_authorized_client.balance_repo.transactions[0].status = "PENDING"

        r = admin_authorized_client.post(
            f"/pegazzo/management/balance/transaction/{reference}/authorization",
            json={"status": "CONFIRMED"},
        )
        assert r.status_code == 403

    def test_authorize_transaction_admin_pending_on_pending_422(self, admin_authorized_client):
        """Admin cannot resubmit a PENDING transaction (not REJECTED)."""
        reference = "MOCK_REF_001"
        admin_authorized_client.balance_repo.transactions[0].status = "PENDING"

        r = admin_authorized_client.post(
            f"/pegazzo/management/balance/transaction/{reference}/authorization",
            json={"status": "PENDING"},
        )
        assert r.status_code == 422

    # Admin delete/edit permission tests

    def test_delete_transaction_admin_rejected_success(self, admin_authorized_client):
        """Admin can delete a REJECTED transaction."""
        reference = "MOCK_REF_001"
        admin_authorized_client.balance_repo.transactions[0].status = "REJECTED"

        r = admin_authorized_client.delete(f"/pegazzo/management/balance/transaction/{reference}")
        assert r.status_code == 200

    def test_delete_transaction_admin_confirmed_403(self, admin_authorized_client):
        """Admin cannot delete a CONFIRMED transaction."""
        reference = "MOCK_REF_001"
        admin_authorized_client.balance_repo.transactions[0].status = "CONFIRMED"

        r = admin_authorized_client.delete(f"/pegazzo/management/balance/transaction/{reference}")
        assert r.status_code == 403

    def test_update_transaction_admin_rejected_success(self, admin_authorized_client):
        """Admin can edit a REJECTED transaction."""
        reference = "MOCK_REF_001"
        admin_authorized_client.balance_repo.transactions[0].status = "REJECTED"

        r = admin_authorized_client.patch(
            f"/pegazzo/management/balance/transaction/{reference}",
            json={"amount": 999},
        )
        assert r.status_code == 200
        assert r.json()["amount"] == 999

    def test_update_transaction_admin_confirmed_403(self, admin_authorized_client):
        """Admin cannot edit a CONFIRMED transaction."""
        reference = "MOCK_REF_001"
        admin_authorized_client.balance_repo.transactions[0].status = "CONFIRMED"

        r = admin_authorized_client.patch(
            f"/pegazzo/management/balance/transaction/{reference}",
            json={"amount": 999},
        )
        assert r.status_code == 403

    # category field tests

    def test_create_transaction_with_category_success(self, authorized_client):
        """POST /transaction includes category in response."""
        r = authorized_client.post(
            "/pegazzo/management/balance/transaction",
            json={
                "amount": 800,
                "type": "credit",
                "description": "Ingreso cliente",
                "payment_method": "cash",
                "category": "Ventas",
            },
        )
        assert r.status_code == 201
        assert r.json()["category"] == "Ventas"

    def test_create_transaction_empty_category_422(self, authorized_client):
        """POST /transaction with empty category string returns 422."""
        r = authorized_client.post(
            "/pegazzo/management/balance/transaction",
            json={
                "amount": 800,
                "type": "credit",
                "description": "Ingreso cliente",
                "payment_method": "cash",
                "category": "",
            },
        )
        assert r.status_code == 422

    def test_create_transaction_category_too_long_422(self, authorized_client):
        """POST /transaction with category > 100 chars returns 422."""
        r = authorized_client.post(
            "/pegazzo/management/balance/transaction",
            json={
                "amount": 800,
                "type": "credit",
                "description": "Ingreso cliente",
                "payment_method": "cash",
                "category": "x" * 101,
            },
        )
        assert r.status_code == 422

    def test_update_transaction_category_optional(self, authorized_client):
        """PATCH /transaction without category succeeds (category is optional on edit)."""
        r = authorized_client.patch(
            "/pegazzo/management/balance/transaction/MOCK_REF_001",
            json={"amount": 500},
        )
        assert r.status_code == 200

    def test_update_transaction_category_updated(self, authorized_client):
        """PATCH /transaction with category updates it in the response."""
        authorized_client.balance_repo.transactions[0].category = "Otro"

        r = authorized_client.patch(
            "/pegazzo/management/balance/transaction/MOCK_REF_001",
            json={"category": "Combustible"},
        )
        assert r.status_code == 200
        assert r.json()["category"] == "Combustible"

    def test_update_transaction_empty_category_422(self, authorized_client):
        """PATCH /transaction with empty category returns 422."""
        r = authorized_client.patch(
            "/pegazzo/management/balance/transaction/MOCK_REF_001",
            json={"category": ""},
        )
        assert r.status_code == 422

    def test_update_transaction_category_too_long_422(self, authorized_client):
        """PATCH /transaction with category > 100 chars returns 422."""
        r = authorized_client.patch(
            "/pegazzo/management/balance/transaction/MOCK_REF_001",
            json={"category": "x" * 101},
        )
        assert r.status_code == 422

    def test_get_transaction_response_has_category(self, authorized_client):
        """GET /transaction/{reference} response includes category field."""
        r = authorized_client.get("/pegazzo/management/balance/transaction/MOCK_REF_001")
        assert r.status_code == 200
        assert "category" in r.json()

    def test_list_transactions_response_has_category(self, authorized_client):
        """GET /transactions includes category in each transaction."""
        r = authorized_client.get(
            "/pegazzo/management/balance/transactions?period=year&year=2026",
        )
        assert r.status_code == 200
        for tx in r.json()["transactions"]:
            assert "category" in tx

    # car_id field tests

    def test_create_transaction_response_has_car_id_null(self, authorized_client):
        """POST /transaction response includes car_id as null."""
        r = authorized_client.post(
            "/pegazzo/management/balance/transaction",
            json={
                "amount": 500,
                "type": "debit",
                "description": "Test car_id",
                "payment_method": "cash",
            },
        )
        assert r.status_code == 201
        assert r.json()["carId"] is None

    def test_get_transaction_response_has_car_id_null(self, authorized_client):
        """GET /transaction/{reference} response includes car_id as null."""
        r = authorized_client.get("/pegazzo/management/balance/transaction/MOCK_REF_001")
        assert r.status_code == 200
        assert r.json()["carId"] is None

    def test_update_transaction_response_has_car_id_null(self, authorized_client):
        """PATCH /transaction/{reference} response includes car_id as null."""
        r = authorized_client.patch(
            "/pegazzo/management/balance/transaction/MOCK_REF_001",
            json={"amount": 750},
        )
        assert r.status_code == 200
        assert r.json()["carId"] is None

    def test_list_transactions_response_has_car_id_null(self, authorized_client):
        """GET /transactions response includes car_id as null in each transaction."""
        r = authorized_client.get(
            "/pegazzo/management/balance/transactions?period=year&year=2026",
        )
        assert r.status_code == 200
        payload = r.json()
        for tx in payload["transactions"]:
            assert tx["carId"] is None

    # GET /transactions/count tests

    def test_get_transactions_count_no_params_returns_current_month(self, authorized_client):
        """No params → 200 with count for current month."""
        r = authorized_client.get("/pegazzo/management/balance/transactions/count")
        assert r.status_code == 200
        payload = r.json()
        assert "count" in payload
        assert "period" in payload
        assert isinstance(payload["count"], int)
        assert payload["count"] >= 0

    def test_get_transactions_count_with_month_year(self, authorized_client):
        """Explicit month + year → 200 with correct period in response."""
        r = authorized_client.get("/pegazzo/management/balance/transactions/count?month=1&year=2026")
        assert r.status_code == 200
        payload = r.json()
        assert payload["period"]["month"] == 1
        assert payload["period"]["year"] == 2026

    def test_get_transactions_count_with_status_pending(self, authorized_client):
        """status=PENDING filter is accepted and returns 200."""
        r = authorized_client.get("/pegazzo/management/balance/transactions/count?status=PENDING")
        assert r.status_code == 200
        assert "count" in r.json()

    def test_get_transactions_count_with_status_rejected(self, authorized_client):
        """status=REJECTED filter is accepted and returns 200."""
        r = authorized_client.get("/pegazzo/management/balance/transactions/count?status=REJECTED")
        assert r.status_code == 200
        assert "count" in r.json()

    def test_get_transactions_count_with_status_confirmed(self, authorized_client):
        """status=CONFIRMED filter is accepted and returns 200."""
        r = authorized_client.get("/pegazzo/management/balance/transactions/count?status=CONFIRMED")
        assert r.status_code == 200
        assert "count" in r.json()

    def test_get_transactions_count_only_month_400(self, authorized_client):
        """Providing only month (no year) returns 400."""
        r = authorized_client.get("/pegazzo/management/balance/transactions/count?month=4")
        assert r.status_code == 400
        assert "Invalid metrics period" in r.json()["detail"]

    def test_get_transactions_count_only_year_400(self, authorized_client):
        """Providing only year (no month) returns 400."""
        r = authorized_client.get("/pegazzo/management/balance/transactions/count?year=2026")
        assert r.status_code == 400
        assert "Invalid metrics period" in r.json()["detail"]

    def test_get_transactions_count_invalid_month_422(self, authorized_client):
        """month out of range (0 or 13) returns 422."""
        r = authorized_client.get("/pegazzo/management/balance/transactions/count?month=13&year=2026")
        assert r.status_code == 422

    def test_get_transactions_count_invalid_status_422(self, authorized_client):
        """Invalid status value returns 422."""
        r = authorized_client.get("/pegazzo/management/balance/transactions/count?status=INVALID")
        assert r.status_code == 422

    def test_get_transactions_count_unauthorized(self, client):
        """Unauthenticated request returns 401."""
        r = client.get("/pegazzo/management/balance/transactions/count")
        assert r.status_code == 401

    def test_get_transactions_count_reflects_mock_data(self, authorized_client):
        """Count matches the number of mock transactions in the current month."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        authorized_client.balance_repo.reset()
        authorized_client.balance_repo.transactions = [
            __import__("app.models.balance", fromlist=["Transaction"]).Transaction(
                amount=100,
                reference="CNT-001",
                date=datetime(now.year, now.month, 5, 10, 0, tzinfo=timezone.utc),
                type="debit",
                description="Test",
                payment_method="cash",
                status="PENDING",
                category="Otro",
            ),
            __import__("app.models.balance", fromlist=["Transaction"]).Transaction(
                amount=200,
                reference="CNT-002",
                date=datetime(now.year, now.month, 10, 10, 0, tzinfo=timezone.utc),
                type="debit",
                description="Test 2",
                payment_method="cash",
                status="REJECTED",
                category="Otro",
            ),
        ]

        r = authorized_client.get("/pegazzo/management/balance/transactions/count")
        assert r.status_code == 200
        assert r.json()["count"] == 2
