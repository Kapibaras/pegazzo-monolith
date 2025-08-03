from unittest.mock import Mock

import pytest

from app.database.seeders import seeders
from app.models.users import Role


@pytest.fixture
def mock_db():
    """Fixture que simula una base de datos vacía.

    Simula que los roles aún no existen, por lo tanto serán agregados.
    """
    # Mock
    db = Mock()
    db.query.return_value = db
    db.filter_by.return_value = db
    db.first.return_value = None
    return db


@pytest.fixture
def existing_role_db():
    """Fixture que simula una base de datos con roles ya existentes.

    Simula que los roles existen y por lo tanto serán actualizados, no insertados.
    """
    # Mock
    db = Mock()
    db.query.return_value = db
    db.filter_by.side_effect = lambda id=None: db
    db.first.side_effect = lambda: Role(id=1, name="old_admin") if db.query.call_count == 1 else Role(id=2, name="old_user")
    return db


@pytest.mark.usefixtures("client")
class TestSeeders:
    """Clase de pruebas para la función seeders, que inserta o actualiza roles en la base de datos."""

    def test_seed_roles_insert_if_not_exists(self, mock_db):
        """Verifica que se agregan los roles cuando no existen previamente en la base de datos."""

        # Act
        seeders(mock_db)

        # Assert
        assert mock_db.add.call_count == 2
        mock_db.commit.assert_called_once()

    def test_seed_roles_update_if_exists(self, existing_role_db):
        """Verifica que se actualiza el nombre del rol cuando ya existe en la base de datos."""

        # Act
        seeders(existing_role_db)

        # Assert
        existing_role_db.add.assert_not_called()
        existing_role_db.commit.assert_called_once()
