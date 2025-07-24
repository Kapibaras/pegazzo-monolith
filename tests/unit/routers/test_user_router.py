import pytest

from app.schemas.user import UserSchema


@pytest.mark.usefixtures("client")
class TestUserRouter:
    """Base class for UserRouter tests."""

    def test_get_all_users(self):
        """Test getting all users."""
        response = self.client.get("/user/all")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all(UserSchema.validate(user) for user in data)

    def test_create_user(self):
        """Test creating a user."""
        user_data = {
            "username": "testuser",
            "name": "Test",
            "surnames": "User",
            "password": "password123",
            "roleId": 1,
        }
        response = self.client.post("/user", json=user_data)
        assert response.status_code == 200
        assert UserSchema.validate(response.json())

    def test_get_user(self):
        """Test getting a user by username."""
        username = "testuser"
        response = self.client.get(f"/user/{username}")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == username
        assert UserSchema.validate(data)
