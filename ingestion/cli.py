"""Composition root: wires real clients into the service. This file is provided.

Usage (with the mock server running):
    python -m ingestion.cli --all
    python -m ingestion.cli vid-001 vid-002 vid-404
"""

import argparse
import asyncio
import time

import httpx

from ingestion.clients import HttpDownloader, HttpStorageProvider, WebhookNotifier
from ingestion.retry import RetryPolicy
from ingestion.service import IngestionService


async def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Ingest files from the storage service.")
    parser.add_argument("file_ids", nargs="*")
    parser.add_argument("--all", action="store_true", help="ingest every file the storage lists")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-key", default="dev-key")
    parser.add_argument("--concurrency", type=int, default=5)
    args = parser.parse_args(argv)

    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        file_ids = list(args.file_ids)
        if args.all:
            resp = await client.get(f"{args.base_url}/storage/files")
            resp.raise_for_status()
            file_ids += resp.json()["files"]

        service = IngestionService(
            storage=HttpStorageProvider(client, args.base_url, args.api_key),
            downloader=HttpDownloader(client),
            notifier=WebhookNotifier(client, f"{args.base_url}/webhook"),
            retry=RetryPolicy(max_attempts=4, base_delay=0.2, max_delay=3.0),
            concurrency=args.concurrency,
        )

        started = time.perf_counter()
        report = await service.ingest(file_ids)
        elapsed = time.perf_counter() - started

    for r in report.results:
        status = f"ok  {r.checksum[:12]}" if r.ok else f"ERR {r.error}"
        print(f"{r.file_id:<10} {status}")
    print(f"\n{len(report.succeeded)} ok, {len(report.failed)} failed in {elapsed:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
