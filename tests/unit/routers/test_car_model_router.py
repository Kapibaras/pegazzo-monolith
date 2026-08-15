from app.models.car_model import CarModel

BASE_PAYLOAD = {"make": "Mazda", "model": "2", "abbreviation": "MZ2"}


def _seed(client, make="Mazda", model="2", abbreviation="MZ2") -> CarModel:
    cm = CarModel(make=make, model=model, abbreviation=abbreviation)
    client.car_model_repo.create(cm)
    return cm


class TestCarModelRouter:
    """Tests for GET/POST/DELETE /management/cars/models."""

    # -------------------------------------------------------------------------
    # GET /management/cars/models
    # -------------------------------------------------------------------------

    def test_list_empty(self, authorized_client):
        response = authorized_client.get("/pegazzo/management/cars/models")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_grouped_by_make(self, authorized_client):
        _seed(authorized_client, "Mazda", "2", "MZ2")
        _seed(authorized_client, "Mazda", "3", "MZ3")
        _seed(authorized_client, "Nissan", "Versa", "VR")

        response = authorized_client.get("/pegazzo/management/cars/models")
        assert response.status_code == 200
        data = response.json()
        makes = [g["make"] for g in data]
        assert makes == sorted(makes)
        mazda = next(g for g in data if g["make"] == "Mazda")
        assert len(mazda["models"]) == 2

    def test_list_unauthenticated(self, client):
        response = client.get("/pegazzo/management/cars/models")
        assert response.status_code == 401

    # -------------------------------------------------------------------------
    # POST /management/cars/models
    # -------------------------------------------------------------------------

    def test_create_success(self, authorized_client):
        response = authorized_client.post("/pegazzo/management/cars/models", json=BASE_PAYLOAD)
        assert response.status_code == 201
        data = response.json()
        assert data["make"] == "Mazda"
        assert data["model"] == "2"
        assert data["abbreviation"] == "MZ2"
        assert "id" in data

    def test_create_duplicate_returns_400(self, authorized_client):
        authorized_client.post("/pegazzo/management/cars/models", json=BASE_PAYLOAD)
        response = authorized_client.post("/pegazzo/management/cars/models", json=BASE_PAYLOAD)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_create_unauthenticated(self, client):
        response = client.post("/pegazzo/management/cars/models", json=BASE_PAYLOAD)
        assert response.status_code == 401

    def test_create_missing_field_returns_422(self, authorized_client):
        payload = {"make": "Mazda", "model": "2"}
        response = authorized_client.post("/pegazzo/management/cars/models", json=payload)
        assert response.status_code == 422

    # -------------------------------------------------------------------------
    # DELETE /management/cars/models/{id}
    # -------------------------------------------------------------------------

    def test_delete_success(self, authorized_client):
        cm = _seed(authorized_client)
        response = authorized_client.delete(f"/pegazzo/management/cars/models/{cm.id}")
        assert response.status_code == 204
        assert authorized_client.car_model_repo.get_by_id(cm.id) is None

    def test_delete_not_found_returns_404(self, authorized_client):
        response = authorized_client.delete("/pegazzo/management/cars/models/9999")
        assert response.status_code == 404

    def test_delete_unauthenticated(self, client):
        response = client.delete("/pegazzo/management/cars/models/1")
        assert response.status_code == 401
