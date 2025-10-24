import pytest

from app.schemas.user import ActionSuccess, UserSchema


@pytest.mark.usefixtures("authorized_client", "client")
class TestUserRouter:
    """Tests for the internal UserRouter endpoints."""

    def test_get_all_users(self, authorized_client):
        """Test getting all users."""
        response = authorized_client.get("/pegazzo/internal/user")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all(UserSchema.model_validate(user) for user in data)

    def test_get_all_users_with_role_filter(self, authorized_client):
        """Test getting all users with role filter."""
        role = "propietario"
        response = authorized_client.get(f"/pegazzo/internal/user?role={role}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all(UserSchema.model_validate(user) for user in data)

    def test_create_user(self, authorized_client):
        """Test creating a user."""
        user_data = {
            "username": "newuser",
            "name": "Test",
            "surnames": "User",
            "password": "password123",
            "role": "administrador",
        }
        response = authorized_client.post("/pegazzo/internal/user", json=user_data)
        assert response.status_code == 201
        assert UserSchema.model_validate(response.json())

    def test_get_user(self, authorized_client):
        """Test getting a user by username."""
        username = "testuser"
        response = authorized_client.get(f"/pegazzo/internal/user/{username}")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == username
        assert UserSchema.model_validate(data)

    def test_delete_user(self, authorized_client):
        """Test deleting a user."""
        username = "testuser"
        response = authorized_client.delete(f"/pegazzo/internal/user/{username}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert ActionSuccess.model_validate(data)

    def test_update_user_name(self, authorized_client):
        """Test updating a user name."""
        username = "testuser"
        update_data = {"name": "Updated", "surnames": "User"}
        response = authorized_client.patch(
            f"/pegazzo/internal/user/{username}/name",
            json=update_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert ActionSuccess.model_validate(data)

    def test_update_user_role(self, authorized_client):
        """Test updating a user role."""
        username = "testuser"
        update_data = {"role": "propietario"}
        response = authorized_client.patch(
            f"/pegazzo/internal/user/{username}/role",
            json=update_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert ActionSuccess.model_validate(data)

    def test_update_user_password(self, authorized_client):
        """Test updating a user password."""
        username = "testuser"
        update_data = {"password": "newpassword123"}
        response = authorized_client.patch(
            f"/pegazzo/internal/user/{username}/password",
            json=update_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert ActionSuccess.model_validate(data)

    @pytest.mark.parametrize(
        ("method", "endpoint"),
        [
            ("get", "/pegazzo/internal/user"),
            ("post", "/pegazzo/internal/user"),
            ("get", "/pegazzo/internal/user/testuser"),
            ("patch", "/pegazzo/internal/user/testuser/name"),
            ("patch", "/pegazzo/internal/user/testuser/password"),
            ("patch", "/pegazzo/internal/user/testuser/role"),
            ("delete", "/pegazzo/internal/user/testuser"),
        ],
    )
    def test_protected_routes_fail_without_auth(self, method, endpoint, client):
        """Test that protected routes fail without proper role."""
        request_func = getattr(client, method)
        json_data = (
            {
                "username": "baduser",
                "name": "Fake",
                "surnames": "User",
                "password": "fake123",
                "role": "viewer",
            }
            if method in ("post", "patch")
            else None
        )

        response = request_func(endpoint, json=json_data) if json_data else request_func(endpoint)
        assert response.status_code == 401
