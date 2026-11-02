from unittest.mock import MagicMock, call

import pytest

from app.errors.database import DBOperationError
from app.models.driver import Driver
from app.repositories.driver import DriverRepository


@pytest.fixture
def driver_repository_test_setup(request):
    """Set up DriverRepository with a mocked session and no linked rows."""
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchall.return_value = []
    request.cls.db = mock_db
    request.cls.repository = DriverRepository(mock_db)
    request.cls.driver = Driver(id="DRV-003")


@pytest.mark.usefixtures("driver_repository_test_setup")
class TestCascadeDeleteDriver:
    """Transaction handling of cascade_delete_driver."""

    def test_driver_is_expired_before_delete(self):
        keys = self.repository.cascade_delete_driver(self.driver)

        assert keys == []
        calls = self.db.method_calls
        assert calls.index(call.expire(self.driver)) < calls.index(call.delete(self.driver))
        self.db.commit.assert_called_once()

    def test_failure_rolls_back(self):
        self.db.commit.side_effect = RuntimeError("boom")

        with pytest.raises(DBOperationError):
            self.repository.cascade_delete_driver(self.driver)

        self.db.rollback.assert_called_once()
