# schema-skip-indexes

**Rule IDs:** `query-index-skipping-indices`, `schema-pk-filter-on-orderby`
**Area:** Schema / Queries
**Severity:** HIGH
**Evidence:** Inventory query 7, deep dive plan, workload filter columns

## Trigger

- A frequent filter column is not in the ordering key and has no skip index.
- A skip index exists but `EXPLAIN indexes = 1` does not show it being used.

## Why it matters

A skip index lets ClickHouse avoid granules for a non-key filter. It is the main alternative when the ordering key cannot change. An unused index is pure write and storage overhead.

## False positives

- Low-selectivity filters (most granules match) do not benefit.
- Small tables do not need one.
- The wrong index type (for example `minmax` on a high-cardinality column) may be skipped by the planner.

## Fix

Propose a `minmax`, `set`, or `bloom_filter` index on the filter column, or drop the unused index. Show the DDL and the `EXPLAIN` before/after.

## Effort

Low to add on a new table. Medium on an existing table.
