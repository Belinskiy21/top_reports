from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import cast
from urllib.parse import urljoin

from app.services.converters.html_to_pdf.html_renderer_factory import HtmlRendererFactory

type UrlFetcher = Callable[[str], dict[str, object]]


def html_to_pdf(
    origin_file: Path,
    base_url: str | None = None,
    url_fetcher: UrlFetcher | None = None,
) -> Path:
    pdf_path = origin_file.with_suffix(".pdf")
    html_renderer = _get_html_renderer()
    document = html_renderer(
        filename=str(origin_file),
        base_url=base_url or str(origin_file.parent),
        url_fetcher=url_fetcher,
    )
    _ = document.write_pdf(str(pdf_path))
    return pdf_path


def filing_base_url(filing_url: str) -> str:
    return urljoin(filing_url, ".")


def _get_html_renderer() -> HtmlRendererFactory:
    try:
        weasyprint = import_module("weasyprint")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "weasyprint is required for PDF conversion. Install project dependencies first.",
        ) from exc

    return cast(HtmlRendererFactory, weasyprint.HTML)
