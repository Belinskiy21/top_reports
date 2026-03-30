from typing import Protocol


class HtmlRendererProtocol(Protocol):
    def write_pdf(self, target: str) -> bytes | None: ...
