"""The ingestion orchestrator.                                  >>> TASK 3 <<<"""

from ingestion.interfaces import Downloader, Notifier, StorageProvider
from ingestion.models import Report
from ingestion.retry import RetryPolicy


class IngestionService:
    """For each file id: get a signed URL -> download -> sha256 -> notify.

    Requirements:
    1. Process files concurrently, with at most `concurrency` files in flight.
    2. One file failing must never stop or fail the others.
    3. `ingest` returns a Report with exactly one FileResult per input id,
       in the same order as the input.
    4. Retry transient failures (use `self._retry`); do not retry permanent ones.
    5. If a download fails with UrlExpired, get a fresh URL and try again
       (at most once more).
    6. Stream the download and hash it incrementally; don't hold whole files
       in memory.
    7. A single file taking longer than `per_file_timeout` seconds is marked as
       failed with an error mentioning "timeout".
    8. Cancelling `ingest()` must cancel the in-flight work (don't swallow
       asyncio.CancelledError).
    """

    def __init__(
        self,
        storage: StorageProvider,
        downloader: Downloader,
        notifier: Notifier,
        retry: RetryPolicy,
        *,
        concurrency: int = 5,
        per_file_timeout: float = 60.0,
    ) -> None:
        self._storage = storage
        self._downloader = downloader
        self._notifier = notifier
        self._retry = retry
        self._concurrency = concurrency
        self._per_file_timeout = per_file_timeout

    async def ingest(self, file_ids: list[str]) -> Report:
        raise NotImplementedError
