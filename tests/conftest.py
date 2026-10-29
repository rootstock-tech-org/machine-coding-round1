import pytest

from ingestion.retry import RetryPolicy
from ingestion.service import IngestionService
from tests.fakes import FakeDownloader, FakeNotifier, FakeStorage


async def _no_sleep(_: float) -> None:
    return None


@pytest.fixture
def make_service():
    """Build an IngestionService wired with fakes; override any piece by keyword."""

    def factory(*, storage=None, downloader=None, notifier=None,
                concurrency=5, per_file_timeout=5.0):
        storage = storage or FakeStorage()
        downloader = downloader or FakeDownloader()
        notifier = notifier or FakeNotifier()
        retry = RetryPolicy(max_attempts=3, base_delay=0.0, max_delay=0.0, sleep=_no_sleep)
        service = IngestionService(
            storage, downloader, notifier, retry,
            concurrency=concurrency, per_file_timeout=per_file_timeout,
        )
        return service, storage, downloader, notifier

    return factory
