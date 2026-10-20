# ingestion-kafka

**Rule IDs:** `playbook:kafka-lag`, `playbook:4-workload-isolation`
**Area:** Ingestion & pipelines
**Severity:** MEDIUM when consumer lag grows with no recovery
**Evidence:** `system.kafka_consumers`

## Trigger

- A Kafka consumer whose `last_poll_time` is older than five minutes.
- `num_messages_read` falling behind the topic offset for the window.
- A non-empty `last_error`.

```sql
/* bf_audit */
SELECT
  table,
  consumer_id,
  assignments,
  last_poll_time,
  num_messages_read,
  last_error
FROM system.kafka_consumers
LIMIT 500
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

If `system.kafka_consumers` is not present, record the check as not run. ClickPipes runs in the control plane and is not visible through SQL: state that as a gap, never as a pass.

## Why it matters

A lagging consumer is a data freshness incident in progress. The table stays queryable, so dashboards show old data without an error.

## False positives

- A consumer paused on purpose.
- A newly created topic with no messages yet.

## Fix

- Read `last_error` and the consumer assignment.
- Scale the consumer or reduce per-message work.
- For ClickPipes, check the pipeline status in the console; SQL cannot see it.

## Effort

Low to inspect. Medium to repair the consumer.
