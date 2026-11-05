from unittest.mock import patch

import pytest

_ADDRESS_FIELDS = {
    "street": "Calle Nueva",
    "exteriorNumber": "10",
    "neighborhood": "Centro",
    "postalCode": "06000",
    "municipality": "Cuauhtémoc",
    "state": "CDMX",
}
_ADDRESS_TEXT = "Calle Nueva 10, Col. Centro, C.P. 06000, Cuauhtémoc, CDMX"

_VALID_GUARANTOR_BODY = {
    "name": "Carlos",
    "surnames": "Ramírez Vega",
    "telephones": ["+525551234567"],
    "addressFields": _ADDRESS_FIELDS,
    "relation": "father",
}


@pytest.mark.usefixtures("authorized_client", "client")
class TestCreateGuarantor:
    """Tests for POST /management/drivers/{driver_id}/guarantors."""

    ENDPOINT = "/pegazzo/management/drivers/{driver_id}/guarantors"

    # -----------------------------------------------------------------
    # Success
    # -----------------------------------------------------------------

    def test_create_guarantor_success(self, authorized_client):
        url = self.ENDPOINT.format(driver_id="DRV-001")
        response = authorized_client.post(url, json=_VALID_GUARANTOR_BODY)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Carlos"
        assert data["surnames"] == "Ramírez Vega"
        assert data["telephones"] == ["+525551234567"]
        assert data["address"] == _ADDRESS_TEXT
        assert data["addressFields"] == {**_ADDRESS_FIELDS, "interiorNumber": None}
        assert data["relation"] == "father"
        assert "id" in data
        assert "createdAt" in data
        assert "updatedAt" in data

    def test_create_guarantor_linked_to_driver(self, authorized_client):
        url = self.ENDPOINT.format(driver_id="DRV-001")
        response = authorized_client.post(url, json=_VALID_GUARANTOR_BODY)
        guarantor_id = response.json()["id"]
        assert authorized_client.guarantor_repo.is_linked_to_driver("DRV-001", guarantor_id)

    def test_create_guarantor_default_telephones(self, authorized_client):
        body = {k: v for k, v in _VALID_GUARANTOR_BODY.items() if k != "telephones"}
        url = self.ENDPOINT.format(driver_id="DRV-001")
        response = authorized_client.post(url, json=body)
        assert response.status_code == 201
        assert response.json()["telephones"] == []

    # -----------------------------------------------------------------
    # Validation errors
    # -----------------------------------------------------------------

    def test_create_guarantor_driver_not_found(self, authorized_client):
        url = self.ENDPOINT.format(driver_id="NO-EXISTE")
        response = authorized_client.post(url, json=_VALID_GUARANTOR_BODY)
        assert response.status_code == 404
        assert "was not found" in response.json()["detail"]

    def test_create_guarantor_missing_required_field(self, authorized_client):
        body = {k: v for k, v in _VALID_GUARANTOR_BODY.items() if k != "name"}
        url = self.ENDPOINT.format(driver_id="DRV-001")
        response = authorized_client.post(url, json=body)
        assert response.status_code == 422

    def test_create_guarantor_missing_address(self, authorized_client):
        body = {k: v for k, v in _VALID_GUARANTOR_BODY.items() if k != "addressFields"}
        url = self.ENDPOINT.format(driver_id="DRV-001")
        response = authorized_client.post(url, json=body)
        assert response.status_code == 422

    def test_create_guarantor_missing_relation(self, authorized_client):
        body = {k: v for k, v in _VALID_GUARANTOR_BODY.items() if k != "relation"}
        url = self.ENDPOINT.format(driver_id="DRV-001")
        response = authorized_client.post(url, json=body)
        assert response.status_code == 422

    def test_create_guarantor_limit_reached(self, authorized_client):
        url = self.ENDPOINT.format(driver_id="DRV-001")
        for _ in range(5):
            resp = authorized_client.post(url, json=_VALID_GUARANTOR_BODY)
            assert resp.status_code == 201

        response = authorized_client.post(url, json=_VALID_GUARANTOR_BODY)
        assert response.status_code == 409
        assert "already has 5 guarantors" in response.json()["detail"]

    # -----------------------------------------------------------------
    # RBAC
    # -----------------------------------------------------------------

    def test_create_guarantor_requires_auth(self, client):
        url = self.ENDPOINT.format(driver_id="DRV-001")
        response = client.post(url, json=_VALID_GUARANTOR_BODY)
        assert response.status_code == 401


@pytest.mark.usefixtures("authorized_client", "client")
class TestUpdateGuarantor:
    """Tests for PATCH /management/drivers/{driver_id}/guarantors/{guarantor_id}."""

    ENDPOINT = "/pegazzo/management/drivers/{driver_id}/guarantors/{guarantor_id}"

    def _create_linked_guarantor(self, authorized_client, driver_id="DRV-001"):
        create_url = f"/pegazzo/management/drivers/{driver_id}/guarantors"
        resp = authorized_client.post(create_url, json=_VALID_GUARANTOR_BODY)
        return resp.json()["id"]

    # -----------------------------------------------------------------
    # Success
    # -----------------------------------------------------------------

    def test_update_guarantor_partial(self, authorized_client):
        gid = self._create_linked_guarantor(authorized_client)
        url = self.ENDPOINT.format(driver_id="DRV-001", guarantor_id=gid)
        response = authorized_client.patch(url, json={"name": "Roberto"})
        assert response.status_code == 200
        assert response.json()["name"] == "Roberto"
        assert response.json()["surnames"] == "Ramírez Vega"

    def test_update_guarantor_address(self, authorized_client):
        gid = self._create_linked_guarantor(authorized_client)
        url = self.ENDPOINT.format(driver_id="DRV-001", guarantor_id=gid)
        response = authorized_client.patch(url, json={"addressFields": {**_ADDRESS_FIELDS, "street": "Av. Nueva"}})
        assert response.status_code == 200
        assert response.json()["address"] == "Av. Nueva 10, Col. Centro, C.P. 06000, Cuauhtémoc, CDMX"

    def test_update_guarantor_multiple_fields(self, authorized_client):
        gid = self._create_linked_guarantor(authorized_client)
        url = self.ENDPOINT.format(driver_id="DRV-001", guarantor_id=gid)
        response = authorized_client.patch(url, json={"name": "Pedro", "relation": "uncle"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Pedro"
        assert data["relation"] == "uncle"

    # -----------------------------------------------------------------
    # Errors
    # -----------------------------------------------------------------

    def test_update_guarantor_not_found(self, authorized_client):
        url = self.ENDPOINT.format(driver_id="DRV-001", guarantor_id=999)
        response = authorized_client.patch(url, json={"name": "Test"})
        assert response.status_code == 404
        assert "was not found" in response.json()["detail"]

    def test_update_guarantor_driver_not_found(self, authorized_client):
        url = self.ENDPOINT.format(driver_id="NO-EXISTE", guarantor_id=1)
        response = authorized_client.patch(url, json={"name": "Test"})
        assert response.status_code == 404
        assert "was not found" in response.json()["detail"]

    def test_update_guarantor_not_linked(self, authorized_client):
        url = self.ENDPOINT.format(driver_id="DRV-001", guarantor_id=1)
        response = authorized_client.patch(url, json={"name": "Test"})
        assert response.status_code == 404
        assert "not linked" in response.json()["detail"]

    # -----------------------------------------------------------------
    # RBAC
    # -----------------------------------------------------------------

    def test_update_guarantor_requires_auth(self, client):
        url = self.ENDPOINT.format(driver_id="DRV-001", guarantor_id=1)
        response = client.patch(url, json={"name": "Test"})
        assert response.status_code == 401


@pytest.mark.usefixtures("authorized_client", "client")
class TestDeleteGuarantor:
    """Tests for DELETE /management/drivers/{driver_id}/guarantors/{guarantor_id}."""

    ENDPOINT = "/pegazzo/management/drivers/{driver_id}/guarantors/{guarantor_id}"

    # -----------------------------------------------------------------
    # Success — orphan (hard delete)
    # -----------------------------------------------------------------

    def test_delete_guarantor_orphan(self, authorized_client):
        # Create guarantor linked to DRV-001
        create_url = "/pegazzo/management/drivers/DRV-001/guarantors"
        resp = authorized_client.post(create_url, json=_VALID_GUARANTOR_BODY)
        gid = resp.json()["id"]

        url = self.ENDPOINT.format(driver_id="DRV-001", guarantor_id=gid)
        response = authorized_client.delete(url)
        assert response.status_code == 200
        assert "removed" in response.json()["message"].lower()

        # Guarantor should be deleted (orphan)
        assert authorized_client.guarantor_repo.get_by_id(gid) is None

    def test_delete_guarantor_orphan_moves_documents_to_deleted(self, authorized_client):
        resp = authorized_client.post("/pegazzo/management/drivers/DRV-001/guarantors", json=_VALID_GUARANTOR_BODY)
        gid = resp.json()["id"]
        authorized_client.guarantor_repo.document_keys[gid] = ["guarantor/ine.pdf", "guarantor/address.pdf"]

        with patch("app.storage.r2.soft_delete_document") as mock_soft_delete:
            response = authorized_client.delete(self.ENDPOINT.format(driver_id="DRV-001", guarantor_id=gid))

        assert response.status_code == 200
        assert [c.args[0] for c in mock_soft_delete.call_args_list] == ["guarantor/ine.pdf", "guarantor/address.pdf"]

    def test_delete_guarantor_storage_failure_does_not_fail_request(self, authorized_client):
        resp = authorized_client.post("/pegazzo/management/drivers/DRV-001/guarantors", json=_VALID_GUARANTOR_BODY)
        gid = resp.json()["id"]
        authorized_client.guarantor_repo.document_keys[gid] = ["guarantor/ine.pdf"]

        with patch("app.storage.r2.soft_delete_document", side_effect=RuntimeError("R2 down")):
            response = authorized_client.delete(self.ENDPOINT.format(driver_id="DRV-001", guarantor_id=gid))

        assert response.status_code == 200
        assert authorized_client.guarantor_repo.get_by_id(gid) is None

    # -----------------------------------------------------------------
    # Success — shared (only unlink)
    # -----------------------------------------------------------------

    def test_delete_guarantor_shared(self, authorized_client):
        # Create guarantor linked to DRV-001
        create_url = "/pegazzo/management/drivers/DRV-001/guarantors"
        resp = authorized_client.post(create_url, json=_VALID_GUARANTOR_BODY)
        gid = resp.json()["id"]

        # Also link to DRV-002
        authorized_client.guarantor_repo.link_to_driver("DRV-002", gid)

        url = self.ENDPOINT.format(driver_id="DRV-001", guarantor_id=gid)
        with patch("app.storage.r2.soft_delete_document") as mock_soft_delete:
            response = authorized_client.delete(url)
        assert response.status_code == 200

        # Guarantor should still exist (linked to DRV-002)
        assert mock_soft_delete.call_count == 0
        assert authorized_client.guarantor_repo.get_by_id(gid) is not None
        assert not authorized_client.guarantor_repo.is_linked_to_driver("DRV-001", gid)
        assert authorized_client.guarantor_repo.is_linked_to_driver("DRV-002", gid)

    # -----------------------------------------------------------------
    # Errors
    # -----------------------------------------------------------------

    def test_delete_guarantor_driver_not_found(self, authorized_client):
        url = self.ENDPOINT.format(driver_id="NO-EXISTE", guarantor_id=1)
        response = authorized_client.delete(url)
        assert response.status_code == 404

    def test_delete_guarantor_not_found(self, authorized_client):
        url = self.ENDPOINT.format(driver_id="DRV-001", guarantor_id=999)
        response = authorized_client.delete(url)
        assert response.status_code == 404

    def test_delete_guarantor_not_linked(self, authorized_client):
        url = self.ENDPOINT.format(driver_id="DRV-001", guarantor_id=1)
        response = authorized_client.delete(url)
        assert response.status_code == 404
        assert "not linked" in response.json()["detail"]

    # -----------------------------------------------------------------
    # RBAC
    # -----------------------------------------------------------------

    def test_delete_guarantor_requires_auth(self, client):
        url = self.ENDPOINT.format(driver_id="DRV-001", guarantor_id=1)
        response = client.delete(url)
        assert response.status_code == 401
