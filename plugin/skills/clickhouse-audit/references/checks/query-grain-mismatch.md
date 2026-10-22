# query-grain-mismatch

**Rule IDs:** `playbook:grain-mismatch`, `playbook:materialized-view-not-used`
**Area:** Query efficiency
**Severity:** HIGH when the pattern reads more than 100 GB per day
**Evidence:** Workload queries 1 and 4, inventory of MVs, aggregate tables and projections

## Trigger

A query groups a base table when an aggregated table, materialized view or projection already answers the same grain.

1. List what already exists:

```sql
/* bf_audit */
SELECT database, name, engine, sorting_key, as_select
FROM system.tables
WHERE engine IN ('AggregatingMergeTree', 'SummingMergeTree', 'ReplacingMergeTree', 'MaterializedView')
  AND database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA', '_temporary_and_external_tables')
LIMIT 2000
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

```sql
/* bf_audit */
SELECT database, table, name, type
FROM system.projections
LIMIT 2000
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

2. Find repeated aggregations on base tables. The time filter below is a 7-day example; for the default full-history run, drop the `event_date` line.

```sql
/* bf_audit */
SELECT
  normalized_query_hash,
  any(query) AS sample,
  count() AS runs,
  sum(read_bytes) AS read_bytes,
  formatReadableSize(sum(read_bytes)) AS readable_read,
  any(tables) AS tables
FROM clusterAllReplicas('<cluster>', system.query_log)
WHERE event_date >= today() - 7
  AND type = 'QueryFinish'
  AND is_initial_query = 1
  AND query_kind = 'Select'
  AND query NOT LIKE '%bf_audit%'
  AND positionCaseInsensitive(query, 'GROUP BY') > 0
GROUP BY normalized_query_hash
ORDER BY read_bytes DESC
LIMIT 100
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

3. Compare. For each top pattern, read its `GROUP BY` columns and the dimensions of the aggregate table or view. If the query's dimensions are a subset, and the view covers the time range the query needs, it is a finding.

## Why it matters

Reading the base grain to recompute a number that already exists is the most common ClickHouse waste. It costs read bytes on every run and adds latency the aggregate already removed.

## False positives

- The aggregate does not cover the query's time range or filters.
- The query needs a column the aggregate does not store.
- The aggregate is refreshed on a schedule the query cannot tolerate.
- A projection exists but the optimizer did not use it because the query shape differs.

## Fix

- Point the query at the aggregate table, or add the missing dimension to it.
- If the pattern is new and repeated, propose a materialized view at that grain.
- If a projection exists, check `EXPLAIN indexes = 1` to see why it was not used.

## Effort

Low to repoint a query. Medium to add a materialized view or projection.
