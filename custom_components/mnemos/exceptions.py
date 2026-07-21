from __future__ import annotations


class MnemosError(Exception):
    pass


class MnemosConnectionError(MnemosError):
    pass


class MnemosAuthError(MnemosError):
    pass


class MnemosApiError(MnemosError):

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(f"HTTP {status}: {detail}")
        self.status = status
        self.detail = detail


class MnemosUnsupportedMedia(MnemosError):
    pass