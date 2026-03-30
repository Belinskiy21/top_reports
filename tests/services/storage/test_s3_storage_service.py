import pytest
from fastapi.responses import RedirectResponse

from app.services.storage.s3_storage_service import S3StorageService


def test_download_file_returns_s3_redirect(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("S3_BUCKET_NAME", "reports-bucket")
    monkeypatch.setenv("AWS_REGION", "eu-north-1")
    service = S3StorageService()

    response = service.download_file("apple_report.pdf")

    assert isinstance(response, RedirectResponse)
    assert response.headers["location"] == (
        "https://reports-bucket.s3.eu-north-1.amazonaws.com/apple_report.pdf"
    )


def test_get_public_url_prefers_custom_public_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("S3_PUBLIC_BASE_URL", "https://cdn.example.com/reports")
    service = S3StorageService()

    public_url = service.get_public_url("apple_report.pdf", "http://ignored/")

    assert public_url == "https://cdn.example.com/reports/apple_report.pdf"
