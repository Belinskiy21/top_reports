import shutil
from pathlib import Path
from urllib.parse import urljoin
from uuid import uuid4

from fastapi.responses import FileResponse, Response


class LocalStorageService:
    def __init__(self, local_root: Path) -> None:
        self._local_root: Path = local_root

    def store_pdf(self, company_name: str, pdf_path: Path) -> str:
        file_name = self._build_file_name(company_name)
        self._local_root.mkdir(parents=True, exist_ok=True)
        destination = self._local_root / file_name
        _ = shutil.copyfile(pdf_path, destination)
        return file_name

    def get_public_url(self, file_name: str, public_base_url: str) -> str:
        return urljoin(public_base_url, f"api/v1/files/{file_name}")

    def download_file(self, file_name: str) -> Response:
        file_path = self._local_root / file_name
        if not self.has_valid_pdf(file_name):
            raise FileNotFoundError(file_name)

        return FileResponse(file_path, filename=file_name, media_type="application/pdf")

    def has_valid_pdf(self, file_name: str) -> bool:
        file_path = self._local_root / file_name
        if not file_path.exists():
            return False

        with file_path.open("rb") as file_handle:
            header = file_handle.read(5)

        return header == b"%PDF-"

    def delete_file(self, file_name: str) -> None:
        file_path = self._local_root / file_name
        if file_path.exists():
            file_path.unlink()

    def _build_file_name(self, company_name: str) -> str:
        normalized_company_name = company_name.lower().replace(" ", "_")
        return f"{normalized_company_name}_{uuid4().hex}.pdf"
