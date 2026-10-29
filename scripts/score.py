"""Score your results against the ground truth. DO NOT MODIFY.

    python scripts/score.py --results results.jsonl --answers answers.jsonl

results.jsonl: one JSON object per input file, e.g.
    {"file": "doc_000001.txt", "invoice_number": "INV-1234", "vendor": "...",
     "invoice_date": "2025-03-05", "currency": "INR", "total": "1234.50"}
    {"file": "doc_000002.txt", "error": "empty_file"}
"""

import argparse
import json
from decimal import Decimal, InvalidOperation

FIELDS = ["invoice_number", "vendor", "invoice_date", "currency", "total"]


def _same(field: str, got, want) -> bool:
    if got is None:
        return False
    if field == "total":
        try:
            return Decimal(str(got).replace(",", "")) == Decimal(want)
        except InvalidOperation:
            return False
    return str(got).strip() == want


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results.jsonl")
    parser.add_argument("--answers", default="answers.jsonl")
    args = parser.parse_args()

    answers = {a["file"]: a for a in map(json.loads, open(args.answers))}
    results = {r["file"]: r for r in map(json.loads, open(args.results))}

    missing = sorted(set(answers) - set(results))
    correct = {f: 0 for f in FIELDS}
    docs_ok = errors_ok = errors_expected = scored = 0
    for name, want in answers.items():
        got = results.get(name)
        if got is None:
            continue
        if want.get("expect_error"):
            errors_expected += 1
            errors_ok += "error" in got
            continue
        scored += 1
        hits = [_same(f, got.get(f), want[f]) for f in FIELDS]
        for f, hit in zip(FIELDS, hits):
            correct[f] += hit
        docs_ok += all(hits)

    print(f"files: {len(answers)}  results: {len(results)}  missing: {len(missing)}")
    for f in FIELDS:
        print(f"  {f:<15} {correct[f] / max(scored, 1):6.1%}")
    print(f"  {'all fields':<15} {docs_ok / max(scored, 1):6.1%}")
    print(f"  bad files flagged as errors: {errors_ok}/{errors_expected}")


if __name__ == "__main__":
    main()
