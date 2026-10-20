# query-patterns

**Rule IDs:** `playbook:3.6-write-fast-queries`, `query-join-filter-before`
**Area:** Queries
**Severity:** HIGH
**Evidence:** Workload query 1 (`sample_query`, read/result ratio)

## Trigger

Any of the following in a top pattern:

- `SELECT *`.
- `LIMIT` without `ORDER BY`.
- A function wrapped around a key column in `WHERE`, such as `toDate(ts) = ...`.
- A wide scan where only a few columns are returned.
- The same normalized query repeated at high frequency with a high read volume.
- A filter applied after a join that could be applied before it.

## Why it matters

Columnar storage reads only referenced columns. `SELECT *` defeats that. Functions on key columns defeat pruning. Repeated identical heavy queries are a pre-computation candidate.

## False positives

- `SELECT *` in an ad-hoc exploration query that runs once.
- `LIMIT` without `ORDER BY` when any rows are acceptable.
- A function on a key column when the key is not used for pruning anyway.

## Fix

- Select only needed columns.
- Rewrite `toDate(ts) = today()` as `ts >= today() AND ts < today() + 1`.
- Filter before joining.
- For repeated heavy aggregations, see `precomputation-mv.md` and `precomputation-projections.md`.

## Effort

Low.
