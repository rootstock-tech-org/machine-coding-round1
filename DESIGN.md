# Design

## Time spent
<!-- roughly, per area -->

## Architecture
<!-- Class / component diagram (Mermaid or ASCII). Which abstractions exist, and why? -->

```mermaid
classDiagram
```

## Document lifecycle & schema
<!-- States a document goes through, the tables, and how a crash at each step is recovered. -->

## Rate limiting & concurrency
<!-- How you stay under rpm / tpm / concurrency, and why that design. -->

## Long documents: chunking & merging
<!-- Chunk size, overlap, merge rules for conflicting values. -->

## Output validation & recovery
<!-- What counts as valid, what you repair locally, when you re-prompt, when you give up. -->

## Cost
<!-- Dedupe strategy, budget enforcement, cost per 1,000 documents on your run. -->

## SOLID in this codebase
| Principle | Where / how (or why deliberately not) |
|---|---|
| Single responsibility | |
| Open/closed | |
| Liskov substitution | |
| Interface segregation | |
| Dependency inversion | |

## Scale-out: 5M documents/day
1. What replaces SQLite and the single process? How is work distributed and claimed?
2. How do you share one provider rate limit across 50 workers?
3. A provider outage lasts 2 hours. What happens?
4. How do you safely re-process 5M documents with a new prompt version?
5. How do you know accuracy hasn't regressed? (evaluation set, sampling, alerts)
6. The invoices contain PII. What changes?

## Results
```
# pytest -q

# python -m docpipe run corpus/ --db state.db

# python -m docpipe status --db state.db

# python scripts/score.py ...
```

## Known limitations / what I'd do with more time
<!-- -->
