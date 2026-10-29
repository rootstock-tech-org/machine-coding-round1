from tests.fakes import FakeDownloader, FakeStorage, sha256_of

# These are a starting point, not full coverage. Add your own tests -- see the
# README for behaviours that are required but not tested here.


async def test_happy_path(make_service):
    service, _, _, notifier = make_service()
    report = await service.ingest(["a", "b"])

    assert report.succeeded == ["a", "b"]
    assert report.checksum_of("a") == sha256_of("a")
    assert sorted(notifier.sent) == [("a", sha256_of("a")), ("b", sha256_of("b"))]


async def test_results_preserve_input_order(make_service):
    ids = [f"f{i}" for i in range(10)]
    service, *_ = make_service(downloader=FakeDownloader(delay=0.001), concurrency=4)
    report = await service.ingest(ids)
    assert [r.file_id for r in report.results] == ids


async def test_one_failure_does_not_break_others(make_service):
    service, _, _, notifier = make_service(storage=FakeStorage(missing={"b"}))
    report = await service.ingest(["a", "b", "c"])

    assert report.succeeded == ["a", "c"]
    assert "b" in report.failed
    assert {fid for fid, _ in notifier.sent} == {"a", "c"}


async def test_refreshes_signed_url_on_expiry(make_service):
    service, storage, downloader, _ = make_service(downloader=FakeDownloader(expire_first={"a"}))
    report = await service.ingest(["a"])

    assert report.succeeded == ["a"]
    assert storage.calls.count("a") == 2
    assert len(downloader.urls) == 2 and downloader.urls[0] != downloader.urls[1]


async def test_concurrency_limit_is_respected(make_service):
    downloader = FakeDownloader(delay=0.01)
    service, *_ = make_service(downloader=downloader, concurrency=3)
    await service.ingest([f"f{i}" for i in range(10)])

    assert 1 < downloader.peak <= 3
