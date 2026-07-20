BASE_URL = "/pegazzo/management/cars/associate"


class TestAssociateRouter:
    """Associate Router Testing."""

    def test_create_associate_success(self, authorized_client):
        response = authorized_client.post(
            BASE_URL,
            json={"name": "Carlos", "surnames": "Gomez Ruiz", "telephones": ["55-1234-5678"]},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Carlos"
        assert data["surnames"] == "Gomez Ruiz"
        assert data["telephones"] == ["55-1234-5678"]
        assert "id" in data

    def test_create_associate_without_telephones(self, authorized_client):
        response = authorized_client.post(
            BASE_URL,
            json={"name": "Sofia", "surnames": "Lopez Torres"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Sofia"
        assert data["telephones"] == []

    def test_create_associate_missing_name(self, authorized_client):
        response = authorized_client.post(
            BASE_URL,
            json={"surnames": "Ramirez"},
        )
        assert response.status_code == 422

    def test_create_associate_missing_surnames(self, authorized_client):
        response = authorized_client.post(
            BASE_URL,
            json={"name": "Pedro"},
        )
        assert response.status_code == 422

    def test_create_associate_unauthenticated(self, client):
        response = client.post(
            BASE_URL,
            json={"name": "Ana", "surnames": "Martinez"},
        )
        assert response.status_code == 401

    def test_list_associates_success(self, authorized_client):
        response = authorized_client.get(BASE_URL)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_list_associates_search(self, authorized_client):
        response = authorized_client.get(BASE_URL, params={"search": "Juan"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Juan"

    def test_list_associates_search_by_surnames(self, authorized_client):
        response = authorized_client.get(BASE_URL, params={"search": "Torres"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["surnames"] == "Torres Perez"

    def test_list_associates_search_no_match(self, authorized_client):
        response = authorized_client.get(BASE_URL, params={"search": "Nonexistent"})
        assert response.status_code == 200
        assert response.json() == []

    def test_list_associates_unauthenticated(self, client):
        response = client.get(BASE_URL)
        assert response.status_code == 401

    def test_update_associate_name(self, authorized_client):
        response = authorized_client.patch(f"{BASE_URL}/1", json={"name": "Juan Carlos"})
        assert response.status_code == 200
        assert response.json()["name"] == "Juan Carlos"

    def test_update_associate_telephones(self, authorized_client):
        response = authorized_client.patch(f"{BASE_URL}/1", json={"telephones": ["55-9999-0000"]})
        assert response.status_code == 200
        assert response.json()["telephones"] == ["55-9999-0000"]

    def test_update_associate_not_found(self, authorized_client):
        response = authorized_client.patch(f"{BASE_URL}/9999", json={"name": "Ghost"})
        assert response.status_code == 404
        assert "9999" in response.json()["detail"]

    def test_update_associate_unauthenticated(self, client):
        response = client.patch(f"{BASE_URL}/1", json={"name": "Ghost"})
        assert response.status_code == 401

    def test_delete_associate_success(self, authorized_client):
        response = authorized_client.delete(f"{BASE_URL}/1")
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

    def test_delete_associate_in_use(self, authorized_client):
        authorized_client.associate_repo.cars_linked.add(1)
        response = authorized_client.delete(f"{BASE_URL}/1")
        assert response.status_code == 400
        assert "1" in response.json()["detail"]

    def test_delete_associate_not_found(self, authorized_client):
        response = authorized_client.delete(f"{BASE_URL}/9999")
        assert response.status_code == 404
        assert "9999" in response.json()["detail"]

    def test_delete_associate_unauthenticated(self, client):
        response = client.delete(f"{BASE_URL}/1")
        assert response.status_code == 401
