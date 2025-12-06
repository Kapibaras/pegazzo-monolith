import pytest

from app.schemas.balance import TransactionResponseSchema


@pytest.mark.usefixtures("authorized_client", "client")
class TestBalanceRouter:
    """Tests for Balance Router endpoints."""

    def test_get_transaction(self, authorized_client):
        """Test getting a transaction successfully."""
        reference = "1739411013"
        response = authorized_client.get(f"/pegazzo/management/balance/transaction/{reference}")

        assert response.status_code == 200
        data = response.json()
        assert TransactionResponseSchema.model_validate(data)

    def test_get_transaction_fail_without_auth(self, client):
        """Test that get transaction fails without authorization."""
        reference = "1739411013"
        response = client.get(f"/pegazzo/management/balance/transaction/{reference}")

        assert response.status_code == 401

    def test_get_transaction_fail_invalid_reference(self, authorized_client):
        """Test that get transaction fails with invalid reference."""

        reference = "invalid_reference"
        response = authorized_client.get(f"/pegazzo/management/balance/transaction/{reference}")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Transaction not found"

    def test_create_transaction(self, authorized_client):
        """Test creating a transaction successfully."""

        transaction_data = {
            "amount": 1500,
            "date": "2025-01-01T10:30:00",
            "type": "debit",
            "description": "Pago de material",
            "payment_method": "cash",
        }

        response = authorized_client.post(
            "/pegazzo/management/balance/transaction",
            json=transaction_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert TransactionResponseSchema.model_validate(data)

    @pytest.mark.parametrize(
        ("method", "endpoint"),
        [
            ("post", "/pegazzo/management/balance/transaction"),
        ],
    )
    def test_balance_routes_fail_without_auth(self, method, endpoint, client):
        """Test that balance routes fail without authorization."""

        json_data = (
            {
                "amount": 1500,
                "reference": "XYZ987654",
                "date": "2025-01-01T08:00:00",
                "type": "debit",
                "description": "Sin auth",
                "paymentMethod": "cash",
            }
            if method == "post"
            else None
        )

        request_func = getattr(client, method)

        response = request_func(endpoint, json=json_data) if json_data else request_func(endpoint)

        assert response.status_code == 401

    def test_create_transaction_invalid_body(self, authorized_client):
        """Test validation errors when sending bad input."""

        invalid_data = {
            "amount": "NOT_A_NUMBER",
            "reference": 1234,
        }

        response = authorized_client.post(
            "/pegazzo/management/balance/transaction",
            json=invalid_data,
        )

        assert response.status_code == 422
