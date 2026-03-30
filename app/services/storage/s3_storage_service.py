import importlib
import os
from pathlib import Path
from urllib.parse import urljoin
from uuid import uuid4

from fastapi.responses import RedirectResponse, Response


class S3StorageService:
    def store_pdf(self, company_name: str, pdf_path: Path) -> str:
        boto3 = importlib.import_module("boto3")
        bucket_name = os.getenv("S3_BUCKET_NAME")
        if not bucket_name:
            raise RuntimeError("S3_BUCKET_NAME must be configured for s3 storage")

        file_name = self._build_file_name(company_name)
        s3_client = boto3.client("s3")  # pyright: ignore[reportAny]
        s3_client.upload_file(str(pdf_path), bucket_name, file_name)  # pyright: ignore[reportAny]
        return file_name

    def get_public_url(self, file_name: str, public_base_url: str) -> str:
        _ = public_base_url
        configured_public_base_url = os.getenv("S3_PUBLIC_BASE_URL")
        if configured_public_base_url:
            normalized_base_url = (
                configured_public_base_url
                if configured_public_base_url.endswith("/")
                else f"{configured_public_base_url}/"
            )
            return urljoin(normalized_base_url, file_name)

        bucket_name = os.getenv("S3_BUCKET_NAME")
        region_name = os.getenv("AWS_REGION", "us-east-1")
        if not bucket_name:
            raise RuntimeError("S3_BUCKET_NAME must be configured for s3 storage")

        return f"https://{bucket_name}.s3.{region_name}.amazonaws.com/{file_name}"

    def download_file(self, file_name: str) -> Response:
        return RedirectResponse(self.get_public_url(file_name, ""))

    def has_valid_pdf(self, file_name: str) -> bool:
        _ = file_name
        return True

    def delete_file(self, file_name: str) -> None:
        boto3 = importlib.import_module("boto3")
        bucket_name = os.getenv("S3_BUCKET_NAME")
        if not bucket_name:
            raise RuntimeError("S3_BUCKET_NAME must be configured for s3 storage")

        s3_client = boto3.client("s3")  # pyright: ignore[reportAny]
        s3_client.delete_object(Bucket=bucket_name, Key=file_name)  # pyright: ignore[reportAny]

    def _build_file_name(self, company_name: str) -> str:
        normalized_company_name = company_name.lower().replace(" ", "_")
        return f"{normalized_company_name}_{uuid4().hex}.pdf"
