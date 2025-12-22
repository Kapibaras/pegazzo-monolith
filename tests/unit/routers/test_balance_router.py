from app.schemas.balance import TransactionResponseSchema
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
