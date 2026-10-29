"""Generate a random command stream for load testing. DO NOT MODIFY.

    python scripts/generate_orders.py --n 100000 --seed 1 > big.jsonl

Mix: ~70% limit orders clustered around a mid price, ~10% market orders,
~15% cancels and ~5% modifies of earlier orders (some already filled, so
expect rejections), across 5 symbols.
"""

import argparse
import json
import random
import sys

SYMBOLS = {"TCS": 4100, "INFY": 1850, "RELIANCE": 2950, "SBIN": 820, "ITC": 460}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    ids: list[str] = []
    out = sys.stdout
    for i in range(args.n):
        roll = rng.random()
        if roll < 0.15 and ids:
            cmd = {"type": "CANCEL", "id": rng.choice(ids)}
        elif roll < 0.20 and ids:
            cmd = {"type": "MODIFY", "id": rng.choice(ids), "qty": rng.randint(1, 50)}
        else:
            symbol = rng.choice(list(SYMBOLS))
            order_id = f"o{i}"
            cmd = {"type": "NEW", "id": order_id, "symbol": symbol,
                   "side": rng.choice(["BUY", "SELL"]), "qty": rng.randint(1, 100)}
            if roll < 0.30:
                cmd["order_type"] = "MARKET"
            else:
                ticks = round(rng.gauss(0, 40))
                cmd["order_type"] = "LIMIT"
                cmd["price"] = f"{SYMBOLS[symbol] + ticks * 0.05:.2f}"
                ids.append(order_id)
        out.write(json.dumps(cmd) + "\n")


if __name__ == "__main__":
    main()
