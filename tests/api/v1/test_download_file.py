from typing import cast

import pytest
from fastapi.responses import Response
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1 import routes


def test_download_file_returns_response_for_authorized_user(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sign_up_response = client.post(
        "/api/v1/sign-up",
        json={"email": "user@example.com", "password": "super-secret"},
    )
    response_data = cast(dict[str, object], sign_up_response.json())
    token = response_data["token"]
    assert isinstance(token, str)

    class StubSecReportService:
        def download_file(
            self,
            session: Session,
            file_name: str,
            downloaded_by: int,
        ) -> Response:
            assert session is not None
            assert file_name == "apple.pdf"
            assert downloaded_by == 1
            return Response(content=b"%PDF-1.4 test", media_type="application/pdf")

    monkeypatch.setattr(routes, "sec_report_service", StubSecReportService())
    response = client.get(
        "/api/v1/files/apple.pdf",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == b"%PDF-1.4 test"


def test_download_file_returns_not_found_for_missing_file(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sign_up_response = client.post(
        "/api/v1/sign-up",
        json={"email": "user@example.com", "password": "super-secret"},
    )
    response_data = cast(dict[str, object], sign_up_response.json())
    token = response_data["token"]
    assert isinstance(token, str)

    class StubSecReportService:
        def download_file(
            self,
            session: Session,
            file_name: str,
            downloaded_by: int,
        ) -> Response:
            _ = session
            _ = file_name
            _ = downloaded_by
            raise FileNotFoundError("missing.pdf")

    monkeypatch.setattr(routes, "sec_report_service", StubSecReportService())
    response = client.get(
        "/api/v1/files/missing.pdf",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "File not found"}
