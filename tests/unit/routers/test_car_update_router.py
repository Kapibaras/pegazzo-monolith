"""Tests for PGZ-129: partial update of a car and the dedicated status endpoint."""

from datetime import UTC, datetime, timedelta

import pytest

from app.models.car import Associate, Insurance
from tests.unit.routers.test_car_router import BASE_PAYLOAD

ENDPOINT = "/pegazzo/management/cars"


@pytest.fixture
def created_car(authorized_client):
    """Create CAR-001 through the API and return its id."""
    response = authorized_client.post(ENDPOINT, json=BASE_PAYLOAD)
    assert response.status_code == 201
    return response.json()["id"]


def _future(days: int = 365) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


class TestUpdateCar:
    """PATCH /management/cars/{car_id}."""

    def test_update_several_fields(self, authorized_client, created_car):
        response = authorized_client.patch(
            f"{ENDPOINT}/{created_car}",
            json={"color": "Black", "odometer": 1500, "policyType": "BASIC", "features": {"ac": True}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["color"] == "Black"
        assert data["odometer"] == 1500
        assert data["policyType"] == "BASIC"
        assert data["features"] == {"ac": True}
        # Untouched fields keep their value
        assert data["make"] == "Toyota"
        assert data["status"] == "ACTIVE"

    def test_update_does_not_change_status(self, authorized_client, created_car):
        response = authorized_client.patch(f"{ENDPOINT}/{created_car}", json={"color": "Blue", "status": "INACTIVE"})

        assert response.status_code == 200
        assert response.json()["status"] == "ACTIVE"

    def test_update_same_vin_and_plate_of_the_car_is_allowed(self, authorized_client, created_car):
        response = authorized_client.patch(
            f"{ENDPOINT}/{created_car}",
            json={"vin": BASE_PAYLOAD["vin"], "plate": BASE_PAYLOAD["plate"]},
        )

        assert response.status_code == 200

    def test_update_vin_already_used_by_another_car(self, authorized_client, created_car):
        other = {**BASE_PAYLOAD, "id": "CAR-002", "vin": "2HGBH41JXMN109187", "plate": "XYZ-9999"}
        assert authorized_client.post(ENDPOINT, json=other).status_code == 201

        response = authorized_client.patch(f"{ENDPOINT}/{created_car}", json={"vin": other["vin"]})

        assert response.status_code == 400
        assert "VIN" in response.json()["detail"]

    def test_update_plate_already_used_by_another_car(self, authorized_client, created_car):
        other = {**BASE_PAYLOAD, "id": "CAR-002", "vin": "2HGBH41JXMN109187", "plate": "XYZ-9999"}
        assert authorized_client.post(ENDPOINT, json=other).status_code == 201

        response = authorized_client.patch(f"{ENDPOINT}/{created_car}", json={"plate": other["plate"]})

        assert response.status_code == 400
        assert "plate" in response.json()["detail"]

    def test_update_policy_expiration_in_the_past(self, authorized_client, created_car):
        response = authorized_client.patch(
            f"{ENDPOINT}/{created_car}",
            json={"policyExpirationDate": _future(-1)},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Policy expiration date must not be in the past"

    def test_update_policy_expiration_in_the_future(self, authorized_client, created_car):
        response = authorized_client.patch(
            f"{ENDPOINT}/{created_car}",
            json={"policyExpirationDate": _future(400)},
        )

        assert response.status_code == 200

    def test_update_insurance_provider_must_exist(self, authorized_client, created_car):
        response = authorized_client.patch(f"{ENDPOINT}/{created_car}", json={"insuranceProviderId": 999})

        assert response.status_code == 400
        assert "Insurance provider" in response.json()["detail"]

    def test_update_insurance_provider_success(self, authorized_client, created_car):
        authorized_client.car_repo.insurances.append(Insurance(id=2, name="GNP", telephones=["+520000000000"]))

        response = authorized_client.patch(f"{ENDPOINT}/{created_car}", json={"insuranceProviderId": 2})

        assert response.status_code == 200
        assert response.json()["insuranceProviderId"] == 2

    def test_update_associate_must_exist(self, authorized_client, created_car):
        response = authorized_client.patch(f"{ENDPOINT}/{created_car}", json={"associateId": 999})

        assert response.status_code == 400
        assert "Associate" in response.json()["detail"]

    def test_update_associate_success(self, authorized_client, created_car):
        associate = Associate(id=2, name="Ana", surnames="Lopez", telephones=["+520000000001"])
        authorized_client.car_repo.associates.append(associate)

        response = authorized_client.patch(f"{ENDPOINT}/{created_car}", json={"associateId": 2})

        assert response.status_code == 200
        car = authorized_client.car_repo.get_by_id(created_car)
        assert [a.id for a in car.associate] == [2]

    def test_update_image_urls(self, authorized_client, created_car):
        response = authorized_client.patch(
            f"{ENDPOINT}/{created_car}",
            json={"agencyImage": "https://img.example/a.png", "photos": ["https://img.example/1.png"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["agencyImage"] == "https://img.example/a.png"
        assert data["photos"] == ["https://img.example/1.png"]

    def test_update_to_not_liquidated_requires_financing_data(self, authorized_client, created_car):
        response = authorized_client.patch(f"{ENDPOINT}/{created_car}", json={"isFinancedLiquidated": False})

        assert response.status_code == 400
        assert "financingAgency" not in response.json()["detail"]  # snake_case field names are reported
        assert "financing_agency" in response.json()["detail"]

    def test_update_to_not_liquidated_with_financing_data(self, authorized_client, created_car):
        response = authorized_client.patch(
            f"{ENDPOINT}/{created_car}",
            json={
                "isFinancedLiquidated": False,
                "financingAgency": "Bank",
                "financingPurchaseDate": "2024-01-10",
                "financingTermMonths": 24,
                "financingRemainingAmount": 100000,
            },
        )

        assert response.status_code == 200
        assert response.json()["financingAgency"] == "Bank"

    def test_update_empty_body_is_rejected(self, authorized_client, created_car):
        response = authorized_client.patch(f"{ENDPOINT}/{created_car}", json={})

        assert response.status_code == 422

    def test_update_invalid_value_is_rejected(self, authorized_client, created_car):
        response = authorized_client.patch(f"{ENDPOINT}/{created_car}", json={"odometer": -1})

        assert response.status_code == 422

    def test_update_naive_datetime_is_rejected(self, authorized_client, created_car):
        response = authorized_client.patch(
            f"{ENDPOINT}/{created_car}",
            json={"policyExpirationDate": "2099-01-01T00:00:00"},
        )

        assert response.status_code == 422

    def test_update_car_not_found(self, authorized_client):
        response = authorized_client.patch(f"{ENDPOINT}/NOPE", json={"color": "Blue"})

        assert response.status_code == 404

    def test_update_soft_deleted_car_is_not_found(self, authorized_client, created_car):
        authorized_client.car_repo.get_by_id(created_car).deleted_at = datetime.now(UTC)

        response = authorized_client.patch(f"{ENDPOINT}/{created_car}", json={"color": "Blue"})

        assert response.status_code == 404

    def test_update_requires_auth(self, client):
        response = client.patch(f"{ENDPOINT}/CAR-001", json={"color": "Blue"})

        assert response.status_code == 401

    def test_update_forbidden_for_employee(self, employee_authorized_client):
        response = employee_authorized_client.patch(f"{ENDPOINT}/CAR-001", json={"color": "Blue"})

        assert response.status_code == 403

    def test_update_allowed_for_admin(self, admin_authorized_client):
        admin_authorized_client.post(ENDPOINT, json=BASE_PAYLOAD)

        response = admin_authorized_client.patch(f"{ENDPOINT}/CAR-001", json={"color": "Blue"})

        assert response.status_code == 200


class TestUpdateCarStatus:
    """PATCH /management/cars/{car_id}/status."""

    @pytest.mark.parametrize("new_status", ["ACTIVE", "INACTIVE", "IN_MAINTENANCE"])
    def test_update_status_valid_values(self, authorized_client, created_car, new_status):
        response = authorized_client.patch(f"{ENDPOINT}/{created_car}/status", json={"status": new_status})

        assert response.status_code == 200
        assert response.json()["status"] == new_status

    def test_update_status_invalid_value(self, authorized_client, created_car):
        response = authorized_client.patch(f"{ENDPOINT}/{created_car}/status", json={"status": "BROKEN"})

        assert response.status_code == 422

    def test_update_status_missing_body(self, authorized_client, created_car):
        response = authorized_client.patch(f"{ENDPOINT}/{created_car}/status", json={})

        assert response.status_code == 422

    def test_update_status_car_not_found(self, authorized_client):
        response = authorized_client.patch(f"{ENDPOINT}/NOPE/status", json={"status": "INACTIVE"})

        assert response.status_code == 404

    def test_update_status_requires_auth(self, client):
        response = client.patch(f"{ENDPOINT}/CAR-001/status", json={"status": "INACTIVE"})

        assert response.status_code == 401

    def test_update_status_forbidden_for_employee(self, employee_authorized_client):
        response = employee_authorized_client.patch(f"{ENDPOINT}/CAR-001/status", json={"status": "INACTIVE"})

        assert response.status_code == 403
