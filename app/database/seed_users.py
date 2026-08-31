from app.database.session import SessionLocal
from app.models.users import User
from app.utils.auth import AuthUtils

_USERS = [
    {
        "username": "PegazzoOwner",
        "name": "Pegazzo",
        "surnames": "Auto",
        "password": "PegazzoProject$$",
        "role_id": 1,
    },
]


def seed_users(db: SessionLocal):
    """Seed production users into the database."""
    for user_data in _USERS:
        exists = db.query(User).filter_by(username=user_data["username"]).first()
        if exists:
            print(f"User '{user_data['username']}' already exists, skipping.")
            continue

        user = User(
            username=user_data["username"],
            name=user_data["name"],
            surnames=user_data["surnames"],
            password=AuthUtils.hash_password(user_data["password"]),
            role_id=user_data["role_id"],
        )
        db.add(user)
        print(f"User '{user_data['username']}' created.")

    db.commit()


if __name__ == "__main__":
    db = SessionLocal()
    seed_users(db)
    db.close()
