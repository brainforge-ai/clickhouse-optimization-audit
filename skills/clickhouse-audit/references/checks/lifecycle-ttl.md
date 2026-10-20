# lifecycle-ttl

**Rule IDs:** `playbook:ttl-health`, `cost:storage`
**Area:** Data lifecycle
**Severity:** MEDIUM when expired parts hold more than 5% of storage
**Evidence:** `system.parts` TTL columns, `system.moves`

## Trigger

- Parts whose TTL timestamp is in the past and still active, or
- Stuck moves in `system.moves`, or
- A table with a TTL expression but `ttl_only_drop_parts = 0` and many partially expired parts.

```sql
/* bf_audit */
SELECT
  database,
  table,
  countIf(delete_ttl_info_max < now()) AS expired_parts,
  sumIf(bytes_on_disk, delete_ttl_info_max < now()) AS expired_bytes,
  min(delete_ttl_info_max) AS oldest_expiry
FROM system.parts
WHERE active
  AND database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA', '_temporary_and_external_tables')
GROUP BY database, table
HAVING expired_parts > 0
ORDER BY expired_bytes DESC
LIMIT 200
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

```sql
/* bf_audit */
SELECT database, table, elapsed, progress
FROM system.moves
LIMIT 50
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

If `delete_ttl_info_max` is not present on this version, record the check as not run.

## Why it matters

TTL that exists but does not delete is the most common reason a "we have retention" table keeps growing. The parts are billed every month.

## False positives

- TTL configured to move data to cold storage rather than delete it.
- A move in progress that started minutes ago.

## Fix

- Enable `ttl_only_drop_parts = 1` where whole-part drops are acceptable.
- Fix the TTL expression so it applies to existing parts.
- Investigate stuck moves before changing the policy.

## Effort

Low to change a TTL setting. Medium to rewrite the policy.
