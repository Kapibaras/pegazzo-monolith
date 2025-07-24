from app.models.users import User
from app.repositories.user import UserRepository


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def get_user(self, username: str):
        """Example method NOT FINAL for getting a user."""

        return self.repository.get_by_username(username)

    def get_all_users(self):
        """Example method NOT FINAL for getting all users."""
        return self.repository.get_all_users()

    def create_user(
        self, username: str, name: str, surnames: str, password: str, role_id: int
    ):
        """Example method NOT FINAL for creating a user."""

        user = User(
            username=username,
            name=name,
            surnames=surnames,
            password=password,
            role_id=role_id,
        )

        return self.repository.create_user(user)
