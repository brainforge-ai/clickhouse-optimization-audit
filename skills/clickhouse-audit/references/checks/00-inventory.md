# Inventory (pass 1)

Metadata only. No user rows. Run in this order and keep the results for the analysis.

**Scope is the full service.** Every user database, table and column is in scope. Do not sample.

**Completeness rule.** Every list query below is a page, not a sample. Read the preflight counts first, then page with a keyset filter until your rows match the counts. If any page fails or a count cannot be reconciled, record a gap. A partial inventory is never a clean pass.

## 0. Preflight counts (run first)

```sql
/* bf_audit */
SELECT
  (SELECT count() FROM system.tables
     WHERE database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA', '_temporary_and_external_tables')) AS tables,
  (SELECT count() FROM system.columns
     WHERE database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA', '_temporary_and_external_tables')) AS columns,
  (SELECT count() FROM system.parts
     WHERE active AND database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA', '_temporary_and_external_tables')) AS parts
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

```sql
/* bf_audit */
SELECT name, value FROM system.settings WHERE name = 'log_queries'
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

Record the three counts. They are the expected row counts for sections 3, 4 and 5. If `log_queries` is `0`, the workload profile cannot run; stop and report that as the finding, not as a clean service.

If the MCP accepts `SHOW GRANTS`, run it and record the role. A read-only role is expected.

## 1. Version, timezone, host

```sql
/* bf_audit */
SELECT version() AS version, timezone() AS timezone, hostName() AS host
LIMIT 1
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## 1b. Log coverage

```sql
/* bf_audit */
SELECT
  min(event_time) AS first_query,
  max(event_time) AS last_query,
  count() AS rows
FROM system.query_log
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

```sql
/* bf_audit */
SELECT min(event_time) AS first_part_event, max(event_time) AS last_part_event
FROM system.part_log
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

Set `scope.window_start` and `scope.window_end` from the measured query_log range. When the requested window is longer than the log, report the measured range and the shortfall in the gaps. Never state a window the log cannot support.

## 2. Cluster name (decides the query_log source)

```sql
/* bf_audit */
SELECT cluster, shard_num, replica_num, host_name
FROM system.clusters
LIMIT 50
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

Record the cluster name as `<cluster>`. Every workload query substitutes it into `clusterAllReplicas('<cluster>', system.query_log)`. If the list is empty, read `system.query_log` directly and record a partial-workload gap.

## 3. Tables

```sql
/* bf_audit */
SELECT
  database,
  name,
  engine,
  sorting_key,
  primary_key,
  partition_key,
  total_rows,
  total_bytes,
  formatReadableSize(total_bytes) AS readable_size,
  positionCaseInsensitive(create_table_query, 'TTL') > 0 AS has_ttl,
  engine IN ('View', 'MaterializedView', 'LiveView', 'WindowView') AS is_view,
  substring(as_select, 1, 2000) AS view_select
FROM system.tables
WHERE database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA', '_temporary_and_external_tables')
ORDER BY total_bytes DESC
LIMIT 5000
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

If the rows equal the preflight table count, the list is complete. If it equals the limit, page with `AND (database, name) > ('<last_database>', '<last_name>')` until the count matches. Never treat a capped list as the inventory.

## 4. Columns

```sql
/* bf_audit */
SELECT
  database,
  table,
  name,
  type,
  position,
  data_compressed_bytes,
  data_uncompressed_bytes,
  round(data_uncompressed_bytes / greatest(data_compressed_bytes, 1), 2) AS compression_ratio,
  compression_codec,
  is_in_sorting_key,
  is_in_primary_key,
  is_in_partition_key
FROM system.columns
WHERE database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA', '_temporary_and_external_tables')
ORDER BY database, table, position
LIMIT 20000
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

Compare the row count with the preflight column count. If it is short, page by database: `AND database = '<db>'` for each database, then by table. If the result is too large for context, keep per-table aggregates (nullable count, type classes) and fetch individual columns only for tables that produce findings. Record which tables were aggregated instead of listed.

## 5. Active parts

```sql
/* bf_audit */
SELECT
  database,
  table,
  count() AS active_parts,
  uniqExact(partition) AS partitions,
  sum(rows) AS rows,
  sum(bytes_on_disk) AS bytes_on_disk,
  sum(data_uncompressed_bytes) AS bytes_uncompressed,
  round(sum(data_uncompressed_bytes) / greatest(sum(bytes_on_disk), 1), 2) AS compression_ratio
FROM system.parts
WHERE active
  AND database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA', '_temporary_and_external_tables')
GROUP BY database, table
ORDER BY bytes_on_disk DESC
LIMIT 5000
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## 6. Merge pressure

```sql
/* bf_audit */
SELECT
  database,
  table,
  count() AS active_merges,
  max(elapsed) AS max_elapsed_seconds,
  round(avg(progress), 3) AS avg_progress,
  sum(rows_read) AS rows_read,
  sum(bytes_read) AS bytes_read
FROM system.merges
GROUP BY database, table
ORDER BY active_merges DESC
LIMIT 200
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## 7. Skipping indices

```sql
/* bf_audit */
SELECT database, table, name, type, expr, granularity
FROM system.data_skipping_indices
LIMIT 5000
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## 8. Projections

```sql
/* bf_audit */
SELECT database, table, name, type
FROM system.projections
LIMIT 5000
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

If `system.projections` is unavailable, record a gap and continue.

## 9. DDL for the tables that produce findings

```sql
/* bf_audit */
SELECT database, name, create_table_query
FROM system.tables
WHERE database = '<db>' AND name IN ('<table1>', '<table2>')
LIMIT 20
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

Use this only after findings are known, and only for those tables. Redact literals before showing any DDL.
