# schema-order-by

**Rule IDs:** `schema-pk-plan-before-creation`, `schema-pk-cardinality-order`, `schema-pk-prioritize-filters`, `schema-pk-filter-on-orderby`
**Area:** Schema
**Severity:** CRITICAL
**Evidence:** Inventory query 3 (`sorting_key`, `primary_key`), deep dive (granules), workload query 1 (filter columns in sample queries)

## Trigger

Any of:

- `sorting_key` is empty or `tuple()`.
- The leading key column is a UUID, a microsecond timestamp, or another high-cardinality column, and top queries filter on a lower-cardinality column.
- The key has more than 5 columns.
- A column used in the `WHERE` clause of the top patterns is absent from the key and has no skip index.

## Why it matters

The ordering key is the single highest-leverage design choice. It drives granule pruning and compression. When it does not match real filters, every hot query reads far more data than it returns.

## False positives

- If every query filters on timestamp, leading with the timestamp is correct.
- A key that looks wrong but prunes well in `EXPLAIN` is not a finding. Measured evidence wins.
- Low-volume tables may not justify a rewrite.

## Fix

Propose a new ordering key aligned to the top filters: low cardinality first, then time. Show the `CREATE TABLE ... ORDER BY (...)` diff, the backfill plan, and a before/after `EXPLAIN indexes = 1` measurement. Never propose changing the key in place; it requires a new table and backfill.

## Effort

High.
