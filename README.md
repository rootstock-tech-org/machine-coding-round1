# Price Alert Engine: Low-Level Design Exercise

## Context

Our trading app lets users set price alerts, such as *"tell me when TCS goes
above ₹4,200"*. You'll design and build the core engine: a domain model,
integration with two market-data vendors, persistence in SQLite, and
notifications.

This is a **low-level design** exercise. There is no skeleton beyond the vendor
SDKs: **you decide the classes, modules and interfaces.** We are evaluating:

- **OOP:** sensible entities, value objects, encapsulation and invariants.
- **SOLID:** where it genuinely helps, not abstraction for its own sake.
- **Integration:** turning two inconsistent third-party APIs into one clean model.
- **Persistence:** schema design, transactions, keeping the domain free of SQL.
- **Testing:** fast and deterministic, with no real time and no real vendors.

---

## Time & rules

- **Time box: about 3 hours.** Note in `DESIGN.md` what you would do next.
- Python 3.11+, **standard library only** (`sqlite3`, `decimal`, `dataclasses`,
  ...) plus `pytest`. No ORMs or frameworks; we want to see your design.
- **Don't modify `vendors/`.** Treat them as third-party code you can't change.
- You may use docs, search and AI assistants. Be ready to explain every line.

## Setup

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

---

## Requirements

### 1. Alerts
A user can **create**, **list** and **cancel** alerts. There are three alert types:

| Type | Fires when | Example |
|---|---|---|
| `PRICE_ABOVE` | price ≥ target | TCS ≥ ₹4,200.00 |
| `PRICE_BELOW` | price ≤ target | SBIN ≤ ₹800.00 |
| `PERCENT_MOVE` | \|price − reference\| / reference ≥ p%, where reference is the price **when the alert was created** | INFY moves 2% either way |

- Lifecycle: `ACTIVE → TRIGGERED`, or `ACTIVE → CANCELLED`. An alert fires
  **at most once**. Triggered or cancelled alerts can't be cancelled or
  re-triggered. Enforce this **in the domain model**, not just in the database.
- When an alert triggers, record the trigger price, the time and the vendor that supplied the quote.
- Money is **never a float**.

### 2. Market data
Two vendor SDKs are provided in `vendors/`. Read their docstrings carefully;
they differ in almost everything:

| | `AlphaClient` (primary) | `BetaMarketsClient` (fallback) |
|---|---|---|
| Symbol format | `TCS` | `NSE:TCS` |
| Price | int paise | decimal string, rupees |
| Timestamp | epoch int | ISO-8601 with offset |
| Batch size | up to 3 symbols | 1 instrument |
| Failures | `AlphaError(429/503)` | `BetaTimeout`, stale ticks |
| Coverage | no `WIPRO` | no `ITC` |

- Your engine must work with **one internal quote model**, and the rest of the
  code must not know which vendor a quote came from.
- Use Alpha first. Fall back to Beta per symbol if Alpha fails or doesn't cover the symbol.
- **Reject quotes older than 60 seconds.** A stale quote must never trigger an alert.
- Adding a third vendor later must not require changing the engine.

### 3. Persistence (SQLite)
- Alerts and their state survive a process restart.
- Design the schema yourself. Commit it as SQL, applied at startup.
- The domain layer must not import `sqlite3`.
- Tests should use `:memory:` or a temporary file.

### 4. Evaluation & notifications
- `run_once()`: fetch quotes for every symbol that has an active alert, using
  as few vendor calls as possible, evaluate the alerts, trigger them and notify
  the user.
- Notification channels: start with a **console** channel and an **in-memory**
  channel for tests. Each alert names its channel. Adding e.g. email or push
  later must not change the engine.
- **Reliability:** if the process crashes after an alert is marked `TRIGGERED`
  but before the notification is sent, the notification must still be sent on
  the next run. Under normal operation, it must not be sent twice.
  (Hint: think about what has to happen inside one transaction.)

### 5. Tests
Cover at least the following:
- Each alert type, including the exact-boundary price.
- Illegal state transitions.
- Vendor normalisation: paise → rupees, symbol mapping, timezones.
- Fallback to Beta when Alpha fails or lacks the symbol.
- A stale quote doesn't trigger an alert.
- The crash-recovery scenario from requirement 4.
- Persistence round-trip.

Inject time (a clock) and vendor clients. **No test should depend on real
time, randomness or vendor latency.**

### 6. `DESIGN.md`
Fill in the provided template: a class diagram (Mermaid or ASCII), where each
SOLID principle shows up in your code (or why you deliberately didn't apply it),
and the questions it lists.

### Stretch (optional)
- `TRAILING_STOP` alert: fires when the price falls p% below the highest price seen since creation.
- A small CLI: `create`, `list`, `cancel`, `run --every 5s`.
- Two engine processes running against the same database: how do you avoid double-triggering?

---

## What to submit

- A zip or private repo **with git history**, without `.venv/`.
- `DESIGN.md` filled in.
- Output of `pytest -q`.

## Follow-up call (45 min)

You'll walk us through your design, then we'll add a new requirement together live.
