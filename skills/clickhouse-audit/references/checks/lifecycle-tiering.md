# lifecycle-tiering

**Rule IDs:** `playbook:storage-tiering`, `cost:storage`
**Area:** Data lifecycle
**Severity:** MEDIUM when one disk holds more than 80% of bytes and no cold tier exists
**Evidence:** `system.storage_policies`, `system.parts.disk_name`, `system.moves`

## Trigger

- All active bytes sit on one disk on a service larger than 1 TB.
- A storage policy defines a cold or object-storage volume that holds no parts.
- Stuck moves.

```sql
/* bf_audit */
SELECT policy_name, volume_name, disks, move_factor
FROM system.storage_policies
LIMIT 200
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

```sql
/* bf_audit */
SELECT disk_name, count() AS parts, sum(bytes_on_disk) AS bytes, formatReadableSize(sum(bytes_on_disk)) AS readable
FROM system.parts
WHERE active
GROUP BY disk_name
ORDER BY bytes DESC
LIMIT 50
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## Why it matters

Tiering is the difference between paying local disk rates and object-storage rates for cold data. On Cloud the lever is often the storage policy on the table, not the table itself.

## False positives

- A service small enough that tiering costs more in complexity than it saves.
- A policy intentionally kept on one volume for latency.

## Fix

- Attach a cold volume to tables whose data is read rarely after 30 days.
- Move by TTL to the cold volume rather than deleting.
- Measure the bytes that would move before changing the policy.

## Effort

Medium for a table policy. High for a service-wide change.
