from abc import ABC

from sqlalchemy.orm import Session


class DBRepository(ABC):
    """
    Abstract base class for database repositories.
    This class should be inherited by all repository classes that interact with the database.
    """

    def __init__(self, db_session: Session):
        """
        Initialize the repository with a database session.
        """
        self.db = db_session
