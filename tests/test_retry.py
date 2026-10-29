import pytest

from ingestion.errors import PermanentError, TransientError, UrlExpired
from ingestion.retry import RetryPolicy


class FakeSleep:
    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


def failing(times: int, exc: Exception, result="ok"):
    calls = {"n": 0}

    async def fn():
        calls["n"] += 1
        if calls["n"] <= times:
            raise exc
        return result

    return fn, calls


def policy(sleep, **kw):
    kw.setdefault("max_attempts", 3)
    return RetryPolicy(base_delay=1.0, max_delay=10.0, sleep=sleep, rand=lambda: 0.5, **kw)


async def test_returns_first_success():
    sleep = FakeSleep()
    fn, calls = failing(0, TransientError())
    assert await policy(sleep).run(fn) == "ok"
    assert calls["n"] == 1 and sleep.delays == []


async def test_retries_transient_with_backoff_and_jitter():
    sleep = FakeSleep()
    fn, calls = failing(2, TransientError("503"))
    assert await policy(sleep).run(fn) == "ok"
    assert calls["n"] == 3
    assert sleep.delays == [0.5, 1.0]  # 0.5 * 1, 0.5 * 2


async def test_gives_up_after_max_attempts():
    sleep = FakeSleep()
    fn, calls = failing(99, TransientError("503"))
    with pytest.raises(TransientError):
        await policy(sleep).run(fn)
    assert calls["n"] == 3 and len(sleep.delays) == 2


async def test_does_not_retry_permanent_errors():
    fn, calls = failing(99, PermanentError("404"))
    with pytest.raises(PermanentError):
        await policy(FakeSleep()).run(fn)
    assert calls["n"] == 1


async def test_does_not_retry_url_expired():
    fn, calls = failing(99, UrlExpired("old url"))
    with pytest.raises(UrlExpired):
        await policy(FakeSleep()).run(fn)
    assert calls["n"] == 1


async def test_respects_retry_after():
    sleep = FakeSleep()
    fn, _ = failing(1, TransientError("429", retry_after=2.0))
    await policy(sleep).run(fn)
    assert sleep.delays == [2.0]
