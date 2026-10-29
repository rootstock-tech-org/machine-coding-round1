# LLM Document Pipeline: Large-Scale Extraction Exercise

## Context

Finance receives millions of supplier invoices as text files. We want to
extract five fields from each one using an LLM:

| Field | Format |
|---|---|
| `invoice_number` | as printed, e.g. `INV-2041337` |
| `vendor` | as printed |
| `invoice_date` | `YYYY-MM-DD` |
| `currency` | ISO code, e.g. `INR` |
| `total` | decimal string, no thousands separators, e.g. `12345.60` |

LLM calls are **slow, rate-limited, billed per token, limited by a context
window and sometimes wrong**. Real corpora are messy. Build a pipeline that is
correct, cheap, resumable, and that you could credibly scale up.

You get:
- `llm_sdk/`: a **mock LLM provider SDK**. It runs locally, needs no key and
  costs nothing, but it behaves like the real thing: rate limits, context
  window, 500 errors, malformed JSON and billing.
  **Read its docstring.**
- `scripts/generate_corpus.py`: generates a corpus of invoices plus the
  correct answers.
- `scripts/score.py`: measures your accuracy against those answers.

There is no skeleton for the pipeline itself. **You design the classes and
modules.** We look at OOP and SOLID design, async correctness and engineering
judgement as much as at accuracy.

---

## Time & rules

- **Time box: about 3–4 hours.** Note in `DESIGN.md` what you would do next.
- Python 3.11+, **standard library only** (`asyncio`, `sqlite3`, `hashlib`, ...)
  plus `pytest` and `pytest-asyncio`.
- **Don't modify** `llm_sdk/` or `scripts/`. Treat them as third-party code.
- Call the LLM **only** through `llm_sdk.LLMClient`, and keep its default limits.
- You may use docs, search and AI assistants. Be ready to explain every line.

## Setup

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
python scripts/generate_corpus.py --n 300 --out corpus --answers answers.jsonl
```

---

## Requirements

### 1. CLI
```bash
python -m docpipe run    corpus/ --db state.db [--max-cost-usd 0.50]
python -m docpipe status          --db state.db
python -m docpipe export          --db state.db --out results.jsonl
python scripts/score.py --results results.jsonl --answers answers.jsonl
```
`export` writes one line per input file in the format described in `scripts/score.py`.

### 2. Throughput within provider limits
- Process documents concurrently with `asyncio`.
- Stay within the provider's **requests/min, tokens/min and concurrency** limits
  **proactively**. Treat 429s as a safety net, not your flow control.
- Retry transient failures with backoff. Never retry what can't succeed.

### 3. Long documents
Some invoices are bigger than the context window. Handle them so that the
fields are still extracted correctly. The vendor is on page 1, the total is on
the last page, and every page repeats the invoice number. Explain your chunking
and merge strategy in `DESIGN.md`.

### 4. Output quality
- Validate every LLM response against the schema above.
- Malformed or partial JSON gets a bounded recovery strategy, for example
  repairing it locally or re-prompting. After that the document is marked failed with a reason.
- Normalise values (dates, totals) to the formats above.

### 5. Resumability & persistence (SQLite)
- Track the state of every document in SQLite.
- If you `kill -9` the process mid-run, re-running `run` must **finish only the
  remaining work**. Documents that already completed must not be re-sent to the LLM.
- The database must never hold a half-written or inconsistent result.

### 6. Cost control
- Identical content (the same bytes under a different file name) is sent to the LLM **only once**.
- `--max-cost-usd`: stop starting new LLM work once the budget would be
  exceeded, let in-flight work finish, and report what's left.
- Report tokens and cost per run.

### 7. Bad input
Empty, binary or non-UTF-8 files are detected **before** any LLM call and
exported with an `error` reason. Decide whether some of them can still be
processed and justify the decision.

### 8. Tests
Fast and deterministic. **No real sleeping**, and the tests must not depend on
the SDK's randomness. Inject your own fake LLM client where useful. Cover at least:
- the rate limiter
- chunking and merging
- JSON recovery
- resume after a crash
- dedupe
- the budget stop

### 9. `DESIGN.md`
Fill in the template. It includes a **scale-out section**: the same pipeline at
5 million documents per day, on many machines, with two LLM providers.

### Stretch (optional)
- Version your prompts and store the version with each result, so you can
  re-run only the documents processed by an old prompt.
- Send a second LLM call only for low-confidence fields, and justify how you
  measure confidence.
- Add a `--workers N` mode with multiple processes sharing one SQLite database
  safely.

---

## What to submit

- A zip or private repo **with git history**, without `.venv/`, `corpus/` or the database.
- `DESIGN.md` filled in.
- Output of `pytest -q`, plus `run`, `status` and `score.py` on a 300-document corpus.

## Follow-up call (45 min)

You'll walk us through your design and the trade-offs, then we'll discuss how it scales.
