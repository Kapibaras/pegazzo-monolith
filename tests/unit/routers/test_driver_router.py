import re
from datetime import UTC, date, datetime
from unittest.mock import patch

import pytest

from app.models.contract import Contract
from app.models.document import Document

_ADDRESS_FIELDS = {
    "street": "Calle Nueva",
    "exteriorNumber": "10",
    "neighborhood": "Centro",
    "postalCode": "06000",
    "municipality": "Cuauhtémoc",
    "state": "CDMX",
}
_ADDRESS_TEXT = "Calle Nueva 10, Col. Centro, C.P. 06000, Cuauhtémoc, CDMX"
_SEED_CURP_1 = "AAAA010101HDFXXX01"
_SEED_CURP_2 = "AAAA010101HDFXXX02"

_VALID_DRIVER_BODY = {
    "name": "Carlos",
    "surnames": "Ramírez Vega",
    "status": "ACTIVE",
    "telephones": ["+525551234567"],
    "licenseNumber": "LICNEW",
    "licenseValidity": "2028-06-01T00:00:00+00:00",
    "identificationNumber": "NEWW010101HDFXXX01",
    "addressFields": _ADDRESS_FIELDS,
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
        assert data["id"] == "CD-CRV-0001"
        assert data["name"] == "Carlos"
        assert data["surnames"] == "Ramírez Vega"
        assert data["status"] == "ACTIVE"
        assert data["telephones"] == ["+525551234567"]
        assert data["licenseNumber"] == "LICNEW"
        assert data["identificationNumber"] == "NEWW010101HDFXXX01"
        assert data["address"] == _ADDRESS_TEXT
        assert data["addressFields"] == {**_ADDRESS_FIELDS, "interiorNumber": None}
        assert "garageAddress" not in data

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

    def test_create_driver_assigns_generated_folio(self, authorized_client):
        response = authorized_client.post(self.ENDPOINT, json=_VALID_DRIVER_BODY)
        assert response.status_code == 201
        assert re.fullmatch(r"CD-CRV-\d{4}", response.json()["id"])

    def test_create_driver_ignores_client_provided_id(self, authorized_client):
        response = authorized_client.post(self.ENDPOINT, json={**_VALID_DRIVER_BODY, "id": "DRV-001"})
        assert response.status_code == 201
        assert response.json()["id"] != "DRV-001"

    def test_create_driver_folios_are_unique_and_consecutive(self, authorized_client):
        first = authorized_client.post(self.ENDPOINT, json=_VALID_DRIVER_BODY).json()["id"]
        second_body = {**_VALID_DRIVER_BODY, "licenseNumber": "LIC-B", "identificationNumber": "NEWW010101HDFXXX02"}
        second = authorized_client.post(self.ENDPOINT, json=second_body).json()["id"]
        assert first != second
        assert int(second[-4:]) == int(first[-4:]) + 1

    def test_create_driver_duplicate_identification_number(self, authorized_client):
        body = {**_VALID_DRIVER_BODY, "identificationNumber": _SEED_CURP_1}
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

    @pytest.mark.parametrize("curp", ["SHORT", "NEWW010101HDFXXX012", ""])
    def test_create_driver_curp_must_have_18_characters(self, authorized_client, curp):
        body = {**_VALID_DRIVER_BODY, "identificationNumber": curp}
        response = authorized_client.post(self.ENDPOINT, json=body)
        assert response.status_code == 422

    @pytest.mark.parametrize("field", ["street", "exteriorNumber", "neighborhood", "postalCode", "municipality", "state"])
    def test_create_driver_address_fields_are_required(self, authorized_client, field):
        fields = {k: v for k, v in _ADDRESS_FIELDS.items() if k != field}
        response = authorized_client.post(self.ENDPOINT, json={**_VALID_DRIVER_BODY, "addressFields": fields})
        assert response.status_code == 422

    @pytest.mark.parametrize("postal_code", ["123", "1234a", "123456"])
    def test_create_driver_postal_code_must_have_5_digits(self, authorized_client, postal_code):
        fields = {**_ADDRESS_FIELDS, "postalCode": postal_code}
        response = authorized_client.post(self.ENDPOINT, json={**_VALID_DRIVER_BODY, "addressFields": fields})
        assert response.status_code == 422

    def test_create_driver_interior_number_is_part_of_the_joined_address(self, authorized_client):
        fields = {**_ADDRESS_FIELDS, "interiorNumber": "4B"}
        response = authorized_client.post(self.ENDPOINT, json={**_VALID_DRIVER_BODY, "addressFields": fields})
        assert response.status_code == 201
        assert response.json()["address"] == "Calle Nueva 10 Int. 4B, Col. Centro, C.P. 06000, Cuauhtémoc, CDMX"

    # -----------------------------------------------------------------
    # RBAC
    # -----------------------------------------------------------------

    def test_create_driver_employee_forbidden(self, employee_authorized_client):
        response = employee_authorized_client.post(self.ENDPOINT, json=_VALID_DRIVER_BODY)
        assert response.status_code == 403

    def test_create_driver_license_validity_tomorrow_accepted(self, authorized_client):
        from datetime import UTC, datetime, timedelta

        tomorrow = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        body = {**_VALID_DRIVER_BODY, "licenseValidity": tomorrow}
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
        assert data["identificationNumber"] == _SEED_CURP_1
        assert data["address"] == "Calle 1 #100"
        assert data["garages"] == []
        assert "createdAt" in data
        assert "updatedAt" in data
        assert data["archivedAt"] is None

    def test_get_driver_archived_returns_archived_at(self, authorized_client):
        response = authorized_client.get(f"{self.ENDPOINT}/DRV-003")
        assert response.status_code == 200
        assert response.json()["archivedAt"].startswith("2026-06-01")

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
        drv = authorized_client.driver_repo.get_by_id("DRV-001")
        drv.documents = [doc]

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

    def test_get_driver_with_guarantors_and_documents(self, authorized_client):
        from types import SimpleNamespace
        from unittest.mock import patch

        from app.models.document import Document

        gdoc = Document(id=50, type="PDF", url="docs/g_ine.pdf", category="ine", expiry_date=None)
        guarantor = SimpleNamespace(
            id=1,
            name="Carlos",
            surnames="López",
            telephones=["+521111111111"],
            address="Calle X",
            address_fields=None,
            relation="padre",
            documents=[gdoc],
        )

        drv = authorized_client.driver_repo.get_by_id("DRV-001")
        drv.guarantors = [guarantor]

        with patch("app.services.driver.r2.generate_document_read_url", return_value="https://presigned.url/g_ine.pdf"):
            response = authorized_client.get(f"{self.ENDPOINT}/DRV-001")

        gs = response.json()["guarantors"]
        assert len(gs) == 1
        assert gs[0]["name"] == "Carlos"
        assert gs[0]["relation"] == "padre"
        assert len(gs[0]["documents"]) == 1
        assert gs[0]["documents"][0]["url"] == "https://presigned.url/g_ine.pdf"

    def test_get_driver_document_expiry_status(self, authorized_client):
        from unittest.mock import patch

        from app.models.document import Document

        expired_doc = Document(
            id=60,
            type="PDF",
            url="docs/expired.pdf",
            category="ine",
            expiry_date=datetime(2020, 1, 1, tzinfo=UTC),
        )
        drv = authorized_client.driver_repo.get_by_id("DRV-001")
        drv.documents = [expired_doc]

        with patch("app.services.driver.r2.generate_document_read_url", return_value="https://url"):
            response = authorized_client.get(f"{self.ENDPOINT}/DRV-001")

        docs = response.json()["documents"]
        assert docs[0]["expiryStatus"].upper() == "EXPIRED"

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
        with patch("app.storage.r2.soft_delete_document") as mock_soft_delete:
            response = authorized_client.delete(url)
        assert response.status_code == 200
        assert authorized_client.driver_repo.driver_documents.get("DRV-003") is None
        mock_soft_delete.assert_called_once_with("docs/ine.pdf")

    def test_delete_driver_moves_own_photo_to_deleted(self, authorized_client):
        from app.storage import r2

        photo = r2.get_image_public_url("driver_photo/DRV-003/a.jpg")
        authorized_client.driver_repo.get_by_id("DRV-003").photo = photo

        url = self.ENDPOINT.format(driver_id="DRV-003")
        with patch("app.storage.r2.soft_delete_image") as mock_image:
            response = authorized_client.delete(url)
        assert response.status_code == 200
        mock_image.assert_called_once_with(photo)

    def test_delete_driver_skips_photo_outside_own_folder(self, authorized_client):
        from app.storage import r2

        authorized_client.driver_repo.get_by_id("DRV-003").photo = r2.get_image_public_url("driver_photo/OTHER/a.jpg")

        url = self.ENDPOINT.format(driver_id="DRV-003")
        with patch("app.storage.r2.soft_delete_image") as mock_image:
            response = authorized_client.delete(url)
        assert response.status_code == 200
        mock_image.assert_not_called()

    def test_delete_driver_photo_cleanup_failure_does_not_fail_request(self, authorized_client):
        from app.storage import r2

        authorized_client.driver_repo.get_by_id("DRV-003").photo = r2.get_image_public_url("driver_photo/DRV-003/a.jpg")

        url = self.ENDPOINT.format(driver_id="DRV-003")
        with patch("app.storage.r2.soft_delete_image", side_effect=RuntimeError("R2 down")):
            response = authorized_client.delete(url)
        assert response.status_code == 200

    def test_delete_driver_guarantor_orphan(self, authorized_client):
        from app.models.document import Document

        authorized_client.guarantor_repo.link_to_driver("DRV-003", 1)
        authorized_client.guarantor_repo.document_keys[1] = ["docs/guarantor.pdf"]

        guarantor = authorized_client.guarantor_repo.get_by_id(1)
        doc = Document(id=99, type="PDF", url="docs/guarantor.pdf", category="ine", expiry_date=None)
        guarantor.documents = [doc]

        drv = authorized_client.driver_repo.get_by_id("DRV-003")
        drv.guarantors = [guarantor]

        url = self.ENDPOINT.format(driver_id="DRV-003")
        with patch("app.storage.r2.soft_delete_document") as mock_soft_delete:
            response = authorized_client.delete(url)
        assert response.status_code == 200
        assert authorized_client.guarantor_repo.get_by_id(1) is None
        mock_soft_delete.assert_called_once_with("docs/guarantor.pdf")

    def test_delete_driver_storage_failure_does_not_fail_request(self, authorized_client):
        from app.models.document import Document

        doc = Document(id=10, type="PDF", url="docs/ine.pdf", category="ine", expiry_date=None)
        authorized_client.driver_repo.driver_documents["DRV-003"] = [doc]

        url = self.ENDPOINT.format(driver_id="DRV-003")
        with patch("app.storage.r2.soft_delete_document", side_effect=RuntimeError("R2 down")):
            response = authorized_client.delete(url)
        assert response.status_code == 200
        assert authorized_client.driver_repo.get_by_id("DRV-003") is None

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


def _past_contract(driver_id: str) -> Contract:
    return Contract(
        id="CTR-OLD",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        type="rent",
        amount=1000,
        guarantee_amount=500,
        car_id="CAR-001",
        driver_id=driver_id,
    )


@pytest.mark.usefixtures("authorized_client")
class TestSoftDeleteDriver:
    """DELETE on a driver with history keeps its data and hides it from the API."""

    DRIVERS = "/pegazzo/management/drivers"

    @pytest.fixture(autouse=True)
    def _soft_deleted_driver(self, authorized_client):
        self.contract = _past_contract("DRV-003")
        authorized_client.driver_repo.contracts.append(self.contract)
        authorized_client.driver_repo.driver_documents["DRV-003"] = [
            Document(id=10, type="PDF", url="docs/ine.pdf", category="ine", expiry_date=None),
        ]
        with patch("app.storage.r2.soft_delete_document") as mock_soft_delete:
            self.response = authorized_client.delete(f"{self.DRIVERS}/DRV-003")
        self.mock_soft_delete = mock_soft_delete

    def test_driver_with_history_is_soft_deleted(self, authorized_client):
        assert self.response.status_code == 200
        assert "history preserved" in self.response.json()["message"]
        driver = authorized_client.driver_repo.get_by_id("DRV-003", include_deleted=True)
        assert driver.deleted_at is not None

    def test_soft_delete_keeps_contract_documents_and_files(self, authorized_client):
        assert self.contract.driver_id == "DRV-003"
        assert authorized_client.driver_repo.driver_documents["DRV-003"]
        self.mock_soft_delete.assert_not_called()

    def test_soft_deleted_driver_is_not_found(self, authorized_client):
        assert authorized_client.get(f"{self.DRIVERS}/DRV-003").status_code == 404
        assert authorized_client.patch(f"{self.DRIVERS}/DRV-003/unarchive").status_code == 404
        assert authorized_client.patch(f"{self.DRIVERS}/DRV-003", json={"name": "X"}).status_code == 404
        assert authorized_client.patch(f"{self.DRIVERS}/DRV-003/status", json={"status": "ACTIVE"}).status_code == 404
        assert authorized_client.delete(f"{self.DRIVERS}/DRV-003").status_code == 404

    def test_soft_deleted_driver_is_not_listed(self, authorized_client):
        response = authorized_client.get(self.DRIVERS, params={"archived": True})
        assert "DRV-003" not in [d["id"] for d in response.json()["drivers"]]

    def test_soft_deleted_driver_folio_is_skipped(self, authorized_client):
        taken = authorized_client.driver_repo.get_by_id("DRV-003", include_deleted=True)
        taken.id = "CD-CRV-0001"
        response = authorized_client.post(self.DRIVERS, json=_VALID_DRIVER_BODY)
        assert response.status_code == 201
        assert response.json()["id"] == "CD-CRV-0002"


@pytest.mark.usefixtures("authorized_client", "client", "admin_authorized_client", "employee_authorized_client")
class TestUpdateDriver:
    """Tests for PATCH /management/drivers/{id}."""

    ENDPOINT = "/pegazzo/management/drivers"

    # -----------------------------------------------------------------
    # Successful updates
    # -----------------------------------------------------------------

    def test_update_driver_name_success(self, authorized_client):
        response = authorized_client.patch(f"{self.ENDPOINT}/DRV-001", json={"name": "Pedro"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Pedro"
        assert data["surnames"] == "García López"

    def test_update_driver_multiple_fields(self, authorized_client):
        body = {"name": "Juan", "surnames": "López Ruiz", "addressFields": _ADDRESS_FIELDS}
        response = authorized_client.patch(f"{self.ENDPOINT}/DRV-001", json=body)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Juan"
        assert data["surnames"] == "López Ruiz"
        assert data["address"] == _ADDRESS_TEXT
        assert data["addressFields"] == {**_ADDRESS_FIELDS, "interiorNumber": None}

    def test_update_driver_telephones(self, authorized_client):
        body = {"telephones": ["+525559999999", "+525558888888"]}
        response = authorized_client.patch(f"{self.ENDPOINT}/DRV-001", json=body)
        assert response.status_code == 200
        assert response.json()["telephones"] == ["+525559999999", "+525558888888"]

    def test_update_driver_ignores_the_removed_garage_address_field(self, authorized_client):
        # Garages are managed through /drivers/{id}/garages now; the old field alone is an empty update.
        response = authorized_client.patch(f"{self.ENDPOINT}/DRV-001", json={"garageAddress": ["Nueva Garage #1"]})
        assert response.status_code == 422

    def test_update_driver_photo(self, authorized_client):
        body = {"photo": "https://images.example.com/new-photo.jpg"}
        response = authorized_client.patch(f"{self.ENDPOINT}/DRV-001", json=body)
        assert response.status_code == 200
        assert response.json()["photo"] == "https://images.example.com/new-photo.jpg"

    def test_update_driver_license_validity_future(self, authorized_client):
        from datetime import timedelta

        future = (datetime.now(UTC) + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        response = authorized_client.patch(f"{self.ENDPOINT}/DRV-001", json={"licenseValidity": future})
        assert response.status_code == 200

    def test_update_driver_clear_photo_with_null(self, authorized_client):
        response = authorized_client.patch(f"{self.ENDPOINT}/DRV-001", json={"photo": None})
        assert response.status_code == 200
        assert response.json()["photo"] is None

    def test_update_driver_omitted_photo_is_kept(self, authorized_client):
        response = authorized_client.patch(f"{self.ENDPOINT}/DRV-001", json={"name": "Pedro"})
        assert response.status_code == 200
        assert response.json()["photo"] == "https://images.example.com/drv001.jpg"

    def test_update_driver_unchanged_expired_license_validity(self, authorized_client):
        authorized_client.driver_repo.get_by_id("DRV-001").license_validity = datetime(2025, 1, 1, tzinfo=UTC)
        response = authorized_client.patch(
            f"{self.ENDPOINT}/DRV-001",
            json={"name": "Pedro", "licenseValidity": "2025-01-01T00:00:00+00:00"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Pedro"

    def test_update_driver_returns_timestamps(self, authorized_client):
        response = authorized_client.patch(f"{self.ENDPOINT}/DRV-001", json={"name": "Nuevo"})
        data = response.json()
        assert "createdAt" in data
        assert "updatedAt" in data

    # -----------------------------------------------------------------
    # Uniqueness re-validation
    # -----------------------------------------------------------------

    def test_update_driver_duplicate_identification_number(self, authorized_client):
        response = authorized_client.patch(
            f"{self.ENDPOINT}/DRV-001",
            json={"identificationNumber": _SEED_CURP_2},
        )
        assert response.status_code == 400
        assert "Identification number" in response.json()["detail"]

    def test_update_driver_same_identification_number(self, authorized_client):
        response = authorized_client.patch(
            f"{self.ENDPOINT}/DRV-001",
            json={"identificationNumber": _SEED_CURP_1},
        )
        assert response.status_code == 200

    def test_update_driver_duplicate_license_number(self, authorized_client):
        response = authorized_client.patch(
            f"{self.ENDPOINT}/DRV-001",
            json={"licenseNumber": "LIC002"},
        )
        assert response.status_code == 400
        assert "License number" in response.json()["detail"]

    def test_update_driver_same_license_number(self, authorized_client):
        response = authorized_client.patch(
            f"{self.ENDPOINT}/DRV-001",
            json={"licenseNumber": "LIC001"},
        )
        assert response.status_code == 200

    # -----------------------------------------------------------------
    # Validation errors
    # -----------------------------------------------------------------

    def test_update_driver_license_validity_in_past(self, authorized_client):
        response = authorized_client.patch(
            f"{self.ENDPOINT}/DRV-001",
            json={"licenseValidity": "2020-01-01T00:00:00+00:00"},
        )
        assert response.status_code == 400

    def test_update_driver_not_found(self, authorized_client):
        response = authorized_client.patch(f"{self.ENDPOINT}/NOTEXIST", json={"name": "X"})
        assert response.status_code == 404
        assert "was not found" in response.json()["detail"]

    def test_update_driver_not_found_takes_precedence_over_past_license(self, authorized_client):
        response = authorized_client.patch(
            f"{self.ENDPOINT}/NOTEXIST",
            json={"licenseValidity": "2020-01-01T00:00:00+00:00"},
        )
        assert response.status_code == 404

    def test_update_driver_empty_body(self, authorized_client):
        response = authorized_client.patch(f"{self.ENDPOINT}/DRV-001", json={})
        assert response.status_code == 422

    def test_update_driver_null_on_required_field(self, authorized_client):
        response = authorized_client.patch(f"{self.ENDPOINT}/DRV-001", json={"name": None})
        assert response.status_code == 422

    def test_update_driver_empty_telephones_list(self, authorized_client):
        response = authorized_client.patch(f"{self.ENDPOINT}/DRV-001", json={"telephones": []})
        assert response.status_code == 422

    def test_update_driver_name_too_long(self, authorized_client):
        response = authorized_client.patch(f"{self.ENDPOINT}/DRV-001", json={"name": "A" * 51})
        assert response.status_code == 422

    def test_update_driver_telephones_item_too_long(self, authorized_client):
        response = authorized_client.patch(
            f"{self.ENDPOINT}/DRV-001",
            json={"telephones": ["+" + "1" * 25]},
        )
        assert response.status_code == 422

    def test_update_driver_address_fields_incomplete(self, authorized_client):
        response = authorized_client.patch(
            f"{self.ENDPOINT}/DRV-001",
            json={"addressFields": {"street": "Solo calle"}},
        )
        assert response.status_code == 422

    # -----------------------------------------------------------------
    # RBAC
    # -----------------------------------------------------------------

    def test_update_driver_requires_auth(self, client):
        response = client.patch(f"{self.ENDPOINT}/DRV-001", json={"name": "X"})
        assert response.status_code == 401

    def test_update_driver_employee_forbidden(self, employee_authorized_client):
        response = employee_authorized_client.patch(f"{self.ENDPOINT}/DRV-001", json={"name": "X"})
        assert response.status_code == 403

    def test_update_driver_admin_allowed(self, admin_authorized_client):
        response = admin_authorized_client.patch(f"{self.ENDPOINT}/DRV-001", json={"name": "Admin"})
        assert response.status_code == 200
        assert response.json()["name"] == "Admin"


@pytest.mark.usefixtures("authorized_client", "client", "admin_authorized_client", "employee_authorized_client")
class TestChangeDriverStatus:
    """Tests for PATCH /management/drivers/{id}/status."""

    ENDPOINT = "/pegazzo/management/drivers"

    # -----------------------------------------------------------------
    # Successful status changes
    # -----------------------------------------------------------------

    def test_change_status_to_inactive(self, authorized_client):
        response = authorized_client.patch(
            f"{self.ENDPOINT}/DRV-001/status",
            json={"status": "INACTIVE"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "INACTIVE"

    def test_change_status_to_suspended(self, authorized_client):
        response = authorized_client.patch(
            f"{self.ENDPOINT}/DRV-001/status",
            json={"status": "SUSPENDED"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "SUSPENDED"

    def test_change_status_to_active(self, authorized_client):
        response = authorized_client.patch(
            f"{self.ENDPOINT}/DRV-002/status",
            json={"status": "ACTIVE"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ACTIVE"

    def test_change_status_idempotent(self, authorized_client):
        response = authorized_client.patch(
            f"{self.ENDPOINT}/DRV-001/status",
            json={"status": "ACTIVE"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ACTIVE"

    # -----------------------------------------------------------------
    # Errors
    # -----------------------------------------------------------------

    def test_change_status_not_found(self, authorized_client):
        response = authorized_client.patch(
            f"{self.ENDPOINT}/NOTEXIST/status",
            json={"status": "ACTIVE"},
        )
        assert response.status_code == 404

    def test_change_status_invalid_value(self, authorized_client):
        response = authorized_client.patch(
            f"{self.ENDPOINT}/DRV-001/status",
            json={"status": "INVALID"},
        )
        assert response.status_code == 422

    # -----------------------------------------------------------------
    # RBAC
    # -----------------------------------------------------------------

    def test_change_status_requires_auth(self, client):
        response = client.patch(f"{self.ENDPOINT}/DRV-001/status", json={"status": "INACTIVE"})
        assert response.status_code == 401

    def test_change_status_employee_forbidden(self, employee_authorized_client):
        response = employee_authorized_client.patch(
            f"{self.ENDPOINT}/DRV-001/status",
            json={"status": "INACTIVE"},
        )
        assert response.status_code == 403

    def test_change_status_admin_allowed(self, admin_authorized_client):
        response = admin_authorized_client.patch(
            f"{self.ENDPOINT}/DRV-001/status",
            json={"status": "INACTIVE"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "INACTIVE"
