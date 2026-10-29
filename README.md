# Async Media Ingestion Service

## Context

Users upload videos to our object storage. A downstream system needs to know
when each file is safely ingested and what its checksum is. You'll build the
Python service that does this:

```
for each file_id:
    storage API  ──►  short-lived signed URL
    CDN          ──►  download (streamed)  ──►  sha256
    webhook      ──►  {"file_id", "checksum"}
```

The external services are **unreliable on purpose**. They are slow, they rate-limit
you, they return 5xx errors, signed URLs expire after a few seconds, and the
webhook sometimes processes a request and then "loses" the response. A local
mock of all three is included, so you don't need any accounts or network access.

We care more about **how you structure and reason about the code** than about
finishing every task. A clean, well-tested subset beats a rushed, complete one.

---

## Time & rules

- **Time box: about 3 hours.** Stop when the time is up and write down in
  `NOTES.md` what you would do next.
- Python **3.11+**.
- **Don't modify** `mock_server/`, `ingestion/errors.py`, `ingestion/models.py`,
  `ingestion/interfaces.py`, or the existing tests. You may add files, tests,
  fakes and helpers freely.
- Dependencies: anything you add must be listed in `pyproject.toml`, with a
  one-line justification in `NOTES.md`.
- You may use docs, search and AI assistants. Be ready to explain every line
  in the follow-up call.

---

## Setup

```bash
python3.11 -m venv .venv && source .venv/bin/activate   # or 3.12 / 3.13
pip install -e ".[dev]"

pytest                       # provided tests fail until you implement the tasks
```

End-to-end run (after Tasks 1–4), using two terminals:

```bash
# terminal 1: the mock external services
uvicorn mock_server.app:app --port 8000

# terminal 2: your service
python -m ingestion.cli --all
curl -s localhost:8000/_debug/state | python -m json.tool   # check your results
curl -s -X POST localhost:8000/_debug/reset                   # clear webhook state
```

Make the mock harsher or reproducible with environment variables on the
server, e.g. `MOCK_URL_TTL=2 MOCK_FAILURE_RATE=0.3 MOCK_SEED=7 uvicorn ...`.

---

## Project layout

```
ingestion/
  errors.py       provided  exception hierarchy used across layers
  models.py       provided  FileResult / Report
  interfaces.py   provided  StorageProvider, Downloader, Notifier protocols
  signing.py      TASK 1    HMAC signed URLs
  retry.py        TASK 2    retry with exponential backoff + jitter
  service.py      TASK 3    async orchestrator (the core of the exercise)
  clients.py      TASK 4    httpx implementations + error mapping
  cli.py          provided  wires everything together
mock_server/app.py provided mock storage API, CDN and webhook (don't modify)
tests/
  fakes.py        provided  in-memory test doubles
  test_*.py       provided  starter tests. Add your own.
NOTES.md          you       design notes, trade-offs, what's next
```

---

## Tasks

The docstrings in each file contain the exact specification. Read them first.

### Task 1: Signed URLs (`ingestion/signing.py`)
Implement `sign_url` and `verify_url` with HMAC-SHA256 from the standard library.
The mock server uses your module, so **the end-to-end run depends on this task**.
`tests/test_signing.py` must pass.

### Task 2: Retry policy (`ingestion/retry.py`)
Exponential backoff with full jitter that retries only transient errors and
honours `Retry-After`. Time and randomness are injected, so the tests never
actually sleep. `tests/test_retry.py` must pass.

### Task 3: Ingestion service (`ingestion/service.py`), the core task
Implement `IngestionService.ingest`. Its docstring lists 8 requirements:
bounded concurrency, failure isolation, ordered results, retries, signed-URL
refresh, streaming hashes, per-file timeouts and correct cancellation.
`tests/test_service.py` covers only some of them.

### Task 4: HTTP clients (`ingestion/clients.py`)
Implement the three httpx clients and map HTTP and transport failures to the
exceptions in `errors.py`. Then run the CLI against the mock server.

### Task 5: Tests
Add tests for the behaviour that isn't covered yet. At minimum:
- per-file timeout
- cancellation of `ingest()`
- permanent errors are not retried
- the HTTP clients' error mapping (`respx` is installed for mocking httpx)

Tests must be **fast and deterministic**: no real network and no real sleeping
for more than a few milliseconds.

### Stretch (optional, pick any)
- Use structured logging or metrics without spreading them through the
  business logic.
- Add a second notifier (e.g. a Slack message) next to the webhook without
  changing `IngestionService`.
- Add a global rate limit (requests/sec) shared across all workers.

---

## External API reference (mock server)

Base URL: `http://127.0.0.1:8000`. API key: `dev-key`.

| Endpoint | Success | Failures you must handle |
|---|---|---|
| `GET /storage/files` | `{"files": ["vid-001", ...]}` | none |
| `POST /storage/files/{id}/signed-url` with header `Authorization: Bearer <key>` | `{"url": "<signed url>"}` | `401`, `404` (`vid-404` doesn't exist), `429` + `Retry-After`, `503` |
| `GET <signed url>` | streamed bytes | `403 {"error": "expired"}`, `403 {"error": "invalid_signature"}`, `404`, `429`, `503`, slow responses |
| `POST /webhook` with JSON `{"file_id", "checksum"}`, optional header `Idempotency-Key` | `{"status": "ok"}` or `{"status": "duplicate"}` | `429`, `503`, `502` (**the request may already have been processed**) |
| `GET /_debug/state` | expected checksums, webhook deliveries, duplicates, expired-URL count | for your own verification |

Signed URLs expire **5 seconds** after they are issued by default.

---

## What to submit

1. A zip of the repo or a link to a private git repo, **with git history**.
   Commit as you go; we read the history.
2. `NOTES.md` filled in.
3. Output of `pytest -q`, plus one CLI run and the `/_debug/state` response
   that follows it (paste them into `NOTES.md`).

Please don't include `.venv/`.

## How we evaluate

- **Correctness under failure**: does it behave well when the services misbehave?
- **Async reasoning**: concurrency, cancellation, timeouts, no blocking calls.
- **Design**: clear responsibilities, dependencies on abstractions, easy to extend.
- **Tests**: meaningful, fast, deterministic.
- **Communication**: your notes and how you explain trade-offs.

## Follow-up call (45 min)

We'll walk through your code together, discuss trade-offs, and then extend it
live with a small change.
