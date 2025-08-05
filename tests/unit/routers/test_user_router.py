import pytest
from fastapi_jwt_auth import AuthJWT

from app.schemas.user import ActionSuccess, UserSchema
from app.utils.auth import AuthUtils


@pytest.mark.usefixtures("client")
class TestUserRouter:
    """Tests for the internal UserRouter endpoints."""

    def test_get_all_users(self):
        """Test getting all users."""
        # Arrange
        authorize = AuthJWT()
        access_token, _ = AuthUtils.create_access_token("adminuser", "admin", authorize)

        # Act
        response = self.client.get("/pegazzo/internal/user", cookies={"access_token_cookie": access_token})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all(UserSchema.validate(user) for user in data)

    def test_get_all_users_with_role_filter(self):
        """Test getting all users with role filter."""
        # Arrange
        role = "admin"
        authorize = AuthJWT()
        access_token, _ = AuthUtils.create_access_token("adminuser", "admin", authorize)

        # Act
        response = self.client.get(f"/pegazzo/internal/user?role={role}", cookies={"access_token_cookie": access_token})

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
        authorize = AuthJWT()
        access_token, _ = AuthUtils.create_access_token("adminuser", "admin", authorize)

        # Act
        response = self.client.post("/pegazzo/internal/user", json=user_data, cookies={"access_token_cookie": access_token})

        # Assert
        assert response.status_code == 201
        assert UserSchema.validate(response.json())

    def test_get_user(self):
        """Test getting a user by username."""
        # Arrange
        username = "testuser"
        authorize = AuthJWT()
        access_token, _ = AuthUtils.create_access_token("adminuser", "admin", authorize)

        # Act
        response = self.client.get(f"/pegazzo/internal/user/{username}", cookies={"access_token_cookie": access_token})

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
        authorize = AuthJWT()
        access_token, _ = AuthUtils.create_access_token("adminuser", "admin", authorize)

        # Act
        response = self.client.put(
            f"/pegazzo/internal/user/{username}", json=update_data, cookies={"access_token_cookie": access_token}
        )

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
        authorize = AuthJWT()
        access_token, _ = AuthUtils.create_access_token("adminuser", "admin", authorize)

        # Act
        response = self.client.delete(f"/pegazzo/internal/user/{username}", cookies={"access_token_cookie": access_token})

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
    def test_protected_routes_fail_without_auth(self, method, endpoint):
        """Test that protected routes fail without proper role."""
        client = getattr(self, "client_no_auth", self.client)

        request_func = getattr(client, method)
        if method in ("post", "put"):
            json = {
                "username": "baduser",
                "name": "Fake",
                "surnames": "User",
                "password": "fake123",
                "role": "viewer",
            }
            response = request_func(endpoint, json=json)
        else:
            response = request_func(endpoint)

        assert response.status_code == 401
