"""Tests for PGZ-151: financing fields on car create/get endpoints."""

from datetime import UTC, datetime, timedelta

BASE_PAYLOAD = {
    "id": "CAR-FIN",
    "make": "Toyota",
    "model": "Corolla",
    "year": "2022",
    "color": "White",
    "status": "ACTIVE",
    "vin": "1HGBH41JXMN109186",
    "plate": "ABC-1234",
    "bodyType": "Sedan",
    "engineType": "Gasoline",
    "transmission": "Automatic",
    "engineSerialNumber": "ENG123456",
    "odometer": 0,
    "doorsNumber": 4,
    "passengersNumber": 5,
    "tireSpecification": "195/65R15",
    "unitValue": 250000.00,
    "unitBillingValue": 240000.00,
    "billNumber": "BILL-001",
    "publicVehicleRegistry": "REG-001",
    "altaPublicVehicleRegistry": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
    "batteryModel": "BattX",
    "batterySerialNumber": "BATT123",
    "batteryDate": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
    "legalOwnerName": "Juan",
    "legalOwnerSurnames": "García López",
    "insuranceProviderId": 1,
    "policyNumber": "POL-001",
    "policyExpirationDate": (datetime.now(UTC) + timedelta(days=365)).isoformat(),
    "policyType": "FULL",
}

_FINANCING_FIELDS = {
    "financingAgency": "BBVA",
    "financingPurchaseDate": "2024-01-15",
    "financingTermMonths": 48,
    "financingRemainingAmount": 150000.00,
}


class TestCarFinancingFields:
    """Tests for financing fields on POST /management/cars."""

    def test_create_liquidated_car_success(self, authorized_client):
        """A liquidated car requires only isFinancedLiquidated=true, no financing details."""
        payload = {**BASE_PAYLOAD, "isFinancedLiquidated": True}
        response = authorized_client.post("/pegazzo/management/cars", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["isFinancedLiquidated"] is True
        assert data["financingAgency"] is None
        assert data["financingPurchaseDate"] is None
        assert data["financingTermMonths"] is None
        assert data["financingRemainingAmount"] is None

    def test_create_financed_car_success(self, authorized_client):
        """A non-liquidated car requires all financing detail fields."""
        payload = {**BASE_PAYLOAD, "isFinancedLiquidated": False, **_FINANCING_FIELDS}
        response = authorized_client.post("/pegazzo/management/cars", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["isFinancedLiquidated"] is False
        assert data["financingAgency"] == "BBVA"
        assert data["financingTermMonths"] == 48

    def test_create_financed_car_missing_agency_returns_422(self, authorized_client):
        """Omitting financingAgency when not liquidated returns 422."""
        fields = {k: v for k, v in _FINANCING_FIELDS.items() if k != "financingAgency"}
        payload = {**BASE_PAYLOAD, "isFinancedLiquidated": False, **fields}
        response = authorized_client.post("/pegazzo/management/cars", json=payload)
        assert response.status_code == 422

    def test_create_financed_car_missing_purchase_date_returns_422(self, authorized_client):
        """Omitting financingPurchaseDate when not liquidated returns 422."""
        fields = {k: v for k, v in _FINANCING_FIELDS.items() if k != "financingPurchaseDate"}
        payload = {**BASE_PAYLOAD, "isFinancedLiquidated": False, **fields}
        response = authorized_client.post("/pegazzo/management/cars", json=payload)
        assert response.status_code == 422

    def test_create_financed_car_missing_term_months_returns_422(self, authorized_client):
        """Omitting financingTermMonths when not liquidated returns 422."""
        fields = {k: v for k, v in _FINANCING_FIELDS.items() if k != "financingTermMonths"}
        payload = {**BASE_PAYLOAD, "isFinancedLiquidated": False, **fields}
        response = authorized_client.post("/pegazzo/management/cars", json=payload)
        assert response.status_code == 422

    def test_create_financed_car_missing_remaining_amount_returns_422(self, authorized_client):
        """Omitting financingRemainingAmount when not liquidated returns 422."""
        fields = {k: v for k, v in _FINANCING_FIELDS.items() if k != "financingRemainingAmount"}
        payload = {**BASE_PAYLOAD, "isFinancedLiquidated": False, **fields}
        response = authorized_client.post("/pegazzo/management/cars", json=payload)
        assert response.status_code == 422

    def test_create_financed_car_missing_all_details_returns_422(self, authorized_client):
        """Omitting all financing details when not liquidated returns 422."""
        payload = {**BASE_PAYLOAD, "isFinancedLiquidated": False}
        response = authorized_client.post("/pegazzo/management/cars", json=payload)
        assert response.status_code == 422

    def test_create_missing_is_financed_liquidated_returns_422(self, authorized_client):
        """Omitting isFinancedLiquidated entirely returns 422."""
        response = authorized_client.post("/pegazzo/management/cars", json=BASE_PAYLOAD)
        assert response.status_code == 422
