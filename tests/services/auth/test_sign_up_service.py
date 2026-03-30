import pytest
from sqlalchemy.orm import Session

from app.exceptions.auth import UserAlreadyExistsError
from app.schema.user import UserSignUpRequest
from app.services.auth import AuthService
from app.services.user import UserService


def test_sign_up_creates_user_and_returns_token(db_session: Session) -> None:
    service = AuthService()

    user = service.sign_up(
        db_session,
        UserSignUpRequest(email="user@example.com", password="super-secret"),
    )

    persisted_user = UserService().find_by_email(db_session, "user@example.com")
    assert persisted_user is not None
    assert user.email == "user@example.com"
    assert user.token.strip() != ""
    assert persisted_user.password_hash != "super-secret"
    assert persisted_user.auth_token == user.token


def test_sign_up_raises_for_existing_email(db_session: Session) -> None:
    service = AuthService()
    payload = UserSignUpRequest(email="user@example.com", password="super-secret")
    _ = service.sign_up(db_session, payload)

    with pytest.raises(UserAlreadyExistsError):
        _ = service.sign_up(db_session, payload)
