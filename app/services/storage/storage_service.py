import os
from pathlib import Path

from fastapi.responses import Response

from app.services.storage.local_storage_service import LocalStorageService
from app.services.storage.s3_storage_service import S3StorageService
from app.services.storage.storage_backend_protocol import StorageBackendProtocol


class StorageService:
    def __init__(self) -> None:
        self._backend: StorageBackendProtocol = self._build_backend()

    def store_pdf(self, company_name: str, pdf_path: Path) -> str:
        return self._backend.store_pdf(company_name, pdf_path)

    def get_public_url(self, file_name: str, public_base_url: str) -> str:
        return self._backend.get_public_url(file_name, public_base_url)

    def download_file(self, file_name: str) -> Response:
        return self._backend.download_file(file_name)

    def has_valid_pdf(self, file_name: str) -> bool:
        return self._backend.has_valid_pdf(file_name)

    def delete_file(self, file_name: str) -> None:
        self._backend.delete_file(file_name)

    def _build_backend(self) -> StorageBackendProtocol:
        storage_backend = os.getenv("STORAGE_BACKEND")
        app_env = os.getenv("APP_ENV", "development")
        if storage_backend is None:
            storage_backend = "s3" if app_env == "production" else "local"

        if storage_backend == "s3":
            return S3StorageService()

        return LocalStorageService(Path(os.getenv("LOCAL_STORAGE_DIR", "storage/files")))
