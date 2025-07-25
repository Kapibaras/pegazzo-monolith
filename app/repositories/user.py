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

    def create_user(self, user: User):
        """
        Create a new user in the database.

        Args:
            user (User): The user object to create.
        """
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
