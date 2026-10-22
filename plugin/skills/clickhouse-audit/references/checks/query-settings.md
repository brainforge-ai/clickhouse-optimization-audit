# query-settings

**Rule IDs:** `playbook:query-settings`, `query-join-choose-algorithm`
**Area:** Query efficiency
**Severity:** MEDIUM when a top pattern runs with settings that disable pruning or spilling
**Evidence:** `query_log.Settings` for the top patterns

## Trigger

For the top 20 patterns by read bytes, any of:

- `max_threads = 1` on a scan larger than 10 GB.
- `max_bytes_before_external_group_by = 0` on an aggregation that peaks above 50% of replica memory.
- `join_algorithm` is `partial_merge` or `full_sorting_merge` without a stated reason.
- `final = 1` on a large table where no dedup is required.
- `use_query_cache = 0` on a repeated identical pattern, or `1` on a pattern that never repeats.

```sql
/* bf_audit */
SELECT
  normalized_query_hash,
  any(query) AS sample,
  count() AS runs,
  sum(read_bytes) AS read_bytes,
  any(Settings['max_threads']) AS max_threads,
  any(Settings['max_memory_usage']) AS max_memory_usage,
  any(Settings['max_bytes_before_external_group_by']) AS external_group_by,
  any(Settings['join_algorithm']) AS join_algorithm,
  any(Settings['use_query_cache']) AS use_query_cache,
  any(Settings['final']) AS final
FROM clusterAllReplicas('<cluster>', system.query_log)
WHERE type = 'QueryFinish'
  AND is_initial_query = 1
  AND query_kind = 'Select'
  AND query NOT LIKE '%bf_audit%'
GROUP BY normalized_query_hash
ORDER BY read_bytes DESC
LIMIT 20
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

If `Settings` is not present on this version, record the check as not run. Do not guess.

## Why it matters

The same SQL can be fast or catastrophic depending on the settings it ran with. These values are recorded per query, so the finding is measured rather than inferred from the text.

## False positives

- A client that deliberately caps threads to protect a shared service.
- A one-off administrative query in the top 20.

## Fix

- Raise `max_threads` for large scans, or set it per query rather than globally.
- Enable external aggregation or raise the memory cap for the pattern that spills.
- Remove `FINAL` where `ReplacingMergeTree` dedup is not needed, or move to a versioned read.
- Turn the query cache on only for repeated identical patterns.

## Effort

Low for per-query settings. Medium to change a client or profile.
