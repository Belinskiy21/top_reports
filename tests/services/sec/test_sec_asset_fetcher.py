import pytest

from app.services.sec.sec_asset_fetcher import SecAssetFetcher
from app.services.sec.sec_client import DEFAULT_SEC_USER_AGENT


def test_build_returns_fetcher() -> None:
    service = SecAssetFetcher()

    assert service.build() is not None


def test_build_uses_sec_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", DEFAULT_SEC_USER_AGENT)
    captured: dict[str, object] = {}
    service = SecAssetFetcher()

    class StubResponse:
        def __init__(self) -> None:
            self.content: bytes = b"image-bytes"
            self.headers: dict[str, str] = {"Content-Type": "image/jpeg"}
            self.url: str = "https://www.sec.gov/Archives/test.jpg"

        def raise_for_status(self) -> None:
            return None

    def stub_get(url: str, *, headers: dict[str, str], timeout: float) -> StubResponse:
        captured["url"] = url
        captured["headers"] = headers
        captured["timeout"] = timeout
        return StubResponse()

    def stub_default_url_fetcher(url: str) -> dict[str, object]:
        return {"string": url.encode()}

    monkeypatch.setattr(service, "_http_get", stub_get)
    monkeypatch.setattr(service, "_get_default_url_fetcher", lambda: stub_default_url_fetcher)
    fetcher = service.build()

    assert fetcher is not None
    result = fetcher("https://www.sec.gov/Archives/test.jpg")

    assert captured["url"] == "https://www.sec.gov/Archives/test.jpg"
    assert captured["headers"] == {
        "User-Agent": DEFAULT_SEC_USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
    }
    assert captured["timeout"] == 30.0
    assert result == {
        "string": b"image-bytes",
        "mime_type": "image/jpeg",
        "redirected_url": "https://www.sec.gov/Archives/test.jpg",
    }


def test_build_falls_back_for_non_sec_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    default_called: dict[str, object] = {}
    service = SecAssetFetcher()

    def stub_default_url_fetcher(url: str) -> dict[str, object]:
        default_called["url"] = url
        return {"string": b"fallback"}

    monkeypatch.setattr(service, "_get_default_url_fetcher", lambda: stub_default_url_fetcher)
    fetcher = service.build()

    assert fetcher is not None
    result = fetcher("https://example.com/image.jpg")

    assert default_called["url"] == "https://example.com/image.jpg"
    assert result == {"string": b"fallback"}
