import pytest
import uuid
from sqlalchemy.orm import Session
from app.database.core import engine, Base
from app.database.session import SessionLocal
from app.models.users import User, Role, Permission


@pytest.fixture(scope="function")
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def test_user_role_permission_relationships(db: Session):
    role_admin = Role(name="admin")
    perm_read = Permission(name="read")
    perm_write = Permission(name="write")
    role_admin.permissions = [perm_read, perm_write]

    unique_username = f"alice_{uuid.uuid4().hex[:8]}"

    user = User(
        username=unique_username,
        name="Alice",
        surnames="Smith",
        password="hashed_pwd",
        role=role_admin
    )

    db.add_all([role_admin, perm_read, perm_write, user])
    db.commit()

    user_from_db = db.query(User).filter_by(username=unique_username).first()
    assert user_from_db is not None
    assert user_from_db.role.name == "admin"

    assert len(user_from_db.role.permissions) == 2
    permission_names = {perm.name for perm in user_from_db.role.permissions}
    assert permission_names == {"read", "write"}

    new_role = Role(name="manager")
    db.add(new_role)
    db.commit()

    user_from_db.role = new_role
    db.commit()
    assert user_from_db.role.name == "manager"
