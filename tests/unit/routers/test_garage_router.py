from unittest.mock import patch

import pytest

_ADDRESS_FIELDS = {
    "street": "Av. Reforma",
    "exteriorNumber": "100",
    "interiorNumber": "4",
    "neighborhood": "Centro",
    "postalCode": "06000",
    "municipality": "Cuauhtémoc",
    "state": "CDMX",
}
_ADDRESS_TEXT = "Av. Reforma 100 Int. 4, Col. Centro, C.P. 06000, Cuauhtémoc, CDMX"
_BODY = {"addressFields": _ADDRESS_FIELDS}


@pytest.mark.usefixtures("authorized_client", "client")
class TestGarageRouter:
    """Tests for /management/drivers/{driver_id}/garages."""

    COLLECTION = "/pegazzo/management/drivers/{driver_id}/garages"
    ITEM = "/pegazzo/management/drivers/{driver_id}/garages/{garage_id}"

    def _create(self, client, driver_id="DRV-001"):
        response = client.post(self.COLLECTION.format(driver_id=driver_id), json=_BODY)
        assert response.status_code == 201
        return response.json()["id"]

    # -- create

    def test_create_garage(self, authorized_client):
        response = authorized_client.post(self.COLLECTION.format(driver_id="DRV-001"), json=_BODY)
        assert response.status_code == 201
        data = response.json()
        assert data["address"] == _ADDRESS_TEXT
        assert data["addressFields"] == _ADDRESS_FIELDS
        assert "id" in data
        assert "createdAt" in data

    def test_create_garage_stores_the_driver_id(self, authorized_client):
        garage_id = self._create(authorized_client)
        assert authorized_client.garage_repo.get_by_id(garage_id).driver_id == "DRV-001"

    def test_create_garage_driver_not_found(self, authorized_client):
        response = authorized_client.post(self.COLLECTION.format(driver_id="NOPE"), json=_BODY)
        assert response.status_code == 404
        assert "Driver with id" in response.json()["detail"]

    @pytest.mark.parametrize("field", ["street", "exteriorNumber", "neighborhood", "postalCode", "municipality", "state"])
    def test_create_garage_requires_every_address_field(self, authorized_client, field):
        fields = {k: v for k, v in _ADDRESS_FIELDS.items() if k != field}
        response = authorized_client.post(self.COLLECTION.format(driver_id="DRV-001"), json={"addressFields": fields})
        assert response.status_code == 422

    def test_create_garage_interior_number_is_optional(self, authorized_client):
        fields = {k: v for k, v in _ADDRESS_FIELDS.items() if k != "interiorNumber"}
        response = authorized_client.post(self.COLLECTION.format(driver_id="DRV-001"), json={"addressFields": fields})
        assert response.status_code == 201
        assert response.json()["address"] == "Av. Reforma 100, Col. Centro, C.P. 06000, Cuauhtémoc, CDMX"

    def test_create_garage_rejects_the_old_free_text_body(self, authorized_client):
        response = authorized_client.post(self.COLLECTION.format(driver_id="DRV-001"), json={"address": "Calle 1"})
        assert response.status_code == 422

    # -- update

    def test_update_garage(self, authorized_client):
        garage_id = self._create(authorized_client)
        body = {"addressFields": {**_ADDRESS_FIELDS, "street": "Insurgentes"}}
        response = authorized_client.patch(self.ITEM.format(driver_id="DRV-001", garage_id=garage_id), json=body)
        assert response.status_code == 200
        assert response.json()["address"].startswith("Insurgentes 100 Int. 4")

    def test_update_garage_of_another_driver_is_not_found(self, authorized_client):
        garage_id = self._create(authorized_client, "DRV-001")
        response = authorized_client.patch(self.ITEM.format(driver_id="DRV-002", garage_id=garage_id), json=_BODY)
        assert response.status_code == 404
        assert "Garage with id" in response.json()["detail"]

    def test_update_garage_not_found(self, authorized_client):
        response = authorized_client.patch(self.ITEM.format(driver_id="DRV-001", garage_id=999), json=_BODY)
        assert response.status_code == 404

    # -- delete

    def test_delete_garage(self, authorized_client):
        garage_id = self._create(authorized_client)
        response = authorized_client.delete(self.ITEM.format(driver_id="DRV-001", garage_id=garage_id))
        assert response.status_code == 200
        assert authorized_client.garage_repo.get_by_id(garage_id) is None

    def test_delete_garage_moves_the_document_files(self, authorized_client):
        garage_id = self._create(authorized_client)
        authorized_client.garage_repo.document_keys[garage_id] = ["garage/1/proof.pdf"]
        with patch("app.storage.r2.soft_delete_document") as soft_delete:
            response = authorized_client.delete(self.ITEM.format(driver_id="DRV-001", garage_id=garage_id))
        assert response.status_code == 200
        soft_delete.assert_called_once_with("garage/1/proof.pdf")

    def test_delete_garage_storage_failure_does_not_fail_the_request(self, authorized_client):
        garage_id = self._create(authorized_client)
        authorized_client.garage_repo.document_keys[garage_id] = ["garage/1/proof.pdf"]
        with patch("app.storage.r2.soft_delete_document", side_effect=RuntimeError("R2 down")):
            response = authorized_client.delete(self.ITEM.format(driver_id="DRV-001", garage_id=garage_id))
        assert response.status_code == 200

    def test_delete_garage_of_another_driver_is_not_found(self, authorized_client):
        garage_id = self._create(authorized_client, "DRV-001")
        response = authorized_client.delete(self.ITEM.format(driver_id="DRV-002", garage_id=garage_id))
        assert response.status_code == 404
        assert authorized_client.garage_repo.get_by_id(garage_id) is not None

    # -- RBAC

    def test_create_requires_auth(self, client):
        assert client.post(self.COLLECTION.format(driver_id="DRV-001"), json=_BODY).status_code == 401

    def test_create_employee_forbidden(self, employee_authorized_client):
        response = employee_authorized_client.post(self.COLLECTION.format(driver_id="DRV-001"), json=_BODY)
        assert response.status_code == 403

    def test_delete_employee_forbidden(self, employee_authorized_client):
        response = employee_authorized_client.delete(self.ITEM.format(driver_id="DRV-001", garage_id=1))
        assert response.status_code == 403
