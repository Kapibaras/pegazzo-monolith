from datetime import datetime, timedelta, timezone


def _future_date(days: int = 365) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _past_date(days: int = 1) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


BASE_PAYLOAD = {
    "id": "CAR-001",
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
    "altaPublicVehicleRegistry": _future_date(30),
    "batteryModel": "BattX",
    "batterySerialNumber": "BATT123",
    "batteryDate": _future_date(30),
    "legalOwnerName": "Juan",
    "legalOwnerSurnames": "García López",
    "financedStatus": "PAID",
    "insuranceProviderId": 1,
    "policyNumber": "POL-001",
    "policyExpirationDate": _future_date(365),
    "policyType": "FULL",
}


class TestCarRouter:
    """Tests for the car management endpoints."""

    # -------------------------------------------------------------------------
    # POST /management/cars
    # -------------------------------------------------------------------------

    def test_create_car_success(self, authorized_client):
        response = authorized_client.post("/pegazzo/management/cars", json=BASE_PAYLOAD)

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "CAR-001"
        assert data["make"] == "Toyota"
        assert data["vin"] == "1HGBH41JXMN109186"
        assert data["plate"] == "ABC-1234"
        assert data["status"] == "ACTIVE"

    def test_create_car_with_associate(self, authorized_client):
        payload = {**BASE_PAYLOAD, "associateId": 1}
        response = authorized_client.post("/pegazzo/management/cars", json=payload)
        assert response.status_code == 201

    def test_create_car_duplicate_id(self, authorized_client):
        authorized_client.post("/pegazzo/management/cars", json=BASE_PAYLOAD)

        response = authorized_client.post("/pegazzo/management/cars", json=BASE_PAYLOAD)
        assert response.status_code == 400
        assert "CAR-001" in response.json()["detail"]

    def test_create_car_duplicate_vin(self, authorized_client):
        authorized_client.post("/pegazzo/management/cars", json=BASE_PAYLOAD)

        payload = {**BASE_PAYLOAD, "id": "CAR-002", "plate": "XYZ-9999"}
        response = authorized_client.post("/pegazzo/management/cars", json=payload)
        assert response.status_code == 400
        assert "1HGBH41JXMN109186" in response.json()["detail"]

    def test_create_car_duplicate_plate(self, authorized_client):
        authorized_client.post("/pegazzo/management/cars", json=BASE_PAYLOAD)

        payload = {**BASE_PAYLOAD, "id": "CAR-002", "vin": "2HGBH41JXMN999999"}
        response = authorized_client.post("/pegazzo/management/cars", json=payload)
        assert response.status_code == 400
        assert "ABC-1234" in response.json()["detail"]

    def test_create_car_policy_expiration_in_past(self, authorized_client):
        payload = {**BASE_PAYLOAD, "policyExpirationDate": _past_date()}
        response = authorized_client.post("/pegazzo/management/cars", json=payload)
        assert response.status_code == 400
        assert "past" in response.json()["detail"].lower()

    def test_create_car_nonexistent_insurance_provider(self, authorized_client):
        payload = {**BASE_PAYLOAD, "insuranceProviderId": 9999}
        response = authorized_client.post("/pegazzo/management/cars", json=payload)
        assert response.status_code == 400
        assert "9999" in response.json()["detail"]

    def test_create_car_nonexistent_associate(self, authorized_client):
        payload = {**BASE_PAYLOAD, "associateId": 9999}
        response = authorized_client.post("/pegazzo/management/cars", json=payload)
        assert response.status_code == 400
        assert "9999" in response.json()["detail"]

    def test_create_car_unauthenticated(self, client):
        response = client.post("/pegazzo/management/cars", json=BASE_PAYLOAD)
        assert response.status_code == 401

    def test_create_car_employee_forbidden(self, authorized_client):
        """Employee role should not be allowed to create cars."""
        pass

    def test_create_car_missing_required_field(self, authorized_client):
        payload = {k: v for k, v in BASE_PAYLOAD.items() if k != "vin"}
        response = authorized_client.post("/pegazzo/management/cars", json=payload)
        assert response.status_code == 422

    # -------------------------------------------------------------------------
    # GET /management/cars
    # -------------------------------------------------------------------------

    def test_list_cars_empty(self, authorized_client):
        response = authorized_client.get("/pegazzo/management/cars")
        assert response.status_code == 200
        data = response.json()
        assert data["cars"] == []
        assert data["pagination"]["total"] == 0
        assert data["pagination"]["totalPages"] == 0

    def test_list_cars_returns_summary_fields(self, authorized_client):
        authorized_client.post("/pegazzo/management/cars", json=BASE_PAYLOAD)

        response = authorized_client.get("/pegazzo/management/cars")
        assert response.status_code == 200
        cars = response.json()["cars"]
        assert len(cars) == 1
        car = cars[0]
        assert car["id"] == "CAR-001"
        assert car["make"] == "Toyota"
        assert car["model"] == "Corolla"
        assert car["plate"] == "ABC-1234"
        assert car["status"] == "ACTIVE"
        assert car["year"] == "2022"
        assert car["color"] == "White"
        assert "agencyImage" in car

    def test_list_cars_pagination(self, authorized_client):
        for i in range(3):
            payload = {
                **BASE_PAYLOAD,
                "id": f"CAR-00{i + 1}",
                "vin": f"VIN0000000000000{i}",
                "plate": f"PLATE-00{i}",
            }
            authorized_client.post("/pegazzo/management/cars", json=payload)

        response = authorized_client.get("/pegazzo/management/cars?page=1&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["cars"]) == 2
        assert data["pagination"]["total"] == 3
        assert data["pagination"]["totalPages"] == 2

        response2 = authorized_client.get("/pegazzo/management/cars?page=2&limit=2")
        assert len(response2.json()["cars"]) == 1

    def test_list_cars_filter_by_status(self, authorized_client):
        authorized_client.post("/pegazzo/management/cars", json=BASE_PAYLOAD)
        payload2 = {**BASE_PAYLOAD, "id": "CAR-002", "vin": "VIN00000000000002", "plate": "PLT-002", "status": "INACTIVE"}
        authorized_client.post("/pegazzo/management/cars", json=payload2)

        response = authorized_client.get("/pegazzo/management/cars?status=ACTIVE")
        assert response.status_code == 200
        cars = response.json()["cars"]
        assert all(c["status"] == "ACTIVE" for c in cars)

        response2 = authorized_client.get("/pegazzo/management/cars?status=INACTIVE")
        cars2 = response2.json()["cars"]
        assert all(c["status"] == "INACTIVE" for c in cars2)

    def test_list_cars_search_by_plate(self, authorized_client):
        authorized_client.post("/pegazzo/management/cars", json=BASE_PAYLOAD)

        response = authorized_client.get("/pegazzo/management/cars?search=ABC")
        assert response.status_code == 200
        assert len(response.json()["cars"]) == 1

    def test_list_cars_search_by_make(self, authorized_client):
        authorized_client.post("/pegazzo/management/cars", json=BASE_PAYLOAD)

        response = authorized_client.get("/pegazzo/management/cars?search=toyota")
        assert response.status_code == 200
        assert len(response.json()["cars"]) == 1

    def test_list_cars_search_no_match(self, authorized_client):
        authorized_client.post("/pegazzo/management/cars", json=BASE_PAYLOAD)

        response = authorized_client.get("/pegazzo/management/cars?search=NOMATCH")
        assert response.status_code == 200
        assert response.json()["cars"] == []

    def test_list_cars_archived_false_by_default(self, authorized_client):
        """Active cars are returned by default; archived cars are hidden."""
        authorized_client.post("/pegazzo/management/cars", json=BASE_PAYLOAD)
        car = authorized_client.car_repo.get_by_id("CAR-001")
        car.archived_at = datetime.now(timezone.utc)

        response = authorized_client.get("/pegazzo/management/cars")
        assert response.json()["cars"] == []

    def test_list_cars_archived_true(self, authorized_client):
        """Archived cars are returned when archived=true."""
        authorized_client.post("/pegazzo/management/cars", json=BASE_PAYLOAD)
        car = authorized_client.car_repo.get_by_id("CAR-001")
        car.archived_at = datetime.now(timezone.utc)

        response = authorized_client.get("/pegazzo/management/cars?archived=true")
        assert len(response.json()["cars"]) == 1

    def test_list_cars_sort_asc(self, authorized_client):
        for make in ["Toyota", "BMW", "Audi"]:
            payload = {
                **BASE_PAYLOAD,
                "id": f"CAR-{make}",
                "vin": f"VIN{make}".ljust(17, "0")[:17],
                "plate": f"PLT-{make}",
                "make": make,
            }
            authorized_client.post("/pegazzo/management/cars", json=payload)

        response = authorized_client.get("/pegazzo/management/cars?sort_by=make&sort_order=asc")
        assert response.status_code == 200
        makes = [c["make"] for c in response.json()["cars"]]
        assert makes == sorted(makes)

    def test_list_cars_unauthenticated(self, client):
        response = client.get("/pegazzo/management/cars")
        assert response.status_code == 401
