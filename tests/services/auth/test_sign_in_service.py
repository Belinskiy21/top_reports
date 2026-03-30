import pytest
from sqlalchemy.orm import Session

from app.exceptions.auth import InvalidCredentialsError
from app.schema.user import UserSignInRequest, UserSignUpRequest
from app.services.auth import AuthService


def test_sign_in_returns_new_token_for_valid_credentials(db_session: Session) -> None:
    service = AuthService()
    sign_up_user = service.sign_up(
        db_session,
        UserSignUpRequest(email="user@example.com", password="super-secret"),
    )

    signed_in_user = service.sign_in(
        db_session,
        UserSignInRequest(email="user@example.com", password="super-secret"),
    )

    assert signed_in_user.email == "user@example.com"
    assert signed_in_user.token.strip() != ""
    assert signed_in_user.token != sign_up_user.token


def test_sign_in_raises_for_invalid_password(db_session: Session) -> None:
    service = AuthService()
    _ = service.sign_up(
        db_session,
        UserSignUpRequest(email="user@example.com", password="super-secret"),
    )

    with pytest.raises(InvalidCredentialsError):
        _ = service.sign_in(
            db_session,
            UserSignInRequest(email="user@example.com", password="wrong-password"),
        )
