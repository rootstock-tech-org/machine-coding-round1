# Design

## Time spent
<!-- roughly, per area -->

## Class diagram
<!-- Mermaid or ASCII. Show entities, value objects, interfaces and who depends on whom. -->

```mermaid
classDiagram
```

## Module layout
<!-- which package/file owns what, and the direction of dependencies -->

## Schema
<!-- tables, keys, indexes, and why -->

## SOLID in this codebase
| Principle | Where / how (or why deliberately not) |
|---|---|
| Single responsibility | |
| Open/closed | |
| Liskov substitution | |
| Interface segregation | |
| Dependency inversion | |

## Questions
1. How do you add a new alert type? Which files change?
2. How do you add a third vendor? Which files change?
3. How does the crash-recovery guarantee work, step by step?
4. Where does money rounding happen, and why there?
5. What breaks first at 1M active alerts across 5,000 symbols, and how would you change the design?

## Known limitations / what I'd do with more time
<!-- -->
