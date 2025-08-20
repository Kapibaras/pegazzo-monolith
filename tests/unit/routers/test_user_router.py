import pytest

from app.schemas.user import ActionSuccess, UserSchema


@pytest.mark.usefixtures("authorized_client", "client")
class TestUserRouter:
    """Tests for the internal UserRouter endpoints."""

    def test_get_all_users(self, authorized_client):
        """Test getting all users."""

        # Act
        response = authorized_client.get("/pegazzo/internal/user")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all(UserSchema.validate(user) for user in data)

    def test_get_all_users_with_role_filter(self, authorized_client):
        """Test getting all users with role filter."""
        # Arrange
        role = "propietario"

        # Act
        response = authorized_client.get(f"/pegazzo/internal/user?role={role}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all(UserSchema.validate(user) for user in data)

    def test_create_user(self, authorized_client):
        """Test creating a user."""
        # Arrange
        user_data = {
            "username": "newuser",
            "name": "Test",
            "surnames": "User",
            "password": "password123",
            "role": "administrador",
        }

        # Act
        response = authorized_client.post("/pegazzo/internal/user", json=user_data)

        # Assert
        assert response.status_code == 201
        assert UserSchema.validate(response.json())

    def test_get_user(self, authorized_client):
        """Test getting a user by username."""
        # Arrange
        username = "testuser"

        # Act
        response = authorized_client.get(f"/pegazzo/internal/user/{username}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == username
        assert UserSchema.validate(data)

    def test_update_user(self, authorized_client):
        """Test updating a user."""
        # Arrange
        username = "testuser"
        update_data = {
            "name": "Updated",
            "surnames": "User",
            "role": "propietario",
        }

        # Act
        response = authorized_client.put(
            f"/pegazzo/internal/user/{username}",
            json=update_data,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["username"] == username
        assert UserSchema.validate(data)

    def test_delete_user(self, authorized_client):
        """Test deleting a user."""
        # Arrange
        username = "testuser"

        # Act
        response = authorized_client.delete(f"/pegazzo/internal/user/{username}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data == {"message": f"User '{username}' was successfully deleted.", "extra_data": None}
        assert ActionSuccess.validate(data)

    @pytest.mark.parametrize(
        ("method", "endpoint"),
        [
            ("get", "/pegazzo/internal/user"),
            ("post", "/pegazzo/internal/user"),
            ("get", "/pegazzo/internal/user/testuser"),
            ("put", "/pegazzo/internal/user/testuser"),
            ("delete", "/pegazzo/internal/user/testuser"),
        ],
    )
    def test_protected_routes_fail_without_auth(self, method, endpoint, client):
        """Test that protected routes fail without proper role."""

        request_func = getattr(client, method)
        if method in ("post", "put"):
            json_data = {
                "username": "baduser",
                "name": "Fake",
                "surnames": "User",
                "password": "fake123",
                "role": "viewer",
            }
            response = request_func(endpoint, json=json_data)
        else:
            response = request_func(endpoint)

        assert response.status_code == 401
