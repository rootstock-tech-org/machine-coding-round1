"""Mock of the external services. DO NOT MODIFY.

Simulates a storage API, a CDN serving signed URLs and a downstream webhook --
including latency, rate limiting, 5xx errors and lost acknowledgements.

Run:  uvicorn mock_server.app:app --port 8000

Tunable via environment variables:
    MOCK_URL_TTL        signed URL lifetime in seconds        (default 5)
    MOCK_FAILURE_RATE   share of requests that fail randomly  (default 0.15)
    MOCK_LATENCY        "min,max" download latency in seconds (default "0.2,1.5")
    MOCK_SEED           random seed for reproducible runs     (default unset)
"""

import asyncio
import hashlib
import os
import random

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse, StreamingResponse

from ingestion import signing

API_KEY = os.getenv("MOCK_API_KEY", "dev-key")
SECRET = os.getenv("MOCK_SIGNING_SECRET", "dev-secret").encode()
URL_TTL = int(os.getenv("MOCK_URL_TTL", "5"))
FAILURE_RATE = float(os.getenv("MOCK_FAILURE_RATE", "0.15"))
LATENCY = tuple(float(x) for x in os.getenv("MOCK_LATENCY", "0.2,1.5").split(","))

_seed = os.getenv("MOCK_SEED")
rng = random.Random(int(_seed) if _seed else None)

# 30 files between 64 KiB and ~1.3 MiB. "vid-404" is deliberately missing.
FILES: dict[str, int] = {f"vid-{i:03d}": ((i * 37) % 20 + 1) * 64 * 1024 for i in range(1, 31)}

webhook_received: dict[str, dict] = {}
stats = {"webhook_duplicates": 0, "expired_urls_rejected": 0}

app = FastAPI(title="Mock external services")


def _block(file_id: str) -> bytes:
    return hashlib.sha256(file_id.encode()).digest() * 2048  # 64 KiB


async def _file_chunks(file_id: str):
    block, remaining = _block(file_id), FILES[file_id]
    while remaining > 0:
        n = min(len(block), remaining)
        yield block[:n]
        remaining -= n
        await asyncio.sleep(0)


def _expected_sha256(file_id: str) -> str:
    h, block, remaining = hashlib.sha256(), _block(file_id), FILES[file_id]
    while remaining > 0:
        n = min(len(block), remaining)
        h.update(block[:n])
        remaining -= n
    return h.hexdigest()


def _random_failure() -> JSONResponse | None:
    r = rng.random()
    if r < FAILURE_RATE / 2:
        return JSONResponse({"error": "service_unavailable"}, status_code=503)
    if r < FAILURE_RATE:
        return JSONResponse({"error": "rate_limited"}, status_code=429, headers={"Retry-After": "1"})
    return None


# ---------------------------------------------------------------- storage API


@app.get("/storage/files")
async def list_files():
    return {"files": [*FILES, "vid-404"]}


@app.post("/storage/files/{file_id}/signed-url")
async def create_signed_url(file_id: str, request: Request,
                            authorization: str | None = Header(None)):
    if authorization != f"Bearer {API_KEY}":
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    if failure := _random_failure():
        return failure
    if file_id not in FILES:
        return JSONResponse({"error": "not_found"}, status_code=404)
    return {"url": signing.sign_url(str(request.base_url).rstrip("/"), f"/files/{file_id}", SECRET, URL_TTL)}


# ------------------------------------------------------------------------ CDN


@app.get("/files/{file_id}")
async def download(file_id: str, request: Request):
    await asyncio.sleep(rng.uniform(*LATENCY))  # queueing / network latency

    verdict = signing.verify_url(str(request.url), SECRET)
    if verdict is signing.Verdict.INVALID:
        return JSONResponse({"error": "invalid_signature"}, status_code=403)
    if verdict is signing.Verdict.EXPIRED:
        stats["expired_urls_rejected"] += 1
        return JSONResponse({"error": "expired"}, status_code=403)
    if failure := _random_failure():
        return failure
    if file_id not in FILES:
        return JSONResponse({"error": "not_found"}, status_code=404)
    return StreamingResponse(
        _file_chunks(file_id),
        media_type="application/octet-stream",
        headers={"Content-Length": str(FILES[file_id])},
    )


# -------------------------------------------------------------------- webhook


@app.post("/webhook")
async def webhook(payload: dict, idempotency_key: str | None = Header(None)):
    if failure := _random_failure():
        return failure
    key = idempotency_key or f"no-key-{len(webhook_received)}-{rng.random()}"
    if key in webhook_received:
        stats["webhook_duplicates"] += 1
        return {"status": "duplicate"}
    webhook_received[key] = payload
    if rng.random() < FAILURE_RATE / 2:
        # Processed, but the ack is "lost": the client sees a 502 and may retry.
        return JSONResponse({"error": "bad_gateway"}, status_code=502)
    return {"status": "ok"}


# ---------------------------------------------------------- debug / grading


@app.get("/_debug/state")
async def debug_state():
    """Expected checksums, what the webhook received, and counters."""
    received = list(webhook_received.values())
    per_file: dict[str, int] = {}
    for p in received:
        per_file[p.get("file_id", "?")] = per_file.get(p.get("file_id", "?"), 0) + 1
    return {
        "expected_checksums": {fid: _expected_sha256(fid) for fid in FILES},
        "webhook_deliveries": len(received),
        "files_delivered_more_than_once": [f for f, n in per_file.items() if n > 1],
        "wrong_checksums": [
            p["file_id"]
            for p in received
            if p.get("file_id") in FILES and p.get("checksum") != _expected_sha256(p["file_id"])
        ],
        **stats,
    }


@app.post("/_debug/reset")
async def debug_reset():
    webhook_received.clear()
    stats.update(webhook_duplicates=0, expired_urls_rejected=0)
    return {"status": "reset"}
