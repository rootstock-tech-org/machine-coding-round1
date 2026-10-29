"""Demo handlers for the stress check. DO NOT MODIFY.

Every handler records when it starts and finishes in a separate audit table, so
`examples.check_audit` can detect overlapping runs and lost jobs. Payloads carry
a unique "n" per job.
"""

import asyncio
import os
import random

from examples.audit import record, starts
from jobq import Queue

DB = os.environ.get("JOBQ_DB", "jobs.db")
queue = Queue(DB, lease_seconds=5)


async def _audited(payload: dict, work) -> None:
    run = record(DB, payload["n"], "start")
    try:
        await work()
    except BaseException:
        record(DB, payload["n"], "error", run)
        raise
    record(DB, payload["n"], "ok", run)


@queue.handler("send_email")
async def send_email(payload: dict) -> None:
    await _audited(payload, lambda: asyncio.sleep(random.uniform(0.01, 0.1)))


@queue.handler("flaky")
async def flaky(payload: dict) -> None:
    # Fails on its first two attempts, then succeeds.
    async def work():
        await asyncio.sleep(random.uniform(0.01, 0.1))
        if starts(DB, payload["n"]) <= 2:
            raise RuntimeError("flaky failure")
    await _audited(payload, work)


@queue.handler("slow")
async def slow(payload: dict) -> None:
    # Runs longer than the 5s lease: only survives if heartbeats extend it.
    await _audited(payload, lambda: asyncio.sleep(8))


@queue.handler("poison")
async def poison(payload: dict) -> None:
    async def work():
        raise ValueError("this job can never succeed")
    await _audited(payload, work)
