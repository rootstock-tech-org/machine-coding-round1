# Design

## Time spent
<!-- roughly, per area -->

## Components
<!-- Mermaid or ASCII: Queue, registry, worker, storage, scheduler... and who depends on whom. -->

```mermaid
classDiagram
```

## Job lifecycle
<!-- States and allowed transitions, including retries and dead-lettering. -->

```mermaid
stateDiagram-v2
```

## Schema
<!-- Tables, indexes, and why. -->

## Claiming, leases & fencing
<!-- The exact SQL/transaction for a claim. How heartbeats work. What stops a stale worker. -->

## Async + SQLite
<!-- sqlite3 is blocking: how do you keep the event loop responsive? Connections per thread/process? -->

## Delivery guarantee
<!-- At-most-once, at-least-once or exactly-once? Why, and what does that require of handlers? -->

## SOLID in this codebase
| Principle | Where / how (or why deliberately not) |
|---|---|
| Single responsibility | |
| Open/closed | |
| Liskov substitution | |
| Interface segregation | |
| Dependency inversion | |

## Questions
1. A handler charges a credit card, then the worker dies before acknowledging. What happens? How should the handler be written?
2. What changes if the storage moves to Postgres?
3. What is the throughput ceiling of this design, and what limits it?
4. How did you prevent starvation of low-priority jobs?

## Stress check output
```
# python -m examples.check_audit --db jobs.db
```

## Known limitations / what I'd do with more time
<!-- -->
