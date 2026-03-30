import os
from collections.abc import Callable
from importlib import import_module
from typing import cast
from urllib.parse import urlparse

import httpx

from app.services.sec.sec_client import DEFAULT_SEC_USER_AGENT

SEC_HOSTS = {"www.sec.gov", "data.sec.gov"}
type UrlFetcher = Callable[[str], dict[str, object]]


class SecAssetFetcher:
    def build(self) -> UrlFetcher:
        default_url_fetcher = self._get_default_url_fetcher()
        default_user_agent = os.getenv("SEC_USER_AGENT", DEFAULT_SEC_USER_AGENT)

        def fetch(url: str) -> dict[str, object]:
            if urlparse(url).hostname not in SEC_HOSTS:
                return default_url_fetcher(url)

            response = self._http_get(
                url,
                headers={
                    "User-Agent": default_user_agent,
                    "Accept-Encoding": "gzip, deflate",
                },
                timeout=30.0,
            )
            _ = response.raise_for_status()
            content_type = cast(str, response.headers.get("Content-Type", ""))
            return {
                "string": response.content,
                "mime_type": content_type.split(";", maxsplit=1)[0],
                "redirected_url": str(response.url),
            }

        return fetch

    def _get_default_url_fetcher(self) -> UrlFetcher:
        try:
            weasyprint = import_module("weasyprint")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "weasyprint is required for PDF conversion. Install project dependencies first.",
            ) from exc

        return cast(UrlFetcher, weasyprint.default_url_fetcher)

    def _http_get(self, url: str, *, headers: dict[str, str], timeout: float) -> httpx.Response:
        return httpx.get(url, headers=headers, timeout=timeout)
