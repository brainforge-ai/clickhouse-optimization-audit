# Inventory (pass 1)

Metadata only. No user rows. Run in this order and keep the results for the analysis.

## 1. Version, timezone, host

```sql
/* bf_audit */
SELECT version() AS version, timezone() AS timezone, hostName() AS host
LIMIT 1
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## 2. Cluster name (decides the query_log source)

```sql
/* bf_audit */
SELECT cluster, shard_num, replica_num, host_name
FROM system.clusters
LIMIT 50
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

If the result has a `default` cluster, read `system.query_log` through `clusterAllReplicas('default', system.query_log)`. Otherwise use `system.query_log` and record a partial-workload gap.

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
LIMIT 300
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

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
LIMIT 3000
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

If the result is larger than the context can hold, rerun filtered to the 20 largest tables by `total_bytes` from query 3.

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
LIMIT 300
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
LIMIT 300
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## 8. Projections

```sql
/* bf_audit */
SELECT database, table, name, type
FROM system.projections
LIMIT 300
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
