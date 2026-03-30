import pytest

from app.services.storage.local_storage_service import LocalStorageService
from app.services.storage.s3_storage_service import S3StorageService
from app.services.storage.storage_service import StorageService


def test_storage_service_defaults_to_local_in_development(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("STORAGE_BACKEND", raising=False)
    monkeypatch.setenv("APP_ENV", "development")

    service = StorageService()

    assert isinstance(service._backend, LocalStorageService)  # pyright: ignore[reportPrivateUsage]


def test_storage_service_defaults_to_s3_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("STORAGE_BACKEND", raising=False)
    monkeypatch.setenv("APP_ENV", "production")

    service = StorageService()

    assert isinstance(service._backend, S3StorageService)  # pyright: ignore[reportPrivateUsage]


def test_storage_service_explicit_backend_overrides_app_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("STORAGE_BACKEND", "local")

    service = StorageService()

    assert isinstance(service._backend, LocalStorageService)  # pyright: ignore[reportPrivateUsage]
