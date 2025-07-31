import pytest

from app.schemas.user import ActionSuccess, UserSchema


@pytest.mark.usefixtures("client")
class TestUserRouter:
    """Tests for the internal UserRouter endpoints."""

    def test_get_all_users(self):
        """Test getting all users."""
        # Act
        response = self.client.get("/pegazzo/internal/user")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all(UserSchema.validate(user) for user in data)

    def test_get_all_users_with_role_filter(self):
        """Test getting all users with role filter."""
        # Arrange
        role = "admin"

        # Act
        response = self.client.get(f"/pegazzo/internal/user?role={role}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all(UserSchema.validate(user) for user in data)

    def test_create_user(self):
        """Test creating a user."""
        # Arrange
        user_data = {
            "username": "newuser",
            "name": "Test",
            "surnames": "User",
            "password": "password123",
            "role": "admin",
        }

        # Act
        response = self.client.post("/pegazzo/internal/user", json=user_data)

        # Assert
        assert response.status_code == 201
        assert UserSchema.validate(response.json())

    def test_get_user(self):
        """Test getting a user by username."""
        # Arrange
        username = "testuser"

        # Act
        response = self.client.get(f"/pegazzo/internal/user/{username}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == username
        assert UserSchema.validate(data)

    def test_update_user(self):
        """Test updating a user."""
        # Arrange
        username = "testuser"
        update_data = {
            "name": "Updated",
            "surnames": "User",
            "role": "admin",
        }

        # Act
        response = self.client.put(f"/pegazzo/internal/user/{username}", json=update_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["username"] == username
        assert UserSchema.validate(data)

    def test_delete_user(self):
        """Test deleting a user."""
        # Arrange
        username = "testuser"

        # Act
        response = self.client.delete(f"/pegazzo/internal/user/{username}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data == {"message": f"User '{username}' was successfully deleted.", "extra_data": None}
        assert ActionSuccess.validate(data)
