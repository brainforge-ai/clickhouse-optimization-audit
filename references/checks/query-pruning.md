# query-pruning

**Rule IDs:** `schema-pk-filter-on-orderby`, `query-index-skipping-indices`
**Area:** Queries
**Severity:** CRITICAL
**Evidence:** Deep dive (granules read vs total), workload query 8 (pruning proxy), workload query 1 (sample queries)

## Trigger

- `Granules: read/total` above 0.5 for a top pattern.
- `read_rows / result_rows` above 100 on a selective query.
- The query filters on a column that is not a key prefix and has no skip index.

## Why it matters

Reading granules that cannot contain the answer is pure waste. It is the most common cause of a query that is “slow for no reason”.

## False positives

- A deliberately broad aggregation over most of the table.
- A filter with low selectivity where most granules genuinely match.
- `read_rows` includes rows read before `PREWHERE`; compare with the `EXPLAIN` output.

## Fix

- Add the filter column to the ordering key (new table + backfill).
- Or add a skip index when the key cannot change.
- Rewrite the predicate so it uses the key prefix, without wrapping the key column in a function.

## Effort

Low for a query rewrite. Medium for a skip index. High for a key change.
