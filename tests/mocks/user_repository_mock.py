from datetime import datetime, timezone

from app.auth import Role as RoleEnum
from app.errors.user import UserNotFoundException
from app.models.users import Role, User


class UserRepositoryMock:
    """Mock implementation of the UserRepository for testing purposes."""

    def __init__(self):
        """Initialize the mock repository with sample data."""
        self.roles = {
            "propietario": Role(id=1, name=RoleEnum.OWNER),
            "administrador": Role(id=2, name=RoleEnum.ADMIN),
            "empleado": Role(id=3, name=RoleEnum.EMPLOYEE),
        }
        self.users = [
            User(
                username="testuser",
                name="Test",
                surnames="User",
                password="hashed_password",
                role_id=1,
                role=self.roles["propietario"],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
        ]

    def get_role_by_name(self, role_name: str) -> Role | None:
        """Get role by name."""
        return self.roles.get(role_name)

    def get_by_username(self, username: str) -> User | None:
        """Get a user by username."""
        return next((u for u in self.users if u.username == username), None)

    def get_all_users(self, role_id: int | None = None) -> list[User]:
        """Return all users, optionally filtered by role_id."""
        if role_id is not None:
            return [u for u in self.users if u.role_id == role_id]
        return self.users

    def create_user(self, user: User) -> User:
        """Simulate user creation."""
        user.created_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        user.role = self.get_role_by_name(user.role.name) or self.roles["empleado"]
        self.users.append(user)
        return user

    def update_user(self, user: User) -> User:
        """Simulate updating a user."""
        existing_user = self.get_by_username(user.username)
        if not existing_user:
            raise UserNotFoundException

        existing_user.name = user.name
        existing_user.surnames = user.surnames
        existing_user.role = self.get_role_by_name(user.role.name)
        existing_user.role_id = existing_user.role.id
        existing_user.updated_at = datetime.now(timezone.utc)
        return existing_user

    def delete_user(self, user: User):
        """Simulate deleting a user."""
        if user not in self.users:
            raise UserNotFoundException
        self.users = [u for u in self.users if u.username != user.username]
