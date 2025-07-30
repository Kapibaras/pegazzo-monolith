from argon2 import PasswordHasher

from app.errors.user import (
    UsernameAlreadyExistsException,
    UserNotFoundException,
)
from app.models.users import User
from app.repositories.user import UserRepository
from app.schemas.user import ActionSuccess, RoleEnum, UserCreateSchema, UserSchema, UserUpdateSchema


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository
        self.ph = PasswordHasher()

    def get_user(self, username: str):
        """Getting a user."""

        user = self.repository.get_by_username(username)
        if not user:
            raise UserNotFoundException()
        return user

    def get_all_users(self, role_name: RoleEnum = None):
        if role_name:
            role = self.repository.get_role_by_name(role_name.value)
            role_id = role.id
        else:
            role_id = None

        users = self.repository.get_all_users(role_id=role_id)
        return users

    def create_user(self, data: UserCreateSchema) -> UserSchema:
        """Creating a user."""

        role = self.repository.get_role_by_name(data.role)

        if self.repository.get_by_username(data.username):
            raise UsernameAlreadyExistsException()

        hashed_password = self.ph.hash(data.password)

        user = User(username=data.username, name=data.name, surnames=data.surnames, password=hashed_password, role=role)

        created_user = self.repository.create_user(user)
        return created_user

    def update_user(self, username: str, data: UserUpdateSchema) -> UserSchema:
        """Updating a user."""
        role = self.repository.get_role_by_name(data.role)
        user = self.repository.get_by_username(username)
        if not user:
            raise UserNotFoundException()
        user.name = data.name
        user.surnames = data.surnames
        user.role = role
        self.repository.update_user(user)
        return user

    def delete_user(self, username: str):
        """Deleting a user."""
        user = self.repository.get_by_username(username)
        if not user:
            raise UserNotFoundException()
        self.repository.delete_user(user)
        return ActionSuccess(message=f"User '{username}' was successfully deleted.", extra_data={"username": username})
