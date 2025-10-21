from app.auth import Role
from app.errors.user import (
    ForbiddenRoleException,
    RoleNotFoundException,
    UsernameAlreadyExistsException,
    UserNotFoundException,
)
from app.models.users import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreateSchema, UserSchema, UserUpdatePasswordSchema, UserUpdateSchema
from app.utils.auth import AuthUtils


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

    def get_all_users(self, role_name: Role = None):
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

        if not role:
            raise RoleNotFoundException

        if role.name == Role.OWNER.value:
            raise ForbiddenRoleException

        if self.repository.get_by_username(data.username):
            raise UsernameAlreadyExistsException
        hashed_password = AuthUtils.hash_password(data.password)
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

    def update_user_password(self, username: str, data: UserUpdatePasswordSchema) -> UserSchema:
        """Update a user's password without requiring the old one."""
        user = self.repository.get_by_username(username)
        if not user:
            raise UserNotFoundException

        user.password = AuthUtils.hash_password(data.new_password)
        self.repository.update_user(user)
        return user
