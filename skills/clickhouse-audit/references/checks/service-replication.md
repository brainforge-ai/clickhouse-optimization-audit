# service-replication

**Rule IDs:** `playbook:replication-health`
**Area:** Service health
**Severity:** HIGH
**Evidence:** `system.replicas`, `system.replication_queue`

## Trigger

- Any replica with `is_readonly = 1`, `absolute_delay > 300`, or
- `system.replication_queue` holds more than 100 entries, or an entry older than 15 minutes.

## Why it matters

A read-only replica loses writes for the tables on it. A growing queue means replication is falling behind and reads may serve stale data.

## False positives

- ClickHouse Cloud on SharedMergeTree: `system.replicas` and `system.replication_queue` are empty by design. Record "not applicable on SharedMergeTree" as a gap, not a pass.
- A short delay during a large insert.

## Fix

- Find the read-only replica and its error in `system.replicas.last_exception`.
- Clear the queue cause before restarting anything.
- Escalate to ClickHouse support for SharedMergeTree health.

## Effort

Low to inspect. High to recover a replica.
