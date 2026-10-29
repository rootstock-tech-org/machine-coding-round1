"""Enqueue a mixed workload for the stress check. DO NOT MODIFY.

    python -m examples.load --db jobs.db --n 500

Mix: ~80% send_email, ~12% flaky, ~5% poison, ~3% slow; random priorities,
some scheduled a few seconds in the future, and a few repeated idempotency keys.
"""

import argparse
import json
import os
import random
from datetime import datetime, timedelta, timezone


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="jobs.db")
    parser.add_argument("--n", type=int, default=500)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    os.environ["JOBQ_DB"] = args.db
    from examples.demo_app import queue  # registers handlers on a Queue bound to --db

    rng = random.Random(args.seed)
    expected: dict[str, list[int]] = {"send_email": [], "flaky": [], "poison": [], "slow": []}
    for n in range(args.n):
        roll = rng.random()
        job_type = "send_email" if roll < 0.80 else "flaky" if roll < 0.92 else "poison" if roll < 0.97 else "slow"
        run_at = datetime.now(timezone.utc) + timedelta(seconds=rng.randint(1, 5)) if rng.random() < 0.1 else None
        queue.enqueue(job_type, {"n": n}, run_at=run_at, priority=rng.choice([0, 0, 0, 5, 10]),
                      max_attempts=5, idempotency_key=f"job-{n}")
        expected[job_type].append(n)

    # Re-enqueue some keys: these must NOT create new jobs.
    for n in rng.sample(range(args.n), k=min(20, args.n)):
        queue.enqueue("send_email", {"n": n}, idempotency_key=f"job-{n}")

    with open(f"{args.db}.expected.json", "w") as f:
        json.dump(expected, f)
    print(f"enqueued {args.n} jobs (+20 duplicate idempotency keys) into {args.db}")


if __name__ == "__main__":
    main()
