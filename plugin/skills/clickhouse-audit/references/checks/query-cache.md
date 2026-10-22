# query-cache

**Rule IDs:** `playbook:query-cache`, `playbook:4-caching-and-the-latency-cliff`
**Area:** Query efficiency
**Severity:** LOW to MEDIUM
**Evidence:** `system.query_log.query_cache_usage`, `system.query_cache`

## Trigger

- The cache is enabled and the hit rate is below 5% while the cache holds more than 100 MB.
- The cache is disabled and the same `normalized_query_hash` runs more than 50 times in the window.
- The cache is enabled and evictions exceed hits.

```sql
/* bf_audit */
SELECT
  query_cache_usage,
  count() AS queries,
  sum(read_bytes) AS read_bytes
FROM clusterAllReplicas('<cluster>', system.query_log)
WHERE type = 'QueryFinish'
  AND is_initial_query = 1
  AND query_kind = 'Select'
  AND query NOT LIKE '%bf_audit%'
GROUP BY query_cache_usage
ORDER BY queries DESC
LIMIT 10
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

```sql
/* bf_audit */
SELECT count() AS entries, sum(result_size) AS bytes, formatReadableSize(sum(result_size)) AS readable
FROM system.query_cache
LIMIT 1
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

If `query_cache_usage` is not present, record the check as not run.

## Why it matters

The query cache is memory. A cache that never hits costs memory and returns nothing; a cache that hits protects a repeated expensive read. Both are decisions the audit can now quantify.

## False positives

- A service where repeated patterns are already served by an aggregate.
- A cache intentionally disabled for correctness during a schema change.

## Fix

- Enable the cache only when the same expensive pattern repeats.
- Size it against the working set, not the largest query ever run.
- Prefer materialized views for deterministic repetition.

## Effort

Low to toggle. Medium to size and monitor.
