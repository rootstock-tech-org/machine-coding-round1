"""HTTP implementations of the interfaces.                     >>> TASK 4 <<<

Each client receives a shared `httpx.AsyncClient` (created once in cli.py) and
must translate HTTP / transport failures into the exceptions in errors.py:

    429, 5xx, timeouts, connection errors -> TransientError
                                             (carry Retry-After if present)
    403 with body {"error": "expired"}    -> UrlExpired
    any other 4xx                         -> PermanentError

See the "External API reference" section of the README for endpoints.
"""

from collections.abc import AsyncIterator

import httpx


class HttpStorageProvider:
    """POST {base_url}/storage/files/{file_id}/signed-url  ->  {"url": "..."}

    Requires header  `Authorization: Bearer <api_key>`.
    """

    def __init__(self, client: httpx.AsyncClient, base_url: str, api_key: str) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    async def get_signed_url(self, file_id: str) -> str:
        raise NotImplementedError


class HttpDownloader:
    """GET <signed url>  ->  streamed file bytes."""

    def __init__(self, client: httpx.AsyncClient, chunk_size: int = 64 * 1024) -> None:
        self._client = client
        self._chunk_size = chunk_size

    async def stream(self, url: str) -> AsyncIterator[bytes]:
        raise NotImplementedError
        yield b""  # makes this an async generator; remove when implementing


class WebhookNotifier:
    """POST {url}  with JSON {"file_id": ..., "checksum": ...}

    The webhook supports an `Idempotency-Key` header.
    """

    def __init__(self, client: httpx.AsyncClient, url: str) -> None:
        self._client = client
        self._url = url

    async def notify(self, file_id: str, checksum: str) -> None:
        raise NotImplementedError
