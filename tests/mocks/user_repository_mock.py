# from app.models.users import Role, User


# class UserRepositoryMock:
#     """Mock implementation of the UserRepository for testing purposes."""

#     def __init__(self):
#         self.users = [
#             User(
#                 username="testuser",
#                 name="Test",
#                 surnames="User",
#                 password="hashed_password",
#                 role_id=1,
#             )
#         ]
#         self.users[0].role = Role(id=1, name="ADMIN")

#     def create_user(self, user):
#         user.role = Role(id=user.role_id, name="ADMIN")
#         self.users.append(user)
#         return user

#     def get_by_username(self, username):
#         return next((user for user in self.users if user.username == username), None)

#     def get_all_users(self):
#         return self.users


from datetime import datetime

from app.errors.user import UserNotFoundException
from app.models.users import Role, User


class UserRepositoryMock:
    """Mock implementation of the UserRepository for testing purposes."""

    def __init__(self):
        self.roles = {
            "admin": Role(id=1, name="admin"),
            "user": Role(id=2, name="user"),
        }
        self.users = [
            User(
                username="testuser",
                name="Test",
                surnames="User",
                password="hashed_password",
                role_id=1,
                role=self.roles["admin"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]

    def get_role_by_name(self, role_name: str) -> Role | None:
        """Mocked method to get role by name."""
        return self.roles.get(role_name.lower())

    def get_by_username(self, username: str) -> User | None:
        """Mocked method to get a user by username."""
        return next((u for u in self.users if u.username == username), None)

    def get_all_users(self, role_id: int = None) -> list[User]:
        """Mocked method to return all users, optionally filtered by role_id."""
        if role_id is not None:
            return [u for u in self.users if u.role_id == role_id]
        return self.users

    def get_all_users_by_role(self, role_id: int) -> list[User]:
        """Alias for get_all_users filtered by role."""
        return self.get_all_users(role_id)

    def create_user(self, user: User) -> User:
        """Mocked method to simulate user creation."""
        user.created_at = datetime.now()
        user.updated_at = datetime.now()
        user.role = self.get_role_by_name(user.role.name) or self.roles["user"]
        self.users.append(user)
        return user

    def update_user(self, user: User) -> User:
        """Mocked method to simulate updating a user."""
        existing_user = self.get_by_username(user.username)
        if not existing_user:
            raise UserNotFoundException()

        existing_user.name = user.name
        existing_user.surnames = user.surnames
        existing_user.role = self.get_role_by_name(user.role.name)
        existing_user.role_id = existing_user.role.id
        existing_user.updated_at = datetime.now()
        return existing_user

    def delete_user(self, user: User):
        """Mocked method to simulate deleting a user."""
        if user not in self.users:
            raise UserNotFoundException()
        self.users = [u for u in self.users if u.username != user.username]
