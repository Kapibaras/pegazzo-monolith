"""Tests for PGZ-130: archive, unarchive and delete (hard / soft) of a car."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from app.models.contract import Contract
from app.models.document import Document
from tests.unit.routers.test_car_router import BASE_PAYLOAD

ENDPOINT = "/pegazzo/management/cars"


@pytest.fixture
def created_car(authorized_client):
    """Create CAR-001 through the API and return its id."""
    response = authorized_client.post(ENDPOINT, json=BASE_PAYLOAD)
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture
def archived_car(authorized_client, created_car):
    """CAR-001 already archived."""
    assert authorized_client.patch(f"{ENDPOINT}/{created_car}/archive").status_code == 200
    return created_car


def _contract(car_id: str, start_offset: int, end_offset: int) -> Contract:
    today = datetime.now(UTC).date()
    return Contract(
        id="CT-1",
        start_date=today + timedelta(days=start_offset),
        end_date=today + timedelta(days=end_offset),
        type="weekly",
        amount=1000,
        guarantee_amount=1000,
        car_id=car_id,
        driver_id="D-1",
    )


class TestArchiveCar:
    """PATCH /management/cars/{car_id}/archive and /unarchive."""

    def test_archive_success(self, authorized_client, created_car):
        response = authorized_client.patch(f"{ENDPOINT}/{created_car}/archive")

        assert response.status_code == 200
        assert response.json()["archivedAt"] is not None

    def test_archived_car_leaves_default_listing_and_shows_with_filter(self, authorized_client, archived_car):
        default = authorized_client.get(ENDPOINT).json()
        archived = authorized_client.get(ENDPOINT, params={"archived": True}).json()

        assert default["pagination"]["total"] == 0
        assert [c["id"] for c in archived["cars"]] == [archived_car]

    def test_archive_blocked_by_active_contract(self, authorized_client, created_car):
        authorized_client.car_repo.contracts.append(_contract(created_car, -5, 5))

        response = authorized_client.patch(f"{ENDPOINT}/{created_car}/archive")

        assert response.status_code == 400
        assert response.json()["detail"] == "Cannot archive a car with an active assignment"
        assert authorized_client.car_repo.get_by_id(created_car).archived_at is None

    def test_archive_not_blocked_by_expired_contract(self, authorized_client, created_car):
        authorized_client.car_repo.contracts.append(_contract(created_car, -30, -1))

        response = authorized_client.patch(f"{ENDPOINT}/{created_car}/archive")

        assert response.status_code == 200

    def test_archive_twice_fails(self, authorized_client, archived_car):
        response = authorized_client.patch(f"{ENDPOINT}/{archived_car}/archive")

        assert response.status_code == 400
        assert "already archived" in response.json()["detail"]

    def test_archive_car_not_found(self, authorized_client):
        assert authorized_client.patch(f"{ENDPOINT}/NOPE/archive").status_code == 404

    def test_archive_requires_auth(self, client):
        assert client.patch(f"{ENDPOINT}/CAR-001/archive").status_code == 401

    def test_archive_forbidden_for_employee(self, employee_authorized_client):
        assert employee_authorized_client.patch(f"{ENDPOINT}/CAR-001/archive").status_code == 403

    def test_unarchive_success(self, authorized_client, archived_car):
        response = authorized_client.patch(f"{ENDPOINT}/{archived_car}/unarchive")

        assert response.status_code == 200
        assert response.json()["archivedAt"] is None
        assert authorized_client.get(ENDPOINT).json()["pagination"]["total"] == 1

    def test_unarchive_not_archived_fails(self, authorized_client, created_car):
        response = authorized_client.patch(f"{ENDPOINT}/{created_car}/unarchive")

        assert response.status_code == 400
        assert "not archived" in response.json()["detail"]

    def test_unarchive_car_not_found(self, authorized_client):
        assert authorized_client.patch(f"{ENDPOINT}/NOPE/unarchive").status_code == 404

    def test_unarchive_requires_auth(self, client):
        assert client.patch(f"{ENDPOINT}/CAR-001/unarchive").status_code == 401

    def test_unarchive_forbidden_for_employee(self, employee_authorized_client):
        assert employee_authorized_client.patch(f"{ENDPOINT}/CAR-001/unarchive").status_code == 403


class TestDeleteCar:
    """DELETE /management/cars/{car_id}."""

    def test_delete_requires_archived_car(self, authorized_client, created_car):
        response = authorized_client.delete(f"{ENDPOINT}/{created_car}")

        assert response.status_code == 400
        assert response.json()["detail"] == "Car must be archived before deletion"
        assert authorized_client.car_repo.get_by_id(created_car) is not None

    def test_hard_delete_without_history(self, authorized_client, archived_car):
        response = authorized_client.delete(f"{ENDPOINT}/{archived_car}")

        assert response.status_code == 200
        assert authorized_client.car_repo.hard_deleted_ids == [archived_car]
        assert authorized_client.car_repo.get_by_id(archived_car) is None
        assert authorized_client.get(f"{ENDPOINT}/{archived_car}").status_code == 404

    def test_hard_delete_moves_documents_and_images_to_deleted_prefix(self, authorized_client, created_car):
        repo = authorized_client.car_repo
        car = repo.get_by_id(created_car)
        car.agency_image = "https://img.example/car_agency_image/CAR-001/a.png"
        car.photos = ["https://img.example/car_photo/CAR-001/1.png"]
        repo.car_documents[created_car] = [Document(id=1, type="invoice", url="car/CAR-001/doc.pdf", category="legal")]
        authorized_client.patch(f"{ENDPOINT}/{created_car}/archive")

        with (
            patch("app.services.car.r2.soft_delete_document") as soft_document,
            patch("app.services.car.r2.soft_delete_image") as soft_image,
        ):
            response = authorized_client.delete(f"{ENDPOINT}/{created_car}")

        assert response.status_code == 200
        soft_document.assert_called_once_with("car/CAR-001/doc.pdf")
        assert [c.args[0] for c in soft_image.call_args_list] == [
            "https://img.example/car_agency_image/CAR-001/a.png",
            "https://img.example/car_photo/CAR-001/1.png",
        ]

    def test_hard_delete_succeeds_even_if_storage_fails(self, authorized_client, created_car):
        repo = authorized_client.car_repo
        repo.car_documents[created_car] = [Document(id=1, type="invoice", url="car/CAR-001/doc.pdf", category="legal")]
        authorized_client.patch(f"{ENDPOINT}/{created_car}/archive")

        with patch("app.services.car.r2.soft_delete_document", side_effect=RuntimeError("r2 down")):
            response = authorized_client.delete(f"{ENDPOINT}/{created_car}")

        assert response.status_code == 200
        assert repo.hard_deleted_ids == [created_car]

    def test_soft_delete_when_car_has_history(self, authorized_client, archived_car):
        repo = authorized_client.car_repo
        repo.history_car_ids.add(archived_car)

        with patch("app.services.car.r2.soft_delete_document") as soft_document:
            response = authorized_client.delete(f"{ENDPOINT}/{archived_car}")

        assert response.status_code == 200
        assert repo.hard_deleted_ids == []
        assert repo.get_by_id(archived_car).deleted_at is not None
        soft_document.assert_not_called()

    def test_soft_deleted_car_disappears_everywhere(self, authorized_client, archived_car):
        authorized_client.car_repo.history_car_ids.add(archived_car)
        authorized_client.delete(f"{ENDPOINT}/{archived_car}")

        assert authorized_client.get(f"{ENDPOINT}/{archived_car}").status_code == 404
        assert authorized_client.get(ENDPOINT, params={"archived": True}).json()["pagination"]["total"] == 0
        assert authorized_client.patch(f"{ENDPOINT}/{archived_car}/unarchive").status_code == 404
        assert authorized_client.delete(f"{ENDPOINT}/{archived_car}").status_code == 404

    def test_delete_car_not_found(self, authorized_client):
        assert authorized_client.delete(f"{ENDPOINT}/NOPE").status_code == 404

    def test_delete_requires_auth(self, client):
        assert client.delete(f"{ENDPOINT}/CAR-001").status_code == 401

    def test_delete_forbidden_for_employee(self, employee_authorized_client):
        assert employee_authorized_client.delete(f"{ENDPOINT}/CAR-001").status_code == 403
