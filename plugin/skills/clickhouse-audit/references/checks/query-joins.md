# query-joins

**Rule IDs:** `query-join-choose-algorithm`, `query-join-use-any`, `query-join-filter-before`, `query-join-consider-alternatives`, `query-join-null-handling`
**Area:** Query efficiency
**Severity:** HIGH
**Evidence:** Workload queries 1–3 (sample query, max memory), DDL

## Trigger

- A top pattern contains a join and its `max_memory_bytes` is the highest in the workload.
- More than 3–4 joins.
- The largest table is on the right.
- `join_use_nulls = 1` with no semantic need.
- A regular join where `ANY` would do.

## Why it matters

The right side is built in memory. Join order and algorithm decide whether the query fits or spills.

## False positives

- Two-table joins are automatically reordered.
- `parallel_hash` is usually the right default.
- `join_use_nulls = 1` can be deliberate for outer joins.

## Fix

- Filter both sides first.
- Put the largest table on the left.
- Use `ANY` when one match is enough.
- Use a dictionary for small dimensions.
- Set `join_algorithm = 'auto'` only when OOM is a risk.

## Effort

Low for query rewrites. Medium for dictionaries.
