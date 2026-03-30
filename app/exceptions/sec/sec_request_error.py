class SecRequestError(Exception):
    def __init__(
        self,
        detail: str = "SEC service request failed",
        *,
        status_code: int = 502,
        upstream_status_code: int | None = None,
        upstream_url: str | None = None,
        upstream_message: str | None = None,
    ) -> None:
        self.detail: str = detail
        self.status_code: int = status_code
        self.upstream_status_code: int | None = upstream_status_code
        self.upstream_url: str | None = upstream_url
        self.upstream_message: str | None = upstream_message
        super().__init__(detail)
