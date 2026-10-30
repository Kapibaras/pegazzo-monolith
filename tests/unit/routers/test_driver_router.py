import pytest

_VALID_DRIVER_BODY = {
    "id": "DRV-NEW",
    "name": "Carlos",
    "surnames": "Ramírez Vega",
    "status": "ACTIVE",
    "telephones": ["+525551234567"],
    "licenseNumber": "LICNEW",
    "licenseValidity": "2028-06-01T00:00:00+00:00",
    "identificationNumber": "IDNEW",
    "address": "Calle Nueva #10",
    "garageAddress": ["Calle Garage #20"],
}


@pytest.mark.usefixtures("authorized_client", "client")
class TestDriverRouter:
    """Tests for GET /management/drivers."""

    ENDPOINT = "/pegazzo/management/drivers"

    # -----------------------------------------------------------------
    # Basic listing
    # -----------------------------------------------------------------

    def test_list_drivers_returns_seeded(self, authorized_client):
        response = authorized_client.get(self.ENDPOINT)
        assert response.status_code == 200
        data = response.json()
        assert len(data["drivers"]) == 2
        assert data["pagination"]["total"] == 2
        assert data["pagination"]["page"] == 1

    def test_list_drivers_summary_fields(self, authorized_client):
        response = authorized_client.get(self.ENDPOINT)
        driver = response.json()["drivers"][0]
        assert "id" in driver
        assert "name" in driver
        assert "surnames" in driver
        assert "status" in driver
        assert "photo" in driver

    # -----------------------------------------------------------------
    # Filtering
    # -----------------------------------------------------------------

    def test_filter_by_status_active(self, authorized_client):
        response = authorized_client.get(self.ENDPOINT, params={"status": "ACTIVE"})
        assert response.status_code == 200
        drivers = response.json()["drivers"]
        assert len(drivers) == 1
        assert drivers[0]["status"] == "ACTIVE"

    def test_filter_by_status_inactive(self, authorized_client):
        response = authorized_client.get(self.ENDPOINT, params={"status": "INACTIVE"})
        drivers = response.json()["drivers"]
        assert len(drivers) == 1
        assert drivers[0]["status"] == "INACTIVE"

    def test_filter_by_status_no_match(self, authorized_client):
        response = authorized_client.get(self.ENDPOINT, params={"status": "SUSPENDED"})
        drivers = response.json()["drivers"]
        assert len(drivers) == 0

    # -----------------------------------------------------------------
    # Archived
    # -----------------------------------------------------------------

    def test_archived_false_excludes_archived(self, authorized_client):
        response = authorized_client.get(self.ENDPOINT)
        ids = [d["id"] for d in response.json()["drivers"]]
        assert "DRV-003" not in ids

    def test_archived_true_returns_only_archived(self, authorized_client):
        response = authorized_client.get(self.ENDPOINT, params={"archived": "true"})
        drivers = response.json()["drivers"]
        assert len(drivers) == 1
        assert drivers[0]["id"] == "DRV-003"

    # -----------------------------------------------------------------
    # Search
    # -----------------------------------------------------------------

    def test_search_by_name(self, authorized_client):
        response = authorized_client.get(self.ENDPOINT, params={"search": "Luis"})
        drivers = response.json()["drivers"]
        assert len(drivers) == 1
        assert drivers[0]["name"] == "Luis"

    def test_search_by_surnames(self, authorized_client):
        response = authorized_client.get(self.ENDPOINT, params={"search": "Hernández"})
        drivers = response.json()["drivers"]
        assert len(drivers) == 1
        assert drivers[0]["surnames"] == "Hernández Ruiz"

    def test_search_by_exact_id(self, authorized_client):
        response = authorized_client.get(self.ENDPOINT, params={"search": "DRV-001"})
        drivers = response.json()["drivers"]
        assert len(drivers) == 1
        assert drivers[0]["id"] == "DRV-001"

    def test_search_no_match(self, authorized_client):
        response = authorized_client.get(self.ENDPOINT, params={"search": "Zzzzz"})
        assert response.json()["drivers"] == []

    # -----------------------------------------------------------------
    # Sorting
    # -----------------------------------------------------------------

    def test_sort_by_name_asc(self, authorized_client):
        response = authorized_client.get(self.ENDPOINT, params={"sortBy": "name", "sortOrder": "asc"})
        names = [d["name"] for d in response.json()["drivers"]]
        assert names == sorted(names)

    def test_sort_by_name_desc(self, authorized_client):
        response = authorized_client.get(self.ENDPOINT, params={"sortBy": "name", "sortOrder": "desc"})
        names = [d["name"] for d in response.json()["drivers"]]
        assert names == sorted(names, reverse=True)

    def test_sort_by_created_at_default_desc(self, authorized_client):
        """Default sort is created_at DESC.

        DRV-002 (2026-02-20) should come before DRV-001 (2026-01-15).
        The summary schema does not expose createdAt, so we verify
        ordering through the known seed IDs.
        """
        response = authorized_client.get(self.ENDPOINT)
        ids = [d["id"] for d in response.json()["drivers"]]
        assert ids == ["DRV-002", "DRV-001"]

    # -----------------------------------------------------------------
    # Pagination
    # -----------------------------------------------------------------

    def test_pagination_limit(self, authorized_client):
        response = authorized_client.get(self.ENDPOINT, params={"limit": 1})
        data = response.json()
        assert len(data["drivers"]) == 1
        assert data["pagination"]["total"] == 2
        assert data["pagination"]["totalPages"] == 2

    def test_pagination_page_2(self, authorized_client):
        response = authorized_client.get(self.ENDPOINT, params={"limit": 1, "page": 2})
        data = response.json()
        assert len(data["drivers"]) == 1
        assert data["pagination"]["page"] == 2

    def test_pagination_beyond_last_page(self, authorized_client):
        response = authorized_client.get(self.ENDPOINT, params={"page": 99})
        data = response.json()
        assert len(data["drivers"]) == 0
        assert data["pagination"]["total"] == 2

    # -----------------------------------------------------------------
    # RBAC
    # -----------------------------------------------------------------

    def test_list_drivers_requires_auth(self, client):
        response = client.get(self.ENDPOINT)
        assert response.status_code == 401


@pytest.mark.usefixtures("authorized_client", "client")
class TestCreateDriver:
    """Tests for POST /management/drivers."""

    ENDPOINT = "/pegazzo/management/drivers"

    # -----------------------------------------------------------------
    # Success
    # -----------------------------------------------------------------

    def test_create_driver_success(self, authorized_client):
        response = authorized_client.post(self.ENDPOINT, json=_VALID_DRIVER_BODY)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "DRV-NEW"
        assert data["name"] == "Carlos"
        assert data["surnames"] == "Ramírez Vega"
        assert data["status"] == "ACTIVE"
        assert data["telephones"] == ["+525551234567"]
        assert data["licenseNumber"] == "LICNEW"
        assert data["identificationNumber"] == "IDNEW"
        assert data["address"] == "Calle Nueva #10"
        assert data["garageAddress"] == ["Calle Garage #20"]

    def test_create_driver_returns_timestamps(self, authorized_client):
        response = authorized_client.post(self.ENDPOINT, json=_VALID_DRIVER_BODY)
        data = response.json()
        assert "createdAt" in data
        assert "updatedAt" in data

    def test_create_driver_admin_allowed(self, admin_authorized_client):
        response = admin_authorized_client.post(self.ENDPOINT, json=_VALID_DRIVER_BODY)
        assert response.status_code == 201

    # -----------------------------------------------------------------
    # Uniqueness validations
    # -----------------------------------------------------------------

    def test_create_driver_duplicate_id(self, authorized_client):
        body = {**_VALID_DRIVER_BODY, "id": "DRV-001"}
        response = authorized_client.post(self.ENDPOINT, json=body)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_driver_duplicate_identification_number(self, authorized_client):
        body = {**_VALID_DRIVER_BODY, "identificationNumber": "ID001"}
        response = authorized_client.post(self.ENDPOINT, json=body)
        assert response.status_code == 400
        assert "Identification number" in response.json()["detail"]

    def test_create_driver_duplicate_license_number(self, authorized_client):
        body = {**_VALID_DRIVER_BODY, "licenseNumber": "LIC001"}
        response = authorized_client.post(self.ENDPOINT, json=body)
        assert response.status_code == 400
        assert "License number" in response.json()["detail"]

    # -----------------------------------------------------------------
    # Date validation
    # -----------------------------------------------------------------

    def test_create_driver_license_validity_in_past(self, authorized_client):
        body = {**_VALID_DRIVER_BODY, "licenseValidity": "2020-01-01T00:00:00+00:00"}
        response = authorized_client.post(self.ENDPOINT, json=body)
        assert response.status_code == 400
        assert "past date" in response.json()["detail"]

    # -----------------------------------------------------------------
    # Schema validation
    # -----------------------------------------------------------------

    def test_create_driver_missing_required_field(self, authorized_client):
        body = {k: v for k, v in _VALID_DRIVER_BODY.items() if k != "name"}
        response = authorized_client.post(self.ENDPOINT, json=body)
        assert response.status_code == 422

    def test_create_driver_empty_telephones(self, authorized_client):
        body = {**_VALID_DRIVER_BODY, "telephones": []}
        response = authorized_client.post(self.ENDPOINT, json=body)
        assert response.status_code == 422

    def test_create_driver_empty_garage_address(self, authorized_client):
        body = {**_VALID_DRIVER_BODY, "garageAddress": []}
        response = authorized_client.post(self.ENDPOINT, json=body)
        assert response.status_code == 422

    # -----------------------------------------------------------------
    # RBAC
    # -----------------------------------------------------------------

    def test_create_driver_employee_forbidden(self, employee_authorized_client):
        response = employee_authorized_client.post(self.ENDPOINT, json=_VALID_DRIVER_BODY)
        assert response.status_code == 403

    def test_create_driver_license_validity_tomorrow_accepted(self, authorized_client):
        from datetime import UTC, datetime, timedelta

        tomorrow = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        body = {**_VALID_DRIVER_BODY, "id": "DRV-TMRW", "licenseValidity": tomorrow}
        response = authorized_client.post(self.ENDPOINT, json=body)
        assert response.status_code == 201

    def test_create_driver_requires_auth(self, client):
        response = client.post(self.ENDPOINT, json=_VALID_DRIVER_BODY)
        assert response.status_code == 401


@pytest.mark.usefixtures("authorized_client", "client")
class TestGetDriverDetail:
    """Tests for GET /management/drivers/{id}."""

    ENDPOINT = "/pegazzo/management/drivers"

    # -----------------------------------------------------------------
    # Basic detail
    # -----------------------------------------------------------------

    def test_get_driver_basic_fields(self, authorized_client):
        response = authorized_client.get(f"{self.ENDPOINT}/DRV-001")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "DRV-001"
        assert data["name"] == "Luis"
        assert data["surnames"] == "García López"
        assert data["status"] == "ACTIVE"
        assert data["telephones"] == ["+521234567890"]
        assert data["licenseNumber"] == "LIC001"
        assert data["identificationNumber"] == "ID001"
        assert data["address"] == "Calle 1 #100"
        assert data["garageAddress"] == ["Calle 2 #200"]
        assert "createdAt" in data
        assert "updatedAt" in data

    def test_get_driver_not_found(self, authorized_client):
        response = authorized_client.get(f"{self.ENDPOINT}/NOTEXIST")
        assert response.status_code == 404
        assert "was not found" in response.json()["detail"]

    # -----------------------------------------------------------------
    # Documents
    # -----------------------------------------------------------------

    def test_get_driver_with_no_documents(self, authorized_client):
        response = authorized_client.get(f"{self.ENDPOINT}/DRV-001")
        assert response.json()["documents"] == []

    def test_get_driver_with_documents(self, authorized_client):
        from unittest.mock import patch

        from app.models.document import Document

        doc = Document(id=1, type="PDF", url="docs/ine.pdf", category="ine", expiry_date=None)
        authorized_client.driver_repo.driver_documents["DRV-001"] = [doc]

        with patch("app.services.driver.r2.generate_document_read_url", return_value="https://presigned.url/ine.pdf"):
            response = authorized_client.get(f"{self.ENDPOINT}/DRV-001")

        docs = response.json()["documents"]
        assert len(docs) == 1
        assert docs[0]["type"] == "PDF"
        assert docs[0]["url"] == "https://presigned.url/ine.pdf"
        assert docs[0]["category"] == "ine"

    # -----------------------------------------------------------------
    # Guarantors
    # -----------------------------------------------------------------

    def test_get_driver_with_no_guarantors(self, authorized_client):
        response = authorized_client.get(f"{self.ENDPOINT}/DRV-001")
        assert response.json()["guarantors"] == []

    # -----------------------------------------------------------------
    # Assigned car
    # -----------------------------------------------------------------

    def test_get_driver_no_assigned_car(self, authorized_client):
        response = authorized_client.get(f"{self.ENDPOINT}/DRV-001")
        assert response.json()["assignedCar"] is None

    def test_get_driver_with_assigned_car(self, authorized_client):
        from datetime import date
        from unittest.mock import MagicMock

        from app.models.contract import Contract

        mock_car = MagicMock()
        mock_car.id = "CAR-001"
        mock_car.make = "Toyota"
        mock_car.model = "Corolla"
        mock_car.plate = "ABC123"
        mock_car.agency_image = None

        contract = Contract(
            id="CTR-001",
            start_date=date(2020, 1, 1),
            end_date=date(2030, 12, 31),
            type="rent",
            amount=1000,
            guarantee_amount=500,
            car_id="CAR-001",
            driver_id="DRV-001",
        )
        contract.car = mock_car

        authorized_client.driver_repo.contracts.append(contract)

        response = authorized_client.get(f"{self.ENDPOINT}/DRV-001")
        car = response.json()["assignedCar"]
        assert car is not None
        assert car["id"] == "CAR-001"
        assert car["make"] == "Toyota"
        assert car["model"] == "Corolla"
        assert car["plate"] == "ABC123"

    # -----------------------------------------------------------------
    # RBAC
    # -----------------------------------------------------------------

    def test_get_driver_requires_auth(self, client):
        response = client.get(f"{self.ENDPOINT}/DRV-001")
        assert response.status_code == 401


@pytest.mark.usefixtures("authorized_client", "client", "employee_authorized_client")
class TestArchiveDriver:
    """Tests for PATCH /management/drivers/{id}/archive."""

    ENDPOINT = "/pegazzo/management/drivers/{driver_id}/archive"

    def test_archive_driver_success(self, authorized_client):
        url = self.ENDPOINT.format(driver_id="DRV-001")
        response = authorized_client.patch(url)
        assert response.status_code == 200
        assert response.json()["archivedAt"] is not None

    def test_archive_driver_not_found(self, authorized_client):
        url = self.ENDPOINT.format(driver_id="NOTEXIST")
        response = authorized_client.patch(url)
        assert response.status_code == 404
        assert "was not found" in response.json()["detail"]

    def test_archive_driver_with_active_contract(self, authorized_client):
        from datetime import date

        from app.models.contract import Contract

        contract = Contract(
            id="CTR-001",
            start_date=date(2020, 1, 1),
            end_date=date(2030, 12, 31),
            type="rent",
            amount=1000,
            guarantee_amount=500,
            car_id="CAR-001",
            driver_id="DRV-001",
        )
        authorized_client.driver_repo.contracts.append(contract)

        url = self.ENDPOINT.format(driver_id="DRV-001")
        response = authorized_client.patch(url)
        assert response.status_code == 400
        assert "active contract" in response.json()["detail"]

    def test_archive_driver_requires_auth(self, client):
        url = self.ENDPOINT.format(driver_id="DRV-001")
        response = client.patch(url)
        assert response.status_code == 401

    def test_archive_driver_employee_forbidden(self, employee_authorized_client):
        url = self.ENDPOINT.format(driver_id="DRV-001")
        response = employee_authorized_client.patch(url)
        assert response.status_code == 403


@pytest.mark.usefixtures("authorized_client", "client", "employee_authorized_client")
class TestUnarchiveDriver:
    """Tests for PATCH /management/drivers/{id}/unarchive."""

    ENDPOINT = "/pegazzo/management/drivers/{driver_id}/unarchive"

    def test_unarchive_driver_success(self, authorized_client):
        url = self.ENDPOINT.format(driver_id="DRV-003")
        response = authorized_client.patch(url)
        assert response.status_code == 200
        assert response.json()["archivedAt"] is None

    def test_unarchive_driver_not_found(self, authorized_client):
        url = self.ENDPOINT.format(driver_id="NOTEXIST")
        response = authorized_client.patch(url)
        assert response.status_code == 404

    def test_unarchive_driver_requires_auth(self, client):
        url = self.ENDPOINT.format(driver_id="DRV-003")
        response = client.patch(url)
        assert response.status_code == 401

    def test_unarchive_driver_employee_forbidden(self, employee_authorized_client):
        url = self.ENDPOINT.format(driver_id="DRV-003")
        response = employee_authorized_client.patch(url)
        assert response.status_code == 403


@pytest.mark.usefixtures("authorized_client", "client", "employee_authorized_client")
class TestDeleteDriver:
    """Tests for DELETE /management/drivers/{id}."""

    ENDPOINT = "/pegazzo/management/drivers/{driver_id}"

    def test_delete_driver_success(self, authorized_client):
        url = self.ENDPOINT.format(driver_id="DRV-003")
        response = authorized_client.delete(url)
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()
        assert authorized_client.driver_repo.get_by_id("DRV-003") is None

    def test_delete_driver_not_found(self, authorized_client):
        url = self.ENDPOINT.format(driver_id="NOTEXIST")
        response = authorized_client.delete(url)
        assert response.status_code == 404

    def test_delete_driver_not_archived(self, authorized_client):
        url = self.ENDPOINT.format(driver_id="DRV-001")
        response = authorized_client.delete(url)
        assert response.status_code == 400
        assert "must be archived" in response.json()["detail"]

    def test_delete_driver_with_documents(self, authorized_client):
        from app.models.document import Document

        doc = Document(id=10, type="PDF", url="docs/ine.pdf", category="ine", expiry_date=None)
        authorized_client.driver_repo.driver_documents["DRV-003"] = [doc]

        url = self.ENDPOINT.format(driver_id="DRV-003")
        response = authorized_client.delete(url)
        assert response.status_code == 200
        assert authorized_client.driver_repo.driver_documents.get("DRV-003") is None

    def test_delete_driver_guarantor_orphan(self, authorized_client):
        from app.models.document import Document

        authorized_client.guarantor_repo.link_to_driver("DRV-003", 1)

        guarantor = authorized_client.guarantor_repo.get_by_id(1)
        doc = Document(id=99, type="PDF", url="docs/guarantor.pdf", category="ine", expiry_date=None)
        guarantor.documents = [doc]

        drv = authorized_client.driver_repo.get_by_id("DRV-003")
        drv.guarantors = [guarantor]

        url = self.ENDPOINT.format(driver_id="DRV-003")
        response = authorized_client.delete(url)
        assert response.status_code == 200
        assert authorized_client.guarantor_repo.get_by_id(1) is None

    def test_delete_driver_guarantor_shared(self, authorized_client):
        authorized_client.guarantor_repo.link_to_driver("DRV-003", 1)
        authorized_client.guarantor_repo.link_to_driver("DRV-001", 1)

        drv = authorized_client.driver_repo.get_by_id("DRV-003")
        drv.guarantors = [authorized_client.guarantor_repo.get_by_id(1)]

        url = self.ENDPOINT.format(driver_id="DRV-003")
        response = authorized_client.delete(url)
        assert response.status_code == 200
        assert authorized_client.guarantor_repo.get_by_id(1) is not None
        assert not authorized_client.guarantor_repo.is_linked_to_driver("DRV-003", 1)
        assert authorized_client.guarantor_repo.is_linked_to_driver("DRV-001", 1)

    def test_delete_driver_requires_auth(self, client):
        url = self.ENDPOINT.format(driver_id="DRV-003")
        response = client.delete(url)
        assert response.status_code == 401

    def test_delete_driver_employee_forbidden(self, employee_authorized_client):
        url = self.ENDPOINT.format(driver_id="DRV-003")
        response = employee_authorized_client.delete(url)
        assert response.status_code == 403
