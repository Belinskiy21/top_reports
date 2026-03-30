from collections.abc import Callable
from typing import Protocol

from app.services.converters.html_to_pdf.html_renderer_protocol import (
    HtmlRendererProtocol,
)

type UrlFetcher = Callable[[str], dict[str, object]]


class HtmlRendererFactoryProtocol(Protocol):
    def __call__(
        self,
        *,
        filename: str,
        base_url: str,
        url_fetcher: UrlFetcher | None = None,
    ) -> HtmlRendererProtocol: ...
