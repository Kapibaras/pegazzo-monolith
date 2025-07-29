from typing import Optional

from argon2 import PasswordHasher

from app.errors.user import (
    InvalidRoleException,
    UsernameAlreadyExistsException,
    UsernameRequiredException,
    UserNotFoundException,
)
from app.models.users import User
from app.repositories.user import UserRepository
from app.schemas.user import ROLE_MAPPING, ActionSuccess, RoleEnum, UserCreateSchema, UserSchema, UserUpdateSchema


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository
        self.ph = PasswordHasher()

    def _get_role_id(self, role: str) -> int:
        try:
            role_enum = RoleEnum(role)
            return ROLE_MAPPING[role_enum]
        except (ValueError, KeyError):
            raise InvalidRoleException()

    def get_user(self, username: str):
        """Getting a user."""

        if not username:
            raise UsernameRequiredException()
        user = self.repository.get_by_username(username)
        if not user:
            raise UserNotFoundException()
        return UserSchema.from_orm(user)

    def get_all_users(self, role: Optional[RoleEnum] = None):
        """Getting all users."""
        if role:
            role_id = self._get_role_id(role)
            users = self.repository.get_all_users_by_role(role_id)
        else:
            users = self.repository.get_all_users()
        return [UserSchema.from_orm(user) for user in users]

    def create_user(self, data: UserCreateSchema) -> UserSchema:
        """Creating a user."""

        role_id = self._get_role_id(data.role)

        if self.repository.get_by_username(data.username):
            raise UsernameAlreadyExistsException()

        hashed_password = self.ph.hash(data.password)

        user = User(
            username=data.username,
            name=data.name,
            surnames=data.surnames,
            password=hashed_password,
            role_id=role_id,
        )

        created_user = self.repository.create_user(user)
        return UserSchema.from_orm(created_user)

    def update_user(self, username: str, data: UserUpdateSchema) -> UserSchema:
        """Updating a user."""
        role_id = self._get_role_id(data.role)
        user = self.repository.get_by_username(username)
        if not user:
            raise UserNotFoundException()
        user.name = data.name
        user.surnames = data.surnames
        user.role_id = role_id
        self.repository.update_user(user)
        return UserSchema.from_orm(user)

    def delete_user(self, username: str):
        """Deleting a user."""
        user = self.repository.get_by_username(username)
        if not user:
            raise UserNotFoundException()
        self.repository.delete_user(user)
        return ActionSuccess(message=f"User '{username}' was successfully deleted.", extra_data={"username": username})
