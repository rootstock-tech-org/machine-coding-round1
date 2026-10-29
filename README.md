# Durable Job Queue on SQLite: Machine Coding Exercise

## Context

Build a small background job system, a mini Celery, backed by a single
SQLite file. Application code enqueues jobs. Async worker processes claim and
run them, retry failures with backoff, move poison jobs to a dead-letter
queue, and recover when a worker is killed mid-job.

There is no skeleton beyond the empty `jobq/` package. **You design the
classes and modules.** The public API and CLI below are fixed, so we can run
your code. We are evaluating:

- **Async correctness:** a worker pool, heartbeats, graceful shutdown, no blocked event loop.
- **Concurrency between processes:** two workers never run the same job at the same time.
- **Persistence:** schema, transactions, locking, crash recovery.
- **LLD / SOLID:** handlers plug in without touching the worker; the storage layer is swappable.
- **Testing:** deterministic tests for retries, leases and crashes.

---

## Steps to complete

- [ ] Set up: `pip install -e ".[dev]"`, then `pytest -q`.
- [ ] In `jobq/__init__.py`, export `Queue` with `enqueue()` and the `@queue.handler(...)` decorator, matching the fixed API below.
- [ ] Design the schema and the job states, and make enqueue idempotent.
- [ ] Implement atomic claiming with leases, heartbeats and a fencing token.
- [ ] Add retries with backoff, dead-lettering, `run_at` and priority with anti-starvation.
- [ ] Create `jobq/__main__.py` with the `worker` and `status` commands, including graceful shutdown on SIGTERM.
- [ ] Write the tests listed under requirement 9, with an injected clock, and get `pytest -q` passing.
- [ ] Run the stress check: `python -m examples.load --db jobs.db --n 500`, then start two workers, `kill -9` one of them part-way and restart it.
- [ ] Run `python -m examples.check_audit --db jobs.db`. It must print `RESULT: PASS`.
- [ ] Fill in `DESIGN.md` and commit as you go.

---

## Time & rules

- **Time box: about 3 hours.** Note in `DESIGN.md` what you would do next.
- Python 3.11+, **standard library only** (`asyncio`, `sqlite3`, ...) plus `pytest` and `pytest-asyncio`.
- **Don't modify** `examples/`.
- You may use docs, search and AI assistants. Be ready to explain every line.

## Setup

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

---

## Public API (fixed)

```python
from jobq import Queue

queue = Queue("jobs.db", lease_seconds=30)

@queue.handler("send_email")
async def send_email(payload: dict) -> None:
    ...

job_id = queue.enqueue(
    "send_email", {"to": "a@example.com"},
    run_at=None,            # datetime; None = now
    priority=0,             # higher runs first
    max_attempts=5,
    idempotency_key=None,   # same key -> same job, enqueued only once
)
```

`enqueue` is a normal (sync) function, so web request handlers can call it.
A handler succeeds by returning, and fails by raising.

## CLI (fixed)

```bash
python -m jobq worker --db jobs.db --app examples.demo_app --concurrency 8
python -m jobq status --db jobs.db
```

`--app` is a module path. Importing it registers the handlers on the `queue` object defined in that module.
`status` prints counts per state, the age of the oldest waiting job and the dead-letter size.

---

## Requirements

1. **Claiming:** a worker claims a job atomically and gets a lease (`lease_seconds`).
   Two workers, even in different processes, must never run the same job at the same time.
2. **Heartbeats:** a running job's lease is extended periodically. A worker that has
   **lost** its lease, because it stalled and the lease expired, must not be able to
   mark the job succeeded or failed. Use a fencing token or attempt id.
3. **Retries:** a failed job is retried with exponential backoff and jitter. After
   `max_attempts` it moves to the **dead-letter** state, keeping its last error and traceback.
4. **Crash recovery:** if a worker is killed with `kill -9` mid-job, the job runs again
   once its lease expires. No job is ever lost.
5. **Scheduling & priority:** a job never runs before `run_at`. Higher priority runs
   first, but a low-priority job must not wait forever. Explain your anti-starvation rule.
6. **Idempotent enqueue:** enqueueing with the same `idempotency_key` returns the existing job id.
7. **Graceful shutdown:** on SIGTERM or Ctrl-C, stop claiming new jobs, let in-flight jobs
   finish within a grace period (10s), and release the leases of anything still unfinished.
8. **Unknown job type:** a job whose type has no registered handler must not crash the worker.
   Decide what happens to it and justify the decision.
9. **Tests**, covering at least:
   - backoff schedule and dead-lettering (with an injected clock, no real sleeps)
   - lease expiry and reclaim after a simulated crash
   - a stale worker can't complete a job it no longer owns
   - idempotent enqueue
   - priority ordering and `run_at`
   - graceful shutdown

## Stress check (provided)

`examples/` contains a demo app and tools to check your queue end to end:

```bash
python -m examples.load --db jobs.db --n 500        # enqueue a mixed workload
python -m jobq worker --db jobs.db --app examples.demo_app --concurrency 8 &
python -m jobq worker --db jobs.db --app examples.demo_app --concurrency 8 &
#   ...kill -9 one of the workers part-way through, then start it again...
python -m examples.check_audit --db jobs.db         # overlaps, lost jobs, dead letters
```

`check_audit` reports any job that ran **at the same time** in two places, any
job that never ran successfully, and how many ended up dead-lettered (only the
`poison` jobs should).

### Stretch (optional)
- A concurrency limit per job type, e.g. at most 2 `video_transcode` jobs at once across all workers.
- Recurring jobs ("every 5 minutes").
- A `retry <job_id>` command that moves a dead-lettered job back to the queue.

---

## What to submit

- A zip or private repo **with git history**, without `.venv/` or `*.db` files.
- `DESIGN.md` filled in.
- Output of `pytest -q` and of `check_audit` after a run where you killed a worker.

## Follow-up call (45 min)

You'll walk us through your design, then we'll discuss moving it to Postgres and add a small feature live.
