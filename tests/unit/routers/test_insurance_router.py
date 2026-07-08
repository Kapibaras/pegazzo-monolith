class TestInsuranceRouter:
    """Tests for /pegazzo/management/cars/insurance endpoints."""

    # --- POST ---

    def test_create_insurance_success(self, authorized_client):
        response = authorized_client.post(
            "/pegazzo/management/cars/insurance",
            json={"name": "Qualitas", "telephones": ["+521112223333"]},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Qualitas"
        assert data["telephones"] == ["+521112223333"]
        assert "id" in data

    def test_create_insurance_without_telephones(self, authorized_client):
        response = authorized_client.post(
            "/pegazzo/management/cars/insurance",
            json={"name": "HDI Seguros"},
        )
        assert response.status_code == 201
        assert response.json()["name"] == "HDI Seguros"

    def test_create_insurance_duplicate_name(self, authorized_client):
        response = authorized_client.post(
            "/pegazzo/management/cars/insurance",
            json={"name": "AXA Seguros"},
        )
        assert response.status_code == 400
        assert "AXA Seguros" in response.json()["detail"]

    def test_create_insurance_unauthenticated(self, client):
        response = client.post(
            "/pegazzo/management/cars/insurance",
            json={"name": "Nueva"},
        )
        assert response.status_code == 401

    def test_create_insurance_missing_name(self, authorized_client):
        response = authorized_client.post(
            "/pegazzo/management/cars/insurance",
            json={"telephones": ["+521234567890"]},
        )
        assert response.status_code == 422

    # --- GET ---

    def test_list_insurances(self, authorized_client):
        response = authorized_client.get("/pegazzo/management/cars/insurance")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_list_insurance_with_search(self, authorized_client):
        response = authorized_client.get("/pegazzo/management/cars/insurance?search=AXA")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "AXA Seguros"

    def test_list_insurances_search_no_match(self, authorized_client):
        response = authorized_client.get("/pegazzo/management/cars/insurance?search=INEXISTENTE")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_insurances_unauthenticated(self, client):
        response = client.get("/pegazzo/management/cars/insurance")
        assert response.status_code == 401

    # --- PATCH ---

    def test_update_insurance_name(self, authorized_client):
        response = authorized_client.patch(
            "/pegazzo/management/cars/insurance/1",
            json={"name": "AXA Seguros MX"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "AXA Seguros MX"

    def test_update_insurance_telephones(self, authorized_client):
        response = authorized_client.patch(
            "/pegazzo/management/cars/insurance/1",
            json={"telephones": ["+529991112222"]},
        )
        assert response.status_code == 200
        assert response.json()["telephones"] == ["+529991112222"]

    def test_update_insurance_not_found(self, authorized_client):
        response = authorized_client.patch(
            "/pegazzo/management/cars/insurance/9999",
            json={"name": "X"},
        )
        assert response.status_code == 404
        assert "9999" in response.json()["detail"]

    def test_update_insurance_duplicate_name(self, authorized_client):
        response = authorized_client.patch(
            "/pegazzo/management/cars/insurance/1",
            json={"name": "GNP Seguros"},
        )
        assert response.status_code == 400
        assert "GNP Seguros" in response.json()["detail"]

    def test_update_insurance_unauthenticated(self, client):
        response = client.patch("/pegazzo/management/cars/insurance/1", json={"name": "X"})
        assert response.status_code == 401

    # --- DELETE ---

    def test_delete_insurance_success(self, authorized_client):
        response = authorized_client.delete("/pegazzo/management/cars/insurance/2")
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

    def test_delete_insurance_not_found(self, authorized_client):
        response = authorized_client.delete("/pegazzo/management/cars/insurance/9999")
        assert response.status_code == 404

    def test_delete_insurance_in_use(self, authorized_client):
        authorized_client.insurance_repo.cars_referencing.add(1)
        response = authorized_client.delete("/pegazzo/management/cars/insurance/1")
        assert response.status_code == 400
        assert "cannot be deleted" in response.json()["detail"]

    def test_delete_insurance_unauthenticated(self, client):
        response = client.delete("/pegazzo/management/cars/insurance/1")
        assert response.status_code == 401
