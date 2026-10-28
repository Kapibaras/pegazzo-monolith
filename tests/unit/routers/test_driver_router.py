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
        response = authorized_client.get(self.ENDPOINT)
        ids = [d["id"] for d in response.json()["drivers"]]
        assert ids[0] == "DRV-002"

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


@pytest.mark.usefixtures("authorized_client", "client", "admin_authorized_client")
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

    def test_create_driver_requires_auth(self, client):
        response = client.post(self.ENDPOINT, json=_VALID_DRIVER_BODY)
        assert response.status_code == 401
