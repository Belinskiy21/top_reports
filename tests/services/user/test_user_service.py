import pytest
from sqlalchemy.orm import Session

from app.exceptions.auth import UserAlreadyExistsError
from app.services.user import UserService


def test_create_and_find_by_email(db_session: Session) -> None:
    service = UserService()

    created_user = service.create(
        db_session,
        email="user@example.com",
        password_hash="hashed-password",
        auth_token="token",
    )
    persisted_user = service.save(db_session, created_user)
    found_user = service.find_by_email(db_session, "user@example.com")

    assert persisted_user.id > 0
    assert found_user is not None
    assert found_user.email == "user@example.com"
    assert found_user.password_hash == "hashed-password"


def test_create_raises_for_duplicate_email(db_session: Session) -> None:
    service = UserService()

    created_user = service.create(
        db_session,
        email="user@example.com",
        password_hash="hashed-password",
        auth_token="token",
    )
    _ = service.save(db_session, created_user)

    with pytest.raises(UserAlreadyExistsError):
        _ = service.create(
            db_session,
            email="user@example.com",
            password_hash="another-hash",
            auth_token="another-token",
        )
