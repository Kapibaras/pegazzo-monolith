from datetime import UTC, datetime, timedelta
from unittest.mock import patch


def _future_date(days: int = 365) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


def _past_date(days: int = 1) -> str:
    return (datetime.now(UTC) - timedelta(days=days)).isoformat()


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
        car.archived_at = datetime.now(UTC)

        response = authorized_client.get("/pegazzo/management/cars")
        assert response.json()["cars"] == []

    def test_list_cars_archived_true(self, authorized_client):
        """Archived cars are returned when archived=true."""
        authorized_client.post("/pegazzo/management/cars", json=BASE_PAYLOAD)
        car = authorized_client.car_repo.get_by_id("CAR-001")
        car.archived_at = datetime.now(UTC)

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

    # --- GET /{car_id} ---

    def _create_car(self, client):
        """Create CAR-001 in the mock and return the Car instance."""
        client.post("/pegazzo/management/cars", json=BASE_PAYLOAD)
        car = client.car_repo.get_by_id("CAR-001")
        car.insurance_provider = client.car_repo.insurances[0]
        car.associate = []
        return car

    def test_get_car_not_found(self, authorized_client):
        response = authorized_client.get("/pegazzo/management/cars/NOTEXIST")
        assert response.status_code == 404

    def test_get_car_unauthenticated(self, client):
        response = client.get("/pegazzo/management/cars/CAR-001")
        assert response.status_code == 401

    def test_get_car_basic_fields(self, authorized_client):
        with patch("app.services.car.r2.generate_document_read_url", return_value="https://r2.example/doc"):
            self._create_car(authorized_client)
            response = authorized_client.get("/pegazzo/management/cars/CAR-001")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "CAR-001"
        assert data["make"] == "Toyota"
        assert data["plate"] == "ABC-1234"
        assert data["documents"] == []
        assert data["assignedDriver"] is None
        assert data["associate"] is None
        assert data["insurance"]["name"] == "AXA"
        assert data["insurance"]["policyNumber"] == BASE_PAYLOAD["policyNumber"]

    def test_get_car_with_documents_expiry_status(self, authorized_client):
        """Documents with expiry_date get a computed expiry_status."""
        from app.models.document import Document

        self._create_car(authorized_client)
        now = datetime.now(UTC)
        doc_valid = Document(id=1, type="PDF", url="key/doc1.pdf", category="license",
                             expiry_date=now + timedelta(days=60))
        doc_expiring = Document(id=2, type="PDF", url="key/doc2.pdf", category="insurance",
                                expiry_date=now + timedelta(days=10))
        doc_expired = Document(id=3, type="PDF", url="key/doc3.pdf", category="registration",
                               expiry_date=now - timedelta(days=1))
        doc_no_expiry = Document(id=4, type="PDF", url="key/doc4.pdf", category="other",
                                 expiry_date=None)
        authorized_client.car_repo.car_documents["CAR-001"] = [
            doc_valid, doc_expiring, doc_expired, doc_no_expiry,
        ]

        with patch("app.services.car.r2.generate_document_read_url", return_value="https://r2.example/doc"):
            response = authorized_client.get("/pegazzo/management/cars/CAR-001")

        assert response.status_code == 200
        docs = {d["id"]: d for d in response.json()["documents"]}
        assert docs[1]["expiryStatus"] == "valid"
        assert docs[2]["expiryStatus"] == "expiring_soon"
        assert docs[3]["expiryStatus"] == "expired"
        assert docs[4]["expiryStatus"] is None
        assert all(d["url"] == "https://r2.example/doc" for d in docs.values())

    def test_get_car_with_assigned_driver(self, authorized_client):
        """Active contract links a driver to the car."""
        from app.models.contract import Contract
        from app.models.driver import Driver

        self._create_car(authorized_client)
        driver = Driver(id="DRV-001", name="Luis", surnames="Gomez Ramirez",
                        status="ACTIVE", telephones=["+521234567890"],
                        license_number="LIC001", license_validity=datetime.now(UTC),
                        identification_number="ID001", address="Calle 1",
                        garage_address=["Calle 2"])
        contract = Contract(
            id="CNT-001",
            car_id="CAR-001",
            driver_id="DRV-001",
            start_date=(datetime.now(tz=UTC) - timedelta(days=30)).date(),
            end_date=(datetime.now(tz=UTC) + timedelta(days=30)).date(),
            type="monthly",
            amount=5000,
            guarantee_amount=1000,
        )
        contract.driver = driver
        authorized_client.car_repo.contracts.append(contract)

        with patch("app.services.car.r2.generate_document_read_url", return_value="https://r2.example/doc"):
            response = authorized_client.get("/pegazzo/management/cars/CAR-001")

        assert response.status_code == 200
        driver_data = response.json()["assignedDriver"]
        assert driver_data["id"] == "DRV-001"
        assert driver_data["name"] == "Luis"
        assert driver_data["surnames"] == "Gomez Ramirez"

    def test_get_car_with_associate(self, authorized_client):
        """Car linked to an associate returns associate data."""
        self._create_car(authorized_client)
        car = authorized_client.car_repo.get_by_id("CAR-001")
        car.associate = [authorized_client.car_repo.associates[0]]

        with patch("app.services.car.r2.generate_document_read_url", return_value="https://r2.example/doc"):
            response = authorized_client.get("/pegazzo/management/cars/CAR-001")

        assert response.status_code == 200
        associate = response.json()["associate"]
        assert associate["name"] == "Juan"
        assert associate["surnames"] == "Pérez"
