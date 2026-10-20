# architecture-joins

**Rule IDs:** `query-join-choose-algorithm`, `query-join-use-any`, `query-join-filter-before`, `query-join-consider-alternatives`, `query-join-null-handling`, `architecture-advisor:decision-join-enrichment`
**Area:** Architecture / Queries
**Severity:** CRITICAL when join memory is the top memory consumer; HIGH otherwise
**Evidence:** Workload queries 1–3 (sample query, max memory), inventory query 3 (engines), DDL for dictionaries

## Trigger

- Top patterns contain `JOIN` and dominate `max_memory_bytes`.
- More than 3–4 joins in one query.
- The large table is on the right side of the join.
- `join_use_nulls = 1` where defaults would do.
- A small dimension is joined repeatedly instead of using a dictionary.

## Why it matters

Joins build the right side in memory. The wrong order, the wrong algorithm, or a missing dictionary turns a cheap lookup into a memory spike and a slow query.

## False positives

- Two-table joins are automatically reordered in recent versions.
- `parallel_hash` is the default and is usually correct.
- A join may be required for correctness when dimensions are large and change often.

## Fix

- Filter both sides before joining.
- Put the largest table on the left.
- Use `ANY JOIN` when one match is enough.
- Replace small dimension lookups with a dictionary.
- Denormalize hot paths into one table.
- Set `join_algorithm = 'auto'` only when OOM is a risk.

## Effort

Low for query rewrites. Medium for dictionaries. High for denormalization.
