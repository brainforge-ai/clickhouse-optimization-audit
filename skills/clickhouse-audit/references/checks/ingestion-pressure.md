# ingestion-pressure

**Rule IDs:** `playbook:insert-backpressure`, `insert-batch-size`
**Area:** Ingestion & pipelines
**Severity:** HIGH when inserts were rejected or delayed
**Evidence:** `system.events`, `system.metrics`

## Trigger

- `RejectedInserts` above zero in the window, or
- `DelayedInserts` above zero, or
- `PartsActive` above 3,000 across the service, or
- A merge backlog that stays above zero for more than ten minutes.

```sql
/* bf_audit */
SELECT event, value
FROM system.events
WHERE event IN ('DelayedInserts', 'RejectedInserts', 'TooManyParts', 'InsertedRows', 'InsertedBytes')
ORDER BY event
LIMIT 20
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

```sql
/* bf_audit */
SELECT metric, value
FROM system.metrics
WHERE metric IN ('PartsActive', 'Merge', 'PartMutation', 'DelayedInserts', 'ReplicatedChecks')
ORDER BY metric
LIMIT 20
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## Why it matters

Parts-per-table snapshots show the steady state. These counters show the moments inserters were told to wait or were rejected, which is the actual ingestion failure.

## False positives

- Counters are cumulative since server start. Compare with the window length and the insert rate.
- A single burst during a backfill.

## Fix

- Batch inserts to 10k to 100k rows, or enable async inserts.
- Reduce partition cardinality so merges can keep up.
- Fix the producer that retries on rejection and amplifies the load.

## Effort

Low to batch. Medium to change the partition key. High to change the producer.
