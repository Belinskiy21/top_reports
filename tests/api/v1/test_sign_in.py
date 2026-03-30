from typing import cast

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import UserRecord


def test_sign_in_returns_user_for_valid_credentials(
    client: TestClient,
    db_session: Session,
) -> None:
    sign_up_response = client.post(
        "/api/v1/sign-up",
        json={"email": "user@example.com", "password": "super-secret"},
    )

    response = client.post(
        "/api/v1/sign-in",
        json={"email": "user@example.com", "password": "super-secret"},
    )

    assert response.status_code == 200
    response_data = cast(dict[str, object], response.json())
    sign_up_response_data = cast(dict[str, object], sign_up_response.json())
    assert response_data["id"] == 1
    assert response_data["email"] == "user@example.com"
    assert isinstance(response_data["token"], str)
    assert response_data["token"].strip() != ""
    assert response_data["token"] != sign_up_response_data["token"]

    user = db_session.get(UserRecord, 1)
    assert user is not None
    assert user.auth_token == response_data["token"]


def test_sign_in_rejects_invalid_password(client: TestClient) -> None:
    _ = client.post(
        "/api/v1/sign-up",
        json={"email": "user@example.com", "password": "super-secret"},
    )

    response = client.post(
        "/api/v1/sign-in",
        json={"email": "user@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}
