from unittest.mock import Mock

import pytest

from app.database.seeders import seeders
from app.models.users import Role


@pytest.fixture
def mock_db():
    """Fixture that simulates an empty database.

    Simulates that the roles do not exist, so they will be added.
    """
    # Mock
    db = Mock()
    db.query.return_value = db
    db.filter_by.return_value = db
    db.first.return_value = None
    return db


@pytest.fixture
def existing_role_db():
    """Fixture that simulates a database with existing roles.

    Simulates that the roles exist and therefore will be updated, not inserted.
    """
    # Mock
    db = Mock()
    db.query.return_value = db
    db.filter_by.side_effect = lambda id=None: db
    db.first.side_effect = lambda: Role(id=1, name="old_owner") if db.query.call_count == 1 else Role(id=2, name="old_user")
    return db


@pytest.mark.usefixtures("client")
class TestSeeders:
    """Class of tests for the seeders function, which inserts or updates roles in the database."""

    def test_seed_roles_insert_if_not_exists(self, mock_db):
        """Verifies that roles are added when they do not exist previously in the database."""

        # Act
        seeders(mock_db)

        # Assert
        assert mock_db.add.call_count == 3
        mock_db.commit.assert_called_once()

    def test_seed_roles_update_if_exists(self, existing_role_db):
        """Verifies that the role name is updated when it already exists in the database."""

        # Act
        seeders(existing_role_db)

        # Assert
        existing_role_db.add.assert_not_called()
        existing_role_db.commit.assert_called_once()
