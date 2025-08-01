from argon2 import PasswordHasher

from app.errors.user import (
    RoleNotFoundException,
    UsernameAlreadyExistsException,
    UserNotFoundException,
)
from app.models.users import User
from app.repositories.user import UserRepository
from app.schemas.user import RoleEnum, UserCreateSchema, UserSchema, UserUpdateSchema


class UserService:
    """User service class."""

    def __init__(self, repository: UserRepository):
        """Initialize the user service with a repository."""
        self.repository = repository

    def get_user(self, username: str):
        """Get a user by username."""

        user = self.repository.get_by_username(username)
        if not user:
            raise UserNotFoundException
        return user

    def get_all_users(self, role_name: RoleEnum = None):
        """Get all users, optionally filtered by role name."""

        if role_name:
            role = self.repository.get_role_by_name(role_name.value)
            if not role:
                raise RoleNotFoundException
            role_id = role.id
        else:
            role_id = None

        return self.repository.get_all_users(role_id=role_id)

    def create_user(self, data: UserCreateSchema) -> UserSchema:
        """Create a new user."""

        role = self.repository.get_role_by_name(data.role)

        if self.repository.get_by_username(data.username):
            raise UsernameAlreadyExistsException

        ph = PasswordHasher()
        hashed_password = ph.hash(data.password)

        user = User(username=data.username, name=data.name, surnames=data.surnames, password=hashed_password, role=role)

        return self.repository.create_user(user)

    def update_user(self, username: str, data: UserUpdateSchema) -> UserSchema:
        """Update a user by their username."""
        role = self.repository.get_role_by_name(data.role)
        user = self.repository.get_by_username(username)
        if not user:
            raise UserNotFoundException
        user.name = data.name
        user.surnames = data.surnames
        user.role = role
        self.repository.update_user(user)
        return user

    def delete_user(self, username: str):
        """Delete a user by their username."""
        user = self.repository.get_by_username(username)
        if not user:
            raise UserNotFoundException
        self.repository.delete_user(user)
