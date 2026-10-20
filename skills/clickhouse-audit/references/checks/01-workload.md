# Workload profile (pass 2)

Default window: 7 days. Replace `7` with the user's choice (`1`, `30`, or a custom number of days). For full history, drop the time predicate or start from the oldest retained `event_time`, and state the actual range in the report. Always read through `clusterAllReplicas('<cluster>', system.query_log)` when the cluster exists. Take `<cluster>` from the inventory (`system.clusters`). If no cluster is reported, drop the wrapper and record a partial-workload gap.

Every query excludes the audit's own statements with `query NOT LIKE '%bf_audit%'`.

## 1. Top patterns by read volume

```sql
/* bf_audit */
SELECT
  normalized_query_hash,
  any(substring(query, 1, 1200)) AS sample_query,
  count() AS executions,
  sum(read_bytes) AS read_bytes,
  sum(read_rows) AS read_rows,
  sum(result_rows) AS result_rows,
  round(avg(query_duration_ms), 1) AS avg_ms,
  round(quantile(0.95)(query_duration_ms), 1) AS p95_ms,
  max(memory_usage) AS max_memory_bytes
FROM clusterAllReplicas('<cluster>', system.query_log)
WHERE event_date >= today() - 7
  AND event_time >= now() - INTERVAL 7 DAY
  AND type = 'QueryFinish'
  AND is_initial_query = 1
  AND query_kind = 'Select'
  AND query NOT LIKE '%bf_audit%'
GROUP BY normalized_query_hash
ORDER BY read_bytes DESC
LIMIT 30
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## 2. Top patterns by duration

Same query as 1, `ORDER BY p95_ms DESC`, limit 20.

## 3. Top patterns by memory

Same query as 1, `ORDER BY max_memory_bytes DESC`, limit 20.

## 4. Hot tables

```sql
/* bf_audit */
SELECT
  arrayJoin(tables) AS table_name,
  count() AS reads,
  sum(read_bytes) AS read_bytes,
  sum(read_rows) AS read_rows
FROM clusterAllReplicas('<cluster>', system.query_log)
WHERE event_date >= today() - 7
  AND event_time >= now() - INTERVAL 7 DAY
  AND type = 'QueryFinish'
  AND is_initial_query = 1
  AND query_kind = 'Select'
  AND query NOT LIKE '%bf_audit%'
  AND notEmpty(tables)
GROUP BY table_name
ORDER BY read_bytes DESC
LIMIT 50
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## 5. Tables with no reads in the window

```sql
/* bf_audit */
SELECT
  t.database,
  t.name,
  t.total_rows,
  t.total_bytes,
  formatReadableSize(t.total_bytes) AS readable_size,
  q.last_read
FROM system.tables AS t
LEFT JOIN (
  SELECT arrayJoin(tables) AS tbl, max(event_time) AS last_read
  FROM clusterAllReplicas('<cluster>', system.query_log)
  WHERE event_date >= today() - 7
    AND event_time >= now() - INTERVAL 7 DAY
    AND type = 'QueryFinish'
    AND is_initial_query = 1
    AND query_kind = 'Select'
    AND query NOT LIKE '%bf_audit%'
    AND notEmpty(tables)
  GROUP BY tbl
) AS q ON concat(t.database, '.', t.name) = q.tbl
WHERE t.database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA', '_temporary_and_external_tables')
  AND t.engine NOT IN ('View', 'MaterializedView', 'LiveView', 'WindowView')
  AND (q.last_read IS NULL OR q.last_read < now() - INTERVAL 7 DAY)
ORDER BY t.total_bytes DESC
LIMIT 5000
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

This returns every unread table, not a sample. Add the totals in SQL so the report quotes one measured number:

```sql
/* bf_audit */
SELECT count() AS unread_tables, sum(t.total_bytes) AS unread_bytes, sum(t.total_rows) AS unread_rows
FROM system.tables AS t
LEFT JOIN (
  SELECT arrayJoin(tables) AS tbl
  FROM clusterAllReplicas('<cluster>', system.query_log)
  WHERE event_date >= today() - 7 AND event_time >= now() - INTERVAL 7 DAY
    AND type = 'QueryFinish' AND is_initial_query = 1 AND query_kind = 'Select'
    AND query NOT LIKE '%bf_audit%' AND notEmpty(tables)
  GROUP BY tbl
) AS q ON concat(t.database, '.', t.name) = q.tbl
WHERE t.database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA', '_temporary_and_external_tables')
  AND t.engine NOT IN ('View', 'MaterializedView', 'LiveView', 'WindowView')
  AND q.tbl IS NULL
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

False positives: table names that appear only through aliases or CTEs may not match, and `tables` can include subquery aliases. Confirm a zero-read table against the DDL or the user before calling it unused.

## 6. Insert cadence and batch size

```sql
/* bf_audit */
SELECT
  toStartOfHour(event_time) AS hour,
  count() AS inserts,
  sum(written_rows) AS rows_written,
  round(avg(written_rows), 0) AS avg_rows_per_insert,
  max(written_rows) AS max_rows_per_insert,
  sum(written_bytes) AS bytes_written
FROM clusterAllReplicas('<cluster>', system.query_log)
WHERE event_date >= today() - 7
  AND event_time >= now() - INTERVAL 7 DAY
  AND type = 'QueryFinish'
  AND is_initial_query = 1
  AND query_kind = 'Insert'
  AND query NOT LIKE '%bf_audit%'
GROUP BY hour
ORDER BY hour DESC
LIMIT 168
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## 7. Concurrency

```sql
/* bf_audit */
SELECT
  toStartOfMinute(event_time) AS minute,
  count() AS queries
FROM clusterAllReplicas('<cluster>', system.query_log)
WHERE event_date >= today() - 7
  AND event_time >= now() - INTERVAL 7 DAY
  AND type = 'QueryFinish'
  AND is_initial_query = 1
  AND query NOT LIKE '%bf_audit%'
GROUP BY minute
ORDER BY queries DESC
LIMIT 20
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## 8. Pruning proxy

```sql
/* bf_audit */
SELECT
  normalized_query_hash,
  any(substring(query, 1, 400)) AS sample_query,
  sum(read_rows) AS read_rows,
  sum(result_rows) AS result_rows,
  round(sum(read_rows) / greatest(sum(result_rows), 1), 1) AS read_per_result
FROM clusterAllReplicas('<cluster>', system.query_log)
WHERE event_date >= today() - 7
  AND event_time >= now() - INTERVAL 7 DAY
  AND type = 'QueryFinish'
  AND is_initial_query = 1
  AND query_kind = 'Select'
  AND query NOT LIKE '%bf_audit%'
GROUP BY normalized_query_hash
HAVING read_rows > 1000000
ORDER BY read_per_result DESC
LIMIT 30
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## 9. Cache behaviour

```sql
/* bf_audit */
SELECT
  sum(ProfileEvents['CachedReadBufferReadFromCacheBytes']) AS cache_read_bytes,
  sum(ProfileEvents['CachedReadBufferReadFromSourceBytes']) AS source_read_bytes,
  sum(ProfileEvents['S3ReadBytes']) AS s3_read_bytes,
  sum(ProfileEvents['OSReadChars']) AS os_read_bytes,
  round(
    sum(ProfileEvents['CachedReadBufferReadFromCacheBytes']) /
    greatest(sum(ProfileEvents['CachedReadBufferReadFromCacheBytes']) +
             sum(ProfileEvents['CachedReadBufferReadFromSourceBytes']), 1) * 100, 1
  ) AS cache_hit_pct
FROM clusterAllReplicas('<cluster>', system.query_log)
WHERE event_date >= today() - 7
  AND event_time >= now() - INTERVAL 7 DAY
  AND type = 'QueryFinish'
  AND is_initial_query = 1
  AND query_kind = 'Select'
  AND query NOT LIKE '%bf_audit%'
LIMIT 1
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

Treat these counters as directional. They are not the billing meter.

## 10. Part creation per day (optional)

`system.part_log` may be disabled or retain less than the window. If the query fails, record a gap and use the insert count as a proxy.

```sql
/* bf_audit */
SELECT
  toDate(event_time) AS day,
  count() AS parts_created,
  sum(size_in_bytes) AS bytes_created
FROM system.part_log
WHERE event_time >= now() - INTERVAL 7 DAY
  AND event_type = 'NewPart'
GROUP BY day
ORDER BY day
LIMIT 40
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## 11. View and materialized-view usage (optional)

If `system.query_views_log` is disabled, record a gap and infer usage from the query text instead.

```sql
/* bf_audit */
SELECT
  view_name,
  count() AS reads,
  sum(read_bytes) AS read_bytes
FROM system.query_views_log
WHERE event_time >= now() - INTERVAL 7 DAY
  AND type = 'QueryFinish'
GROUP BY view_name
ORDER BY reads DESC
LIMIT 50
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## 12. Concurrency baseline and peak

```sql
/* bf_audit */
SELECT
  quantile(0.5)(q) AS median_queries_per_minute,
  quantile(0.95)(q) AS p95_queries_per_minute,
  max(q) AS peak_queries_per_minute
FROM (
  SELECT toStartOfMinute(event_time) AS minute, count() AS q
  FROM clusterAllReplicas('<cluster>', system.query_log)
  WHERE event_date >= today() - 7
    AND event_time >= now() - INTERVAL 7 DAY
    AND type = 'QueryFinish'
    AND is_initial_query = 1
    AND query NOT LIKE '%bf_audit%'
  GROUP BY minute
)
LIMIT 1
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## 13. Filter columns and never-referenced columns

This is analysis, not another query. Use the `sample_query` values from query 1 (top 20 patterns).

1. Extract every column named in each `WHERE`, `PREWHERE`, `JOIN ... ON`, `GROUP BY`, and `ORDER BY`.
2. Map each column to its table from `system.columns`.
3. Count how often each column appears across the top 20 patterns.
4. Compare the most frequent filter columns with:
   - `system.tables.sorting_key`
   - `system.data_skipping_indices`
5. Record columns that do not appear in any top-20 pattern and are larger than 10 GB compressed. These are unread-column candidates, not yet findings. Confirm against comments or DDL before calling them unused.

Limits:

- `sample_query` is truncated to 1,200 characters. It is enough to see the main filters but not every predicate.
- Column names can be aliases. Match on the underlying column where possible.
- A column absent from the top 20 may still be used by a long-tail query. State confidence as `medium` at best.
