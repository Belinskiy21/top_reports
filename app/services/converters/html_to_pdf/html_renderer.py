from typing import Protocol


class HtmlRenderer(Protocol):
    def write_pdf(self, target: str) -> bytes | None: ...
