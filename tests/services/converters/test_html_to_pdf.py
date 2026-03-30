from importlib import import_module
from pathlib import Path

import pytest

from app.services.converters.html_to_pdf.html_to_pdf import filing_base_url, html_to_pdf

html_to_pdf_module = import_module("app.services.converters.html_to_pdf.html_to_pdf")


def test_html_to_pdf_creates_pdf_from_html_like_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    origin_file = tmp_path / "report.html"
    _ = origin_file.write_text("<h1>Annual Report</h1><p>Revenue &amp; Growth</p>")

    class StubHtmlRenderer:
        def __init__(
            self,
            *,
            filename: str,
            base_url: str,
            url_fetcher: object | None = None,
        ) -> None:
            self.filename: str = filename
            self.base_url: str = base_url
            assert url_fetcher is None

        def write_pdf(self, target: str) -> None:
            assert self.filename == str(origin_file)
            assert self.base_url == str(origin_file.parent)
            _ = Path(target).write_bytes(b"%PDF-1.4 test")

    monkeypatch.setattr(html_to_pdf_module, "_get_html_renderer", lambda: StubHtmlRenderer)
    pdf_path = html_to_pdf(origin_file)

    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"
    assert pdf_path.read_bytes().startswith(b"%PDF")


def test_html_to_pdf_uses_explicit_base_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    origin_file = tmp_path / "report.html"
    _ = origin_file.write_text("<img src='g66145g66i43.jpg'>")

    class StubHtmlRenderer:
        def __init__(
            self,
            *,
            filename: str,
            base_url: str,
            url_fetcher: object | None = None,
        ) -> None:
            assert filename == str(origin_file)
            assert base_url == "https://www.sec.gov/Archives/edgar/data/320193/000032019324000001/"
            assert url_fetcher is None

        def write_pdf(self, target: str) -> None:
            _ = Path(target).write_bytes(b"%PDF-1.4 test")

    monkeypatch.setattr(html_to_pdf_module, "_get_html_renderer", lambda: StubHtmlRenderer)
    pdf_path = html_to_pdf(
        origin_file,
        "https://www.sec.gov/Archives/edgar/data/320193/000032019324000001/",
    )

    assert pdf_path.exists()


def test_html_to_pdf_passes_url_fetcher(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    origin_file = tmp_path / "report.html"
    _ = origin_file.write_text("<img src='asset.jpg'>")

    def url_fetcher(url: str) -> dict[str, object]:
        return {"string": url.encode()}

    class StubHtmlRenderer:
        def __init__(
            self,
            *,
            filename: str,
            base_url: str,
            url_fetcher: object | None = None,
        ) -> None:
            assert filename == str(origin_file)
            assert base_url == str(origin_file.parent)
            assert url_fetcher is not None

        def write_pdf(self, target: str) -> None:
            _ = Path(target).write_bytes(b"%PDF-1.4 test")

    monkeypatch.setattr(html_to_pdf_module, "_get_html_renderer", lambda: StubHtmlRenderer)
    pdf_path = html_to_pdf(origin_file, url_fetcher=url_fetcher)

    assert pdf_path.exists()


def test_filing_base_url_returns_parent_directory() -> None:
    assert (
        filing_base_url(
            "https://www.sec.gov/Archives/edgar/data/320193/000032019324000001/aapl-10k.htm",
        )
        == "https://www.sec.gov/Archives/edgar/data/320193/000032019324000001/"
    )
