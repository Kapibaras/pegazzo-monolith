import pytest

from app.schemas.user import RoleEnum, UserSchema


@pytest.mark.usefixtures("client")
class TestUserRouter:
    def test_get_all_users(self):
        response = self.client.get("/pegazzo/internal/user")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        validated_users = [UserSchema.parse_obj(user) for user in data]
        assert all(isinstance(u, UserSchema) for u in validated_users)

    def test_get_all_users_filter_role(self):
        response = self.client.get("/pegazzo/internal/user?role=user")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for user in data:
            UserSchema.parse_obj(user)
        assert all(user.get("role") == RoleEnum.user.value for user in data)

    def test_create_user(self):
        user_data = {
            "username": "newuser",
            "name": "Test",
            "surnames": "User",
            "password": "password123",
            "role": "user",
        }
        response = self.client.post("/pegazzo/internal/user", json=user_data)
        assert response.status_code == 201
        data = response.json()
        user = UserSchema.parse_obj(data)
        assert user.username == user_data["username"]

    def test_get_user(self):
        username = "testuser"
        response = self.client.get(f"/pegazzo/internal/user/{username}")
        assert response.status_code == 200
        data = response.json()
        user = UserSchema.parse_obj(data)
        assert user.username == username

    def test_update_user(self):
        username = "testuser"
        update_data = {
            "name": "Updated",
            "surnames": "User",
            "role": "admin",
        }
        response = self.client.put(f"/pegazzo/internal/user/{username}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["role"] == update_data["role"]

    def test_delete_user(self):
        username = "testuser"
        response = self.client.delete(f"/pegazzo/internal/user/{username}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert isinstance(data["message"], str)
