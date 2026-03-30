from pathlib import Path

import pytest
from fastapi.responses import FileResponse

from app.services.storage.local_storage_service import LocalStorageService


def test_store_pdf_locally_and_build_public_url(tmp_path: Path) -> None:
    service = LocalStorageService(tmp_path / "storage")
    pdf_path = tmp_path / "report.pdf"
    _ = pdf_path.write_bytes(b"%PDF-1.4 test")

    file_name = service.store_pdf("Apple", pdf_path)
    public_url = service.get_public_url(file_name, "http://testserver/")

    assert file_name.startswith("apple_")
    assert (tmp_path / "storage" / file_name).exists()
    assert public_url == f"http://testserver/api/v1/files/{file_name}"


def test_download_file_returns_local_file_response(tmp_path: Path) -> None:
    service = LocalStorageService(tmp_path / "storage")
    file_name = "apple_report.pdf"
    file_path = tmp_path / "storage" / file_name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    _ = file_path.write_bytes(b"%PDF-1.4 test")

    response = service.download_file(file_name)

    assert isinstance(response, FileResponse)
    assert response.path == file_path


def test_has_valid_pdf_returns_false_for_invalid_local_file(tmp_path: Path) -> None:
    service = LocalStorageService(tmp_path / "storage")
    file_name = "apple_report.pdf"
    file_path = tmp_path / "storage" / file_name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    _ = file_path.write_text("<html>not a pdf</html>")

    assert service.has_valid_pdf(file_name) is False


def test_download_file_raises_for_invalid_local_file(tmp_path: Path) -> None:
    service = LocalStorageService(tmp_path / "storage")
    file_name = "apple_report.pdf"
    file_path = tmp_path / "storage" / file_name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    _ = file_path.write_text("<html>not a pdf</html>")

    with pytest.raises(FileNotFoundError):
        _ = service.download_file(file_name)


def test_delete_file_removes_existing_local_file(tmp_path: Path) -> None:
    service = LocalStorageService(tmp_path / "storage")
    file_name = "apple_report.pdf"
    file_path = tmp_path / "storage" / file_name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    _ = file_path.write_bytes(b"%PDF-1.4 test")

    service.delete_file(file_name)

    assert not file_path.exists()
