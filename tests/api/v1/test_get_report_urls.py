from typing import cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1 import routes
from app.exceptions.sec import SecRequestError


def test_get_report_urls_returns_download_urls_for_requested_companies(
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
        async def get_recent_report_urls(
            self,
            session: Session,
            report_type: str,
            company_names: list[str],
            public_base_url: str,
            created_by: int,
        ) -> dict[str, str]:
            assert session is not None
            assert report_type == "10-K"
            assert company_names == ["Apple", "Meta"]
            assert public_base_url == "http://testserver/"
            assert created_by == 1
            return {
                "Apple": "http://testserver/api/v1/files/apple.pdf",
                "Meta": "http://testserver/api/v1/files/meta.pdf",
            }

    monkeypatch.setattr(routes, "sec_report_service", StubSecReportService())
    response = client.post(
        "/api/v1/get-report-urls",
        json={"report_type": "10-K", "companies": ["Apple", "Meta"]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "Apple": "http://testserver/api/v1/files/apple.pdf",
        "Meta": "http://testserver/api/v1/files/meta.pdf",
    }


def test_get_report_urls_requires_authorization(client: TestClient) -> None:
    response = client.post(
        "/api/v1/get-report-urls",
        json={"report_type": "10-K", "companies": ["Apple"]},
    )

    assert response.status_code == 403


def test_get_report_urls_returns_bad_gateway_for_sec_error(
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
        async def get_recent_report_urls(
            self,
            session: Session,
            report_type: str,
            company_names: list[str],
            public_base_url: str,
            created_by: int,
        ) -> dict[str, str]:
            _ = session
            _ = report_type
            _ = company_names
            _ = public_base_url
            _ = created_by
            raise SecRequestError(
                "SEC service request failed",
                status_code=502,
                upstream_status_code=403,
                upstream_url="https://www.sec.gov/test",
                upstream_message="Forbidden",
            )

    monkeypatch.setattr(routes, "sec_report_service", StubSecReportService())
    response = client.post(
        "/api/v1/get-report-urls",
        json={"report_type": "10-K", "companies": ["Apple"]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "SEC service request failed"}
