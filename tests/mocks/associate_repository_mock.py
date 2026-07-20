from app.models.car import Associate


class AssociateRepositoryMock:
    """Associate repository mock class."""

    def __init__(self):
        self.associates: list[Associate] = [
            Associate(id=1, name="Juan", surnames="Garcia Lopez", telephones=["+521234567890"]),
            Associate(id=2, name="Maria", surnames="Torres Perez", telephones=[]),
        ]
        self._next_id = 3
        self.cars_linked: set[int] = set()

    def reset(self):
        self.associates = [
            Associate(id=1, name="Juan", surnames="Garcia Lopez", telephones=["+521234567890"]),
            Associate(id=2, name="Maria", surnames="Torres Perez", telephones=[]),
        ]
        self._next_id = 3
        self.cars_linked = set()

    def get_by_id(self, associate_id: int) -> Associate | None:
        return next((a for a in self.associates if a.id == associate_id), None)

    def list_all(self, search: str | None = None) -> list[Associate]:
        if search:
            return [
                a for a in self.associates
                if search.lower() in a.name.lower() or search.lower() in a.surnames.lower()
            ]
        return list(self.associates)

    def has_linked_cars(self, associate_id: int) -> bool:
        return associate_id in self.cars_linked

    def create(self, associate: Associate) -> Associate:
        associate.id = self._next_id
        self._next_id += 1
        self.associates.append(associate)
        return associate

    def update(self, associate: Associate) -> Associate:
        return associate

    def delete(self, associate: Associate) -> None:
        self.associates = [a for a in self.associates if a.id != associate.id]
