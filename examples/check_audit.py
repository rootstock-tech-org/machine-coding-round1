"""Check a stress run for overlapping, lost and dead-lettered jobs. DO NOT MODIFY.

    python -m examples.check_audit --db jobs.db

Run it after all workers have drained the queue.
"""

import argparse
import json
from collections import defaultdict

from examples.audit import runs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="jobs.db")
    args = parser.parse_args()

    with open(f"{args.db}.expected.json") as f:
        expected: dict[str, list[int]] = json.load(f)
    by_job: dict[int, list] = defaultdict(list)
    for n, run_id, started, finished, outcome in runs(args.db):
        by_job[n].append((started, finished, outcome))

    overlaps = []
    for n, job_runs in by_job.items():
        ordered = sorted(job_runs)
        for (s1, f1, _), (s2, _, _) in zip(ordered, ordered[1:]):
            if f1 is not None and s2 < f1:
                overlaps.append(n)
                break

    must_succeed = expected["send_email"] + expected["flaky"] + expected["slow"]
    never_succeeded = [n for n in must_succeed if not any(o == "ok" for *_, o in by_job.get(n, []))]
    poison_runs = [len(by_job.get(n, [])) for n in expected["poison"]]
    total_runs = sum(len(r) for r in by_job.values())

    print(f"jobs expected:            {sum(len(v) for v in expected.values())}")
    print(f"handler runs recorded:    {total_runs}")
    print(f"jobs run concurrently:    {len(overlaps)}  {overlaps[:10]}")
    print(f"jobs never succeeded:     {len(never_succeeded)}  {never_succeeded[:10]}")
    print(f"poison jobs:              {len(expected['poison'])} "
          f"(attempts each: min {min(poison_runs, default=0)}, max {max(poison_runs, default=0)})")
    ok = not overlaps and not never_succeeded
    print("\nRESULT:", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
