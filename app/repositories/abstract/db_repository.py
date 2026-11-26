from abc import ABC

from sqlalchemy.orm import Session


class DBRepository(ABC):
    """Abstract base class for database repositories.

    This class should be inherited by all repository classes that interact with the database.
    """

    def __init__(self, db_session: Session):
        """Initialize the repository with a database session."""
        self.db = db_session

    def commit(self) -> None:
        """Commit the session; for callers composing several non-committing writes in one transaction."""
        self.db.commit()

    def rollback(self) -> None:
        """Roll back the session; for callers composing several non-committing writes in one transaction."""
        self.db.rollback()
