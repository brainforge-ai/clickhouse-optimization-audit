# cost-unused-tables

**Rule IDs:** `playbook:unused-tables`, `cost:storage`
**Area:** Cost
**Severity:** HIGH when unread bytes exceed 5% of stored bytes, MEDIUM otherwise
**Evidence:** Workload query 5 (no reads in the window) plus the last-read query below

## Trigger

Read the last read time per table across the full `system.query_log` retention, not just the audit window.

- Never read and larger than 1 GB: HIGH.
- Last read more than 90 days ago and larger than 1 GB: HIGH.
- Last read 30 to 90 days ago and larger than 5% of storage: MEDIUM.
- Read inside the window: not a finding.

```sql
/* bf_audit */
SELECT
  t.database,
  t.name,
  t.total_rows,
  t.total_bytes,
  formatReadableSize(t.total_bytes) AS readable_size,
  q.last_read,
  dateDiff('day', q.last_read, now()) AS days_since_read
FROM system.tables AS t
LEFT JOIN (
  SELECT arrayJoin(tables) AS tbl, max(event_time) AS last_read
  FROM clusterAllReplicas('<cluster>', system.query_log)
  WHERE type = 'QueryFinish'
    AND is_initial_query = 1
    AND query_kind = 'Select'
    AND query NOT LIKE '%bf_audit%'
    AND notEmpty(tables)
  GROUP BY tbl
) AS q ON concat(t.database, '.', t.name) = q.tbl
WHERE t.database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA', '_temporary_and_external_tables')
  AND t.engine NOT IN ('View', 'MaterializedView', 'LiveView', 'WindowView')
ORDER BY t.total_bytes DESC
LIMIT 5000
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## Why it matters

Storage is billed every month on compressed bytes. A table nobody reads is the cheapest saving in the audit, and the query gives an exact last-read date instead of a guess.

## False positives

- Data kept for compliance, audit or a legal hold.
- Tables read by an external system, a BI tool with a separate role, or a restore test outside the log retention.
- A table loaded for a one-off exercise and about to be dropped.
- `system.query_log` retention shorter than the staleness threshold: then the table is "not seen in N days", not "unused".

## Fix

- Confirm the owner and the retention reason.
- Add a TTL, archive to object storage, or drop.
- Quote the saving in bytes and an estimated dollar figure from the pricing table.

## Effort

Low for TTL. Medium for archive. High for a drop, because it needs owner sign-off.
