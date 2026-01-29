from datetime import datetime, timezone
from decimal import Decimal

from app.models.transaction_metrics import TransactionMetrics
from app.schemas.balance import (
    BalanceMetricsDetailedResponseSchema,
    BalanceMetricsSimpleResponseSchema,
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
                "date": "2025-01-01T10:30:00",
                "type": "debit",
                "description": "Pago de material",
                "payment_method": "cash",
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

    def test_get_management_metrics_week_success(self, authorized_client, balance_repo):
        balance_repo.mapping[("week", 2026, 1, 5)] = TransactionMetrics(
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

    def test_get_management_metrics_month_success(self, authorized_client, balance_repo):
        balance_repo.mapping[("month", 2026, 1, None)] = TransactionMetrics(
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

    def test_get_management_metrics_year_success(self, authorized_client, balance_repo):
        balance_repo.mapping[("year", 2026, None, None)] = TransactionMetrics(
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
