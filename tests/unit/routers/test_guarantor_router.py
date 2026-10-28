import pytest

_VALID_GUARANTOR_BODY = {
    "name": "Carlos",
    "surnames": "Ramírez Vega",
    "telephones": ["+525551234567"],
    "address": "Calle Nueva #10",
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
        assert data["address"] == "Calle Nueva #10"
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
        body = {k: v for k, v in _VALID_GUARANTOR_BODY.items() if k != "address"}
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
    """Tests for PATCH /management/guarantors/{guarantor_id}."""

    ENDPOINT = "/pegazzo/management/guarantors/{guarantor_id}"

    # -----------------------------------------------------------------
    # Success
    # -----------------------------------------------------------------

    def test_update_guarantor_partial(self, authorized_client):
        url = self.ENDPOINT.format(guarantor_id=1)
        response = authorized_client.patch(url, json={"name": "Roberto"})
        assert response.status_code == 200
        assert response.json()["name"] == "Roberto"
        assert response.json()["surnames"] == "García López"

    def test_update_guarantor_address(self, authorized_client):
        url = self.ENDPOINT.format(guarantor_id=1)
        response = authorized_client.patch(url, json={"address": "Av. Nueva #99"})
        assert response.status_code == 200
        assert response.json()["address"] == "Av. Nueva #99"

    def test_update_guarantor_multiple_fields(self, authorized_client):
        url = self.ENDPOINT.format(guarantor_id=1)
        response = authorized_client.patch(url, json={"name": "Pedro", "relation": "uncle"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Pedro"
        assert data["relation"] == "uncle"

    # -----------------------------------------------------------------
    # Errors
    # -----------------------------------------------------------------

    def test_update_guarantor_not_found(self, authorized_client):
        url = self.ENDPOINT.format(guarantor_id=999)
        response = authorized_client.patch(url, json={"name": "Test"})
        assert response.status_code == 404
        assert "was not found" in response.json()["detail"]

    # -----------------------------------------------------------------
    # RBAC
    # -----------------------------------------------------------------

    def test_update_guarantor_requires_auth(self, client):
        url = self.ENDPOINT.format(guarantor_id=1)
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
        response = authorized_client.delete(url)
        assert response.status_code == 200

        # Guarantor should still exist (linked to DRV-002)
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
        assert response.status_code == 400
        assert "not linked" in response.json()["detail"]

    # -----------------------------------------------------------------
    # RBAC
    # -----------------------------------------------------------------

    def test_delete_guarantor_requires_auth(self, client):
        url = self.ENDPOINT.format(driver_id="DRV-001", guarantor_id=1)
        response = client.delete(url)
        assert response.status_code == 401
