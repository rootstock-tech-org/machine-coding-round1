"""Error types shared across the ingestion package.

HTTP clients translate transport / status-code failures into these, so the
service layer never needs to know about httpx or HTTP status codes.

This file is provided. You may add to it, but keep the existing classes.
"""


class IngestionError(Exception):
    """Base class for all *expected* ingestion failures."""


class TransientError(IngestionError):
    """Temporary failure (5xx, 429, timeout, connection reset). Safe to retry.

    `retry_after` is the server-suggested wait in seconds (e.g. from a
    `Retry-After` header), or None if the server gave no hint.
    """

    def __init__(self, message: str = "", retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class PermanentError(IngestionError):
    """Failure that will not succeed on retry (e.g. 400, 401, 404, bad signature)."""


class UrlExpired(IngestionError):
    """The signed URL is past its expiry.

    Retrying the *same* URL will never succeed -- a fresh URL is needed.
    """
