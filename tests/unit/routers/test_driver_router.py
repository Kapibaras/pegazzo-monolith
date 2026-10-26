import pytest


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
