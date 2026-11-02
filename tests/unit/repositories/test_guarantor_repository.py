from unittest.mock import MagicMock

import pytest

from app.errors.database import DBOperationError
from app.models.document import Document
from app.models.driver import Driver, Guarantor
from app.repositories.guarantor import GuarantorRepository


def _count_query(value: int) -> MagicMock:
    query = MagicMock()
    query.select_from.return_value.filter.return_value.scalar.return_value = value
    return query


def _documents_query(documents: list[Document]) -> MagicMock:
    query = MagicMock()
    query.join.return_value.filter.return_value.all.return_value = documents
    return query


@pytest.fixture
def guarantor_repository_test_setup(request):
    """Set up GuarantorRepository with a mocked session."""
    mock_db = MagicMock()
    request.cls.db = mock_db
    request.cls.repository = GuarantorRepository(mock_db)
    request.cls.guarantor = Guarantor(id=7)


@pytest.mark.usefixtures("guarantor_repository_test_setup")
class TestCountGuarantorsForDriver:
    """Locking strategy of count_guarantors_for_driver."""

    def test_lock_is_taken_on_the_driver_row_not_the_aggregate(self):
        driver_query, count_query = MagicMock(), _count_query(2)
        self.db.query.side_effect = [driver_query, count_query]

        assert self.repository.count_guarantors_for_driver("DRV-001", lock=True) == 2

        assert self.db.query.call_args_list[0].args == (Driver,)
        driver_query.filter.return_value.with_for_update.return_value.first.assert_called_once()
        count_query.select_from.return_value.filter.return_value.with_for_update.assert_not_called()

    def test_without_lock_only_counts(self):
        self.db.query.side_effect = [_count_query(1)]

        assert self.repository.count_guarantors_for_driver("DRV-001") == 1
        assert self.db.query.call_count == 1


@pytest.mark.usefixtures("guarantor_repository_test_setup")
class TestUnlinkAndDeleteIfOrphan:
    """Unlink and orphan delete must happen in a single transaction."""

    def test_orphan_is_deleted_with_documents_in_one_commit(self):
        document = Document(id=1, url="guarantor/7/ine.pdf")
        self.db.query.side_effect = [_count_query(0), _documents_query([document])]

        keys = self.repository.unlink_and_delete_if_orphan("DRV-001", self.guarantor)

        assert keys == ["guarantor/7/ine.pdf"]
        self.db.delete.assert_any_call(document)
        self.db.delete.assert_any_call(self.guarantor)
        self.db.expire.assert_called_once_with(self.guarantor)
        self.db.commit.assert_called_once()

    def test_shared_guarantor_is_only_unlinked(self):
        self.db.query.side_effect = [_count_query(1)]

        keys = self.repository.unlink_and_delete_if_orphan("DRV-001", self.guarantor)

        assert keys == []
        self.db.delete.assert_not_called()
        self.db.commit.assert_called_once()

    def test_failure_rolls_back_everything(self):
        self.db.execute.side_effect = RuntimeError("boom")

        with pytest.raises(DBOperationError):
            self.repository.unlink_and_delete_if_orphan("DRV-001", self.guarantor)

        self.db.rollback.assert_called_once()
        self.db.commit.assert_not_called()
