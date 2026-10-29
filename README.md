# Machine Coding Round 1

Each exercise lives on its own branch. Check out only the branch you were assigned:

```bash
git clone -b <branch> git@github.com:rootstock-tech-org/machine-coding-round1.git
```

| Branch | Exercise | Focus | Time |
|---|---|---|---|
| `q1-async-ingestion` | Async Media Ingestion Service | Async concurrency, signed URLs, retries, testing async code | ~3 h |
| `q2-price-alert-engine` | Price Alert Engine | LLD, OOP, SOLID, stock quote vendor integration, SQLite | ~3 h |
| `q3-llm-doc-pipeline` | LLM Document Pipeline at Scale | Rate limits, chunking, resumability, cost control | ~3–4 h |
| `q4-order-matching-engine` | Order Matching Engine | OOP, data structures, invariants, event log in SQLite | ~3 h |
| `q5-durable-job-queue` | Durable Job Queue on SQLite | Async workers, leases, retries, crash recovery | ~3 h |

Each branch has its own `README.md` with the full brief, rules, setup and what to submit.

## General rules

- Python 3.11+.
- Don't modify provided mocks, vendor SDKs or scripts. Add any files and tests you like.
- Docs, search and AI assistants are allowed. Be ready to explain every line in the follow-up call.
- Commit as you go; we read the history.
