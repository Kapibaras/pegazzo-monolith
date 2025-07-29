from app.models.users import User

from .abstract import DBRepository


class UserRepository(DBRepository):
    def get_by_username(self, username: str):
        """
        Retrieve a user by their username.

        Args:
            username (str): The username of the user to retrieve.
        """
        return self.db.query(User).filter(User.username == username).first()

    def get_all_users(self):
        """
        Retrieve all users from the database.
        """
        return self.db.query(User).all()

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
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        query = self.db.query(User).filter_by(username=user.username)
        query = self.with_selectinload(query, User.role)
        user_with_role = query.first()

        return user_with_role

    def update_user(self, user: User):
        """
        Update an existing user in the database.

        Args:
            user (User): The user object to update.
        """

        self.db.commit()
        self.db.refresh(user)
        query = self.db.query(User).filter_by(username=user.username)
        query = self.with_selectinload(query, User.role)
        user_with_role = query.first()

        return user_with_role

    def delete_user(self, user: User):
        """
        Delete an existing user from the database.

        Args:
            user (User): The user object to delete.
        """
        self.db.delete(user)
        self.db.commit()
