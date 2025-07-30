from datetime import datetime, timezone

from app.models.users import User
from app.schemas.user import RoleEnum


class RoleMock:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name


class UserRepositoryMock:
    """Mock implementation of the UserRepository for testing purposes."""

    def __init__(self):
        self.roles = {
            1: RoleMock(1, "admin"),
            2: RoleMock(2, "user"),
        }

        user = User(
            username="testuser",
            name="Test",
            surnames="User",
            password="hashed_password",
            role_id=1,
        )
        user.role = self.roles[user.role_id]
        user.created_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)

        self.users = [user]
        self._deleted_users = []

    def get_role_by_name(self, role_name: str) -> RoleMock:
        for role in self.roles.values():
            if role.name == role_name:
                return role
        raise Exception("Role not found")

    def get_by_username(self, username: str):
        return next((u for u in self.users if u.username == username), None)

    def get_all_users(self, role_id: int = None):
        if role_id is not None:
            return [u for u in self.users if u.role_id == role_id]
        return self.users

    def get_all_users_by_role(self, role_id: int):
        return [u for u in self.users if u.role_id == role_id]

    def create_user(self, user: User):
        if self.get_by_username(user.username):
            raise Exception("User already exists")
        user.role = self.roles.get(user.role_id, RoleEnum.user)
        user.created_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        self.users.append(user)
        return user

    def update_user(self, user: User):
        existing = self.get_by_username(user.username)
        if not existing:
            raise Exception("User not found")
        existing.name = user.name
        existing.surnames = user.surnames
        existing.password = user.password
        existing.role_id = user.role_id
        existing.role = self.roles.get(user.role_id, RoleEnum.user)
        existing.updated_at = datetime.utcnow()
        return existing

    def delete_user(self, user: User):
        if user not in self.users:
            raise Exception("User not found")
        self._deleted_users.append(user)
        pass
