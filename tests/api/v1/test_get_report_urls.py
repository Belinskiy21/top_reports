from typing import cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1 import routes
from app.exceptions.sec import SecRequestError
from app.services.company import CompanyService


def _seed_supported_companies(session: Session) -> None:
    company_service = CompanyService()
    for name, cik, ticker in [
        ("Alphabet", "0001652044", "GOOGL"),
        ("Amazon", "0001018724", "AMZN"),
        ("Apple", "0000320193", "AAPL"),
        ("Goldman Sachs", "0000886982", "GS"),
        ("Meta", "0001326801", "META"),
        ("Netflix", "0001065280", "NFLX"),
    ]:
        _ = company_service.create(
            session,
            name=name,
            cik=cik,
            ticker=ticker,
        )


def test_get_report_urls_returns_download_urls_for_requested_companies(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_supported_companies(db_session)
    sign_up_response = client.post(
        "/api/v1/sign-up",
        json={"email": "user@example.com", "password": "super-secret"},
    )
    response_data = cast(dict[str, object], sign_up_response.json())
    token = response_data["token"]
    assert isinstance(token, str)

    class StubSecReportService:
        def get_supported_report_types(self) -> list[str]:
            return ["10-K"]

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


def test_get_report_urls_normalizes_duplicate_company_names(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_supported_companies(db_session)
    sign_up_response = client.post(
        "/api/v1/sign-up",
        json={"email": "user@example.com", "password": "super-secret"},
    )
    response_data = cast(dict[str, object], sign_up_response.json())
    token = response_data["token"]
    assert isinstance(token, str)

    class StubSecReportService:
        def get_supported_report_types(self) -> list[str]:
            return ["10-K"]

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
        json={"report_type": "10-K", "companies": ["Apple", " Apple ", "Meta", "Apple"]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "Apple": "http://testserver/api/v1/files/apple.pdf",
        "Meta": "http://testserver/api/v1/files/meta.pdf",
    }


def test_get_report_urls_requires_authorization(client: TestClient, db_session: Session) -> None:
    _seed_supported_companies(db_session)
    response = client.post(
        "/api/v1/get-report-urls",
        json={"report_type": "10-K", "companies": ["Apple"]},
    )

    assert response.status_code == 403


def test_get_report_urls_rejects_empty_company_name(
    client: TestClient,
    db_session: Session,
) -> None:
    _seed_supported_companies(db_session)
    sign_up_response = client.post(
        "/api/v1/sign-up",
        json={"email": "user@example.com", "password": "super-secret"},
    )
    response_data = cast(dict[str, object], sign_up_response.json())
    token = response_data["token"]
    assert isinstance(token, str)

    response = client.post(
        "/api/v1/get-report-urls",
        json={"report_type": "10-K", "companies": [""]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "Invalid value of company name. Supported companies names: "
            "['Alphabet', 'Amazon', 'Apple', 'Goldman Sachs', 'Meta', 'Netflix']"
        ),
    }


def test_get_report_urls_rejects_unsupported_report_type(
    client: TestClient,
    db_session: Session,
) -> None:
    _seed_supported_companies(db_session)
    sign_up_response = client.post(
        "/api/v1/sign-up",
        json={"email": "user@example.com", "password": "super-secret"},
    )
    response_data = cast(dict[str, object], sign_up_response.json())
    token = response_data["token"]
    assert isinstance(token, str)

    response = client.post(
        "/api/v1/get-report-urls",
        json={"report_type": "1-K", "companies": ["Apple"]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Invalid value of report type. Supported report types: ['10-K']",
    }


def test_get_report_urls_rejects_whitespace_company_name(
    client: TestClient,
    db_session: Session,
) -> None:
    _seed_supported_companies(db_session)
    sign_up_response = client.post(
        "/api/v1/sign-up",
        json={"email": "user@example.com", "password": "super-secret"},
    )
    response_data = cast(dict[str, object], sign_up_response.json())
    token = response_data["token"]
    assert isinstance(token, str)

    response = client.post(
        "/api/v1/get-report-urls",
        json={"report_type": "10-K", "companies": ["   "]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "Invalid value of company name. Supported companies names: "
            "['Alphabet', 'Amazon', 'Apple', 'Goldman Sachs', 'Meta', 'Netflix']"
        ),
    }


def test_get_report_urls_rejects_unsupported_company_name(
    client: TestClient,
    db_session: Session,
) -> None:
    _seed_supported_companies(db_session)
    sign_up_response = client.post(
        "/api/v1/sign-up",
        json={"email": "user@example.com", "password": "super-secret"},
    )
    response_data = cast(dict[str, object], sign_up_response.json())
    token = response_data["token"]
    assert isinstance(token, str)

    response = client.post(
        "/api/v1/get-report-urls",
        json={"report_type": "10-K", "companies": ["Beta"]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "Invalid value of company name. Supported companies names: "
            "['Alphabet', 'Amazon', 'Apple', 'Goldman Sachs', 'Meta', 'Netflix']"
        ),
    }


def test_get_report_urls_rejects_empty_companies_array(
    client: TestClient,
    db_session: Session,
) -> None:
    _seed_supported_companies(db_session)
    sign_up_response = client.post(
        "/api/v1/sign-up",
        json={"email": "user@example.com", "password": "super-secret"},
    )
    response_data = cast(dict[str, object], sign_up_response.json())
    token = response_data["token"]
    assert isinstance(token, str)

    response = client.post(
        "/api/v1/get-report-urls",
        json={"report_type": "10-K", "companies": []},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "Invalid value of company name. Supported companies names: "
            "['Alphabet', 'Amazon', 'Apple', 'Goldman Sachs', 'Meta', 'Netflix']"
        ),
    }


def test_get_report_urls_returns_bad_gateway_for_sec_error(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_supported_companies(db_session)
    sign_up_response = client.post(
        "/api/v1/sign-up",
        json={"email": "user@example.com", "password": "super-secret"},
    )
    response_data = cast(dict[str, object], sign_up_response.json())
    token = response_data["token"]
    assert isinstance(token, str)

    class StubSecReportService:
        def get_supported_report_types(self) -> list[str]:
            return ["10-K"]

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
