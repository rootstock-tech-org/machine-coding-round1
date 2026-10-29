"""Acceptance test for the fixed CLI interface. DO NOT MODIFY -- add your own tests next to it.

What the worked example exercises, line by line (examples/basic.jsonl):
  b1  crosses two price levels: best price first (s3 @ 99.50), then time priority (s1 before s2)
  s1  MODIFY to a smaller qty keeps time priority, so b2 fills s1 before s2
  b2  MARKET order walks the book
  s2  CANCEL of a partly filled order
  b3  REJECTED: 100.03 is not a multiple of the 0.05 tick
  b4  MARKET order with no liquidity -> CANCELLED, no trade
  b1  CANCEL of a filled order -> REJECTED
  s4  trades at the RESTING price (98.00), not its own 97.00, then rests
  b6  books are per symbol
"""

import json
import subprocess
import sys
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def run_engine(commands: Path) -> list[dict]:
    result = subprocess.run(
        [sys.executable, "-m", "matching", str(commands)],
        capture_output=True, text=True, timeout=30, check=True,
    )
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def test_basic_example_trades():
    events = run_engine(EXAMPLES / "basic.jsonl")
    trades = [e for e in events if e["event"] == "TRADE"]
    expected = [json.loads(line) for line in (EXAMPLES / "basic_trades.jsonl").read_text().splitlines()]
    assert trades == expected


def test_basic_example_rejections_and_cancels():
    events = run_engine(EXAMPLES / "basic.jsonl")
    rejected = {e["id"] for e in events if e["event"] == "REJECTED"}
    cancelled = {e["id"]: e["remaining"] for e in events if e["event"] == "CANCELLED"}
    assert rejected == {"b3", "b1"}
    assert cancelled == {"s2": 2, "b4": 1}
