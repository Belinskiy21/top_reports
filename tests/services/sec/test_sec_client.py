import asyncio

import pytest

from app.services.sec.sec_client import DEFAULT_SEC_USER_AGENT, SEC_DATA_BASE_URL, SecClient


class StubResponse:
    def __init__(self, *, json_data: dict[str, object] | None = None, content: bytes = b"") -> None:
        self._json_data: dict[str, object] = json_data or {}
        self.content: bytes = content

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self._json_data


class StubHttpClient:
    def __init__(self, response: StubResponse) -> None:
        self._response: StubResponse = response
        self.calls: list[tuple[str, dict[str, str]]] = []

    async def get(self, url: str, headers: dict[str, str]) -> StubResponse:
        self.calls.append((url, headers))
        return self._response


def test_get_submissions_calls_sec_data_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", DEFAULT_SEC_USER_AGENT)
    client = SecClient()
    stub_http_client = StubHttpClient(StubResponse(json_data={"filings": {}}))
    monkeypatch.setattr(client, "_client", stub_http_client)

    payload = asyncio.run(client.get_submissions("0000320193"))

    assert payload == {"filings": {}}
    assert stub_http_client.calls[0][0] == f"{SEC_DATA_BASE_URL}submissions/CIK0000320193.json"
    assert stub_http_client.calls[0][1]["User-Agent"] == DEFAULT_SEC_USER_AGENT


def test_download_file_returns_response_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", DEFAULT_SEC_USER_AGENT)
    client = SecClient()
    stub_http_client = StubHttpClient(StubResponse(content=b"file-bytes"))
    monkeypatch.setattr(client, "_client", stub_http_client)

    content = asyncio.run(client.download_file("https://www.sec.gov/test-file.txt"))

    assert content == b"file-bytes"
    assert stub_http_client.calls[0][0] == "https://www.sec.gov/test-file.txt"
    assert stub_http_client.calls[0][1]["User-Agent"] == DEFAULT_SEC_USER_AGENT
