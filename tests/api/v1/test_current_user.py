from typing import cast

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.current_user import get_current_user


def test_get_current_user_returns_user_for_valid_token(
    client: TestClient,
    db_session: Session,
) -> None:
    sign_up_response = client.post(
        "/api/v1/sign-up",
        json={"email": "user@example.com", "password": "super-secret"},
    )
    response_data = cast(dict[str, object], sign_up_response.json())
    token = response_data["token"]
    assert isinstance(token, str)

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    user = get_current_user(credentials=credentials, session=db_session)

    assert user.id == 1
    assert user.email == "user@example.com"


def test_get_current_user_rejects_invalid_token(db_session: Session) -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")

    try:
        _ = get_current_user(credentials=credentials, session=db_session)
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Invalid or expired token"
    else:
        raise AssertionError("Expected HTTPException for invalid token")
