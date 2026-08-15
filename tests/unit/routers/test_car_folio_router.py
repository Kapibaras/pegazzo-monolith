from app.models.car_model import CarModel

BASE_PAYLOAD = {
    "associateId": 1,
    "legalOwnerIsPegazzo": False,
    "make": "Mazda",
    "model": "2",
    "transmission": "TA",
}


def _seed_car_model(client, make: str = "Mazda", model: str = "2", abbreviation: str = "MZ2"):
    cm = CarModel(id=1, make=make, model=model, abbreviation=abbreviation)
    client.car_model_repo.car_models.append(cm)


class TestCarFolioRouter:
    """Tests for POST /management/cars/folio."""

    # -------------------------------------------------------------------------
    # Auth
    # -------------------------------------------------------------------------

    def test_unauthenticated_returns_401(self, client):
        _seed_car_model(client)
        response = client.post("/pegazzo/management/cars/folio", json=BASE_PAYLOAD)
        assert response.status_code == 401

    def test_regular_associate_folio(self, authorized_client):
        _seed_car_model(authorized_client)
        response = authorized_client.post("/pegazzo/management/cars/folio", json=BASE_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert "folio" in data
        assert data["folio"] == "S-JP-MZ2(TA)-01"

    def test_legal_owner_is_pegazzo_prefix(self, authorized_client):
        _seed_car_model(authorized_client)
        payload = {**BASE_PAYLOAD, "legalOwnerIsPegazzo": True}
        response = authorized_client.post("/pegazzo/management/cars/folio", json=payload)
        assert response.status_code == 200
        assert response.json()["folio"].startswith("PG-")

    def test_us_owner_prefix(self, authorized_client):
        authorized_client.car_repo.us_associate_ids.add(1)
        _seed_car_model(authorized_client)
        response = authorized_client.post("/pegazzo/management/cars/folio", json=BASE_PAYLOAD)
        assert response.status_code == 200
        assert response.json()["folio"].startswith("US-")

    def test_response_contains_folio_key(self, authorized_client):
        _seed_car_model(authorized_client)
        response = authorized_client.post("/pegazzo/management/cars/folio", json=BASE_PAYLOAD)
        assert response.status_code == 200
        assert set(response.json().keys()) == {"folio"}

    def test_nonexistent_associate_returns_400(self, authorized_client):
        _seed_car_model(authorized_client)
        payload = {**BASE_PAYLOAD, "associateId": 9999}
        response = authorized_client.post("/pegazzo/management/cars/folio", json=payload)
        assert response.status_code == 400
        assert "9999" in response.json()["detail"]

    def test_car_model_not_in_catalog_returns_400(self, authorized_client):
        payload = {**BASE_PAYLOAD, "make": "Unknown", "model": "X"}
        response = authorized_client.post("/pegazzo/management/cars/folio", json=payload)
        assert response.status_code == 400
        assert "catalog" in response.json()["detail"].lower()

    def test_missing_required_field_returns_422(self, authorized_client):
        payload = {k: v for k, v in BASE_PAYLOAD.items() if k != "associateId"}
        response = authorized_client.post("/pegazzo/management/cars/folio", json=payload)
        assert response.status_code == 422
