# Order Matching Engine: Machine Coding Exercise

## Context

Build the core of a stock exchange: a limit order book that matches buy and
sell orders by **price-time priority**, records every trade in SQLite, and can
rebuild itself exactly after a restart.

There is no skeleton beyond the empty `matching/` package. **You design the
classes, modules and data structures.** We are evaluating:

- **OOP:** a clear domain model, encapsulation and invariants that can't be broken.
- **Data structures:** the right complexity for each operation, justified.
- **SOLID:** new order types without rewriting the matcher.
- **Persistence:** an append-only event log in SQLite, and an exact replay from it.
- **Testing:** scenario tests plus randomised invariant checks.

---

## Steps to complete

- [ ] Set up: `pip install -e ".[dev]"`, then `pytest -q`. `tests/test_examples.py` fails at first.
- [ ] Design the domain model and the data structures inside `matching/`. Prices are `Decimal`.
- [ ] Create `matching/__main__.py`, which reads commands from a file and prints one event per line, in the format given below.
- [ ] Implement price-time matching, partial fills, market orders, cancel, modify and validation.
- [ ] Get `pytest -q tests/test_examples.py` passing.
- [ ] Add the SQLite event log (`--db`) and replay on startup.
- [ ] Add at least one of `IOC` or `FOK` without rewriting the matching loop.
- [ ] Write scenario tests, a randomised invariant test and a replay test.
- [ ] Measure throughput with `python scripts/generate_orders.py --n 100000 > big.jsonl`, then `time python -m matching big.jsonl > /dev/null`.
- [ ] Fill in `DESIGN.md`, including the complexity table and your throughput, and commit as you go.

---

## Time & rules

- **Time box: about 3 hours.** Note in `DESIGN.md` what you would do next.
- Python 3.11+, **standard library only** plus `pytest`.
- **Don't modify** `examples/`, `scripts/` or `tests/test_examples.py`.
- You may use docs, search and AI assistants. Be ready to explain every line.

## Setup

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest          # tests/test_examples.py fails until the engine works
```

---

## Interface (fixed, so we can run your code)

```bash
python -m matching <commands.jsonl> [--db engine.db]
```

The program reads one command per line and writes **one event per line to stdout**, in the order the events happen.

### Commands

```json
{"type": "NEW", "id": "o1", "symbol": "TCS", "side": "BUY", "order_type": "LIMIT", "qty": 10, "price": "100.00"}
{"type": "NEW", "id": "o2", "symbol": "TCS", "side": "SELL", "order_type": "MARKET", "qty": 5}
{"type": "CANCEL", "id": "o1"}
{"type": "MODIFY", "id": "o1", "qty": 4, "price": "100.05"}
```

- `qty` in `MODIFY` is the new **remaining** quantity. `price` is optional.
- Prices are strings; parse them as `Decimal`.

### Events

```json
{"event": "ACCEPTED", "id": "o1"}
{"event": "REJECTED", "id": "o9", "reason": "price not a multiple of tick 0.05"}
{"event": "TRADE", "symbol": "TCS", "buy_id": "o1", "sell_id": "o2", "price": "100.00", "qty": 5}
{"event": "FILLED", "id": "o2"}
{"event": "CANCELLED", "id": "o1", "remaining": 5}
{"event": "MODIFIED", "id": "o1", "qty": 4, "price": "100.05"}
```

Prices in events are formatted with exactly two decimal places.

---

## Matching rules

1. **Price-time priority:** the best price matches first; at the same price, the earliest order matches first.
2. **Trade price** is always the price of the **resting** order.
3. **Partial fills** are allowed. A limit order's unfilled remainder rests in the book.
4. A **market order** fills what it can. Any remainder is `CANCELLED`, and market orders never rest.
5. `MODIFY`: reducing quantity at the same price **keeps** time priority.
   Changing the price or increasing quantity **loses** it, and the order may match immediately.
6. **Validation:** a price must be a positive multiple of **0.05**, a quantity a positive
   integer, and ids unique. Cancelling or modifying an unknown or finished order is `REJECTED` with a reason.
7. Each symbol has its own independent book.

### Invariants (must hold after every command)

- The book is never crossed: best bid < best ask for every symbol.
- For every order, the filled quantity plus the remaining quantity plus the cancelled quantity equals the original quantity.

`examples/basic.jsonl` and `examples/basic_trades.jsonl` show a worked scenario covering most of these rules.

---

## Requirements

1. **Domain model:** orders, trades, price levels, books and events. Money is never a float.
2. **Data structures:** best price, add, cancel by id and match must all be efficient.
   State the complexity of each operation in `DESIGN.md` and justify your choice.
3. **Persistence (SQLite):** with `--db`, every accepted command and the events it produced are written
   to an append-only log. **Restart = replay**: starting with an existing database rebuilds exactly the same
   books before new commands are processed. The domain layer must not import `sqlite3`.
4. **Queries** (a Python API is enough): top of book, depth for N price levels per side, and an order's status.
5. **Extensibility:** adding `IOC` (immediate-or-cancel) or `FOK` (fill-or-kill) must not
   require rewriting the matching loop. Implement **at least one** of them.
6. **Performance:** `python scripts/generate_orders.py --n 100000 > big.jsonl`, then
   report your throughput in orders per second in `DESIGN.md`.
7. **Tests:**
   - a scenario test for each rule
   - a **randomised** test that checks both invariants after every command
   - a test that replay produces the same book as a live run

### Stretch (optional)
- Self-trade prevention: two orders with the same `account` field must never trade with each other.
- Stop orders.
- Snapshots, so replay doesn't start from the beginning of the log.

---

## What to submit

- A zip or private repo **with git history**, without `.venv/` or `*.db` files.
- `DESIGN.md` filled in.
- Output of `pytest -q` and your throughput number.

## Follow-up call (45 min)

You'll walk us through your design, then we'll add a new order type together live.
