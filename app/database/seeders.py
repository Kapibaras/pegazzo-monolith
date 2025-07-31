from app.database.session import SessionLocal
from app.models.users import Role


def seeders(db: SessionLocal):
    """Seed roles into the database."""
    roles = [
        Role(id=1, name="admin"),
        Role(id=2, name="user"),
    ]

    for role in roles:
        exists = db.query(Role).filter_by(id=role.id).first()
        if not exists:
            db.add(role)
        else:
            exists.name = role.name

    db.commit()


if __name__ == "__main__":
    db = SessionLocal()
    seeders(db)
    db.close()
