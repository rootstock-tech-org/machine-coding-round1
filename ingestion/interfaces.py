"""Abstractions the ingestion service depends on. This file is provided.

The service must depend only on these protocols -- never on httpx, a concrete
storage vendor, or the mock server. Real implementations live in clients.py;
test doubles live in tests/fakes.py.

Every implementation must signal failures using the exceptions in errors.py.
"""

from collections.abc import AsyncIterator
from typing import Protocol


class StorageProvider(Protocol):
    async def get_signed_url(self, file_id: str) -> str:
        """Return a short-lived signed download URL for `file_id`.

        Raises PermanentError if the file does not exist,
        TransientError on temporary failures.
        """
        ...


class Downloader(Protocol):
    def stream(self, url: str) -> AsyncIterator[bytes]:
        """Yield the file's bytes in chunks.

        Raises UrlExpired if the URL has expired, TransientError on temporary
        failures, PermanentError otherwise.
        """
        ...


class Notifier(Protocol):
    async def notify(self, file_id: str, checksum: str) -> None:
        """Report a successfully processed file to the downstream system.

        May be called more than once for the same file (e.g. after a retry);
        implementations must make that safe.
        """
        ...
