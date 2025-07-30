from app.errors.database import DBOperationError
from app.models.users import Role, User
from app.utils.logging_config import logger

from .abstract import DBRepository


class UserRepository(DBRepository):
    def get_role_by_name(self, role_name: str) -> Role:
        return self.db.query(Role).filter_by(name=role_name).first()

    def get_by_username(self, username: str):
        """
        Retrieve a user by their username.

        Args:
            username (str): The username of the user to retrieve.
        """
        return self.db.query(User).filter(User.username == username).first()

    def get_all_users(self, role_id: int = None):
        query = self.db.query(User)
        if role_id is not None:
            query = query.filter(User.role_id == role_id)
        return query.all()

    def get_all_users_by_role(self, role_id: int):
        """
        Retrieve all users from the database.
        """
        return self.db.query(User).filter(User.role_id == role_id).all()

    def create_user(self, user: User):
        """
        Create a new user in the database.

        Args:
            user (User): The user object to create.
        """
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        except Exception as ex:
            self.db.rollback()
            logger.error(f"Error creating user {user.username} due to: {ex}")
            raise DBOperationError("Error creating user in the database")

        return self.get_by_username(user.username)

    def update_user(self, user: User):
        """
        Update an existing user in the database.

        Args:
            user (User): The user object to update.
        """
        try:
            self.db.commit()
            self.db.refresh(user)
        except Exception as ex:
            self.db.rollback()
            logger.error(f"Error updating user {user.username} due to: {ex}")
            raise DBOperationError("Error updating user in the database")

        return self.get_by_username(user.username)

    def delete_user(self, user: User):
        """
        Delete an existing user from the database.

        Args:
            user (User): The user object to delete.
        """
        try:
            self.db.delete(user)
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error(f"Error deleting user {user.username} due to: {ex}")
            raise DBOperationError("Error deleting user in the database")
