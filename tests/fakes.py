"""In-memory test doubles for the interfaces. Use them, extend them, add more."""

import asyncio
import hashlib

from ingestion.errors import PermanentError, TransientError, UrlExpired


def fid_from_url(url: str) -> str:
    return url.rsplit("/", 1)[-1].split("?", 1)[0]


def content_for(file_id: str) -> bytes:
    return f"content-of-{file_id}".encode()


def sha256_of(file_id: str) -> str:
    return hashlib.sha256(content_for(file_id)).hexdigest()


class FakeStorage:
    def __init__(self, *, missing=(), events: list | None = None) -> None:
        self.calls: list[str] = []
        self.missing = set(missing)
        self.events = events if events is not None else []

    async def get_signed_url(self, file_id: str) -> str:
        self.calls.append(file_id)
        self.events.append(("sign", file_id))
        if file_id in self.missing:
            raise PermanentError(f"{file_id} not found")
        return f"https://fake.local/files/{file_id}?v={len(self.calls)}"


class FakeDownloader:
    """
    expire_first: ids whose FIRST download raises UrlExpired
    errors:       id -> exception raised on every download of that id
    hang:         ids whose download never finishes
    delay:        seconds to wait before yielding (to create real overlap)
    """

    def __init__(self, *, expire_first=(), errors=None, hang=(), delay=0.0,
                 events: list | None = None) -> None:
        self.urls: list[str] = []
        self.expire_first = set(expire_first)
        self.errors = dict(errors or {})
        self.hang = set(hang)
        self.delay = delay
        self.events = events if events is not None else []
        self.active = 0
        self.peak = 0

    async def stream(self, url: str):
        fid = fid_from_url(url)
        self.urls.append(url)
        self.events.append(("download", fid))
        self.active += 1
        self.peak = max(self.peak, self.active)
        try:
            if fid in self.hang:
                await asyncio.Event().wait()
            if self.delay:
                await asyncio.sleep(self.delay)
            if fid in self.expire_first:
                self.expire_first.discard(fid)
                raise UrlExpired(url)
            if fid in self.errors:
                raise self.errors[fid]
            data = content_for(fid)
            for i in range(0, len(data), 4):
                yield data[i:i + 4]
        finally:
            self.active -= 1


class FakeNotifier:
    def __init__(self, *, transient_failures: dict[str, int] | None = None) -> None:
        self.sent: list[tuple[str, str]] = []
        self._failures = dict(transient_failures or {})

    async def notify(self, file_id: str, checksum: str) -> None:
        if self._failures.get(file_id, 0) > 0:
            self._failures[file_id] -= 1
            raise TransientError("webhook returned 503")
        self.sent.append((file_id, checksum))
