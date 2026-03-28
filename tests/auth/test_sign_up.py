from typing import cast

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import UserRecord


def test_sign_up_creates_user(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/api/v1/sign-up",
        json={"email": "user@example.com", "password": "super-secret"},
    )

    assert response.status_code == 201
    response_data = cast(dict[str, object], response.json())
    assert response_data["id"] == 1
    assert response_data["email"] == "user@example.com"
    assert isinstance(response_data["token"], str)
    assert response_data["token"].strip() != ""

    user = db_session.get(UserRecord, 1)
    assert user is not None
    assert user.auth_token == response_data["token"]


def test_sign_up_rejects_duplicate_email(client: TestClient) -> None:
    _ = client.post(
        "/api/v1/sign-up",
        json={"email": "user@example.com", "password": "super-secret"},
    )

    response = client.post(
        "/api/v1/sign-up",
        json={"email": "user@example.com", "password": "another-secret"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "User with this email already exists"}
