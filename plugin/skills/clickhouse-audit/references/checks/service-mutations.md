# service-mutations

**Rule IDs:** `playbook:mutation-backlog`
**Area:** Service health
**Severity:** HIGH when a mutation has failed or is older than one hour
**Evidence:** `system.mutations`

## Trigger

Any mutation with `is_done = 0`, and either `latest_fail_reason` is non-empty or `create_time` is more than one hour old.

```sql
/* bf_audit */
SELECT
  database,
  table,
  mutation_id,
  command,
  create_time,
  parts_to_do,
  is_done,
  latest_fail_time,
  latest_fail_reason
FROM system.mutations
WHERE is_done = 0
ORDER BY create_time
LIMIT 200
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

Also count recent mutations per table, because frequent `ALTER UPDATE` or `ALTER DELETE` rewrites parts:

```sql
/* bf_audit */
SELECT table, count() AS mutations, max(create_time) AS latest
FROM system.mutations
WHERE create_time >= now() - INTERVAL 7 DAY
GROUP BY table
ORDER BY mutations DESC
LIMIT 50
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## Why it matters

A mutation rewrites every part it touches. A stuck one keeps rewriting them, blocks merges, grows the queue and can fail the next insert. In Cloud this is one of the few ways a service degrades without a visible query error.

## False positives

- A large mutation that started minutes ago and is progressing (`parts_to_do` falling).
- A deliberate one-off backfill the team already watches.

## Fix

- Read `latest_fail_reason` first. Fix the cause before retrying.
- Kill a stuck mutation with `KILL MUTATION` only after the cause is understood.
- Prefer `ReplacingMergeTree` with a version column over repeated `ALTER UPDATE`.
- Batch `ALTER DELETE` into partition drops where the data model allows it.

## Effort

Low to inspect. Medium to change the ingestion pattern. High to repair a stuck mutation on a large table.
