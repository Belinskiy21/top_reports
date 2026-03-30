import os
from typing import cast
from urllib.parse import urljoin

import httpx

SEC_BASE_URL = "https://www.sec.gov/"
SEC_DATA_BASE_URL = "https://data.sec.gov/"
COMPANY_TICKERS_URL = urljoin(SEC_BASE_URL, "files/company_tickers.json")
DEFAULT_SEC_USER_AGENT = "top-reports sec-contact@your-domain.com"


class SecClient:
    def __init__(self) -> None:
        self._client: httpx.AsyncClient = httpx.AsyncClient(timeout=30.0)
        self._default_user_agent: str = os.getenv("SEC_USER_AGENT", DEFAULT_SEC_USER_AGENT)

    async def get_submissions(self, cik: str) -> dict[str, object]:
        response = await self._client.get(
            urljoin(SEC_DATA_BASE_URL, f"submissions/CIK{cik}.json"),
            headers=self._headers(),
        )
        _ = response.raise_for_status()
        return cast(dict[str, object], response.json())

    async def download_file(self, url: str) -> bytes:
        response = await self._client.get(url, headers=self._headers())
        _ = response.raise_for_status()
        return response.content

    def _headers(self) -> dict[str, str]:
        return {
            "User-Agent": self._default_user_agent,
            "Accept-Encoding": "gzip, deflate",
        }
