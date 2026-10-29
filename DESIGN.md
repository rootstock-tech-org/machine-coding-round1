# Design

## Time spent
<!-- roughly, per area -->

## Class diagram
<!-- Mermaid or ASCII: entities, value objects, events, interfaces, and who depends on whom. -->

```mermaid
classDiagram
```

## Data structures & complexity
| Operation | Structure used | Complexity | Why |
|---|---|---|---|
| Best bid / ask | | | |
| Add resting order | | | |
| Cancel by id | | | |
| Match one fill | | | |
| Depth (N levels) | | | |

## Event log & replay
<!-- Schema, what is written per command, what happens if the process dies mid-write. -->

## SOLID in this codebase
| Principle | Where / how (or why deliberately not) |
|---|---|
| Single responsibility | |
| Open/closed | |
| Liskov substitution | |
| Interface segregation | |
| Dependency inversion | |

## Questions
1. How do you add a new order type? Which files change?
2. How is `FOK` (or `IOC`) implemented, and how do you guarantee nothing partially executes for `FOK`?
3. Why do real exchanges run one thread per symbol? How would you scale to 5,000 symbols?
4. Your throughput was X orders/sec. What is the bottleneck, and what would you change first?

## Performance
```
# python scripts/generate_orders.py --n 100000 > big.jsonl
# time python -m matching big.jsonl > /dev/null
```

## Known limitations / what I'd do with more time
<!-- -->
