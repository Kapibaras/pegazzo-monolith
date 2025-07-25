from app.models.users import Role, User


class UserRepositoryMock:
    """Mock implementation of the UserRepository for testing purposes."""

    def __init__(self):
        self.users = [
            User(
                username="testuser",
                name="Test",
                surnames="User",
                password="hashed_password",
                role_id=1,
            )
        ]
        self.users[0].role = Role(id=1, name="ADMIN")

    def create_user(self, user):
        user.role = Role(id=user.role_id, name="ADMIN")
        self.users.append(user)
        return user

    def get_by_username(self, username):
        return next((user for user in self.users if user.username == username), None)

    def get_all_users(self):
        return self.users
