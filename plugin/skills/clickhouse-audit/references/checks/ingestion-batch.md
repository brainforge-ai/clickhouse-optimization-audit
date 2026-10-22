# ingestion-batch

**Rule IDs:** `insert-batch-size`, `insert-async-small-batches`, `insert-format-native`, `insert-mutation-avoid-update`, `insert-mutation-avoid-delete`, `insert-optimize-avoid-final`, `architecture-advisor:decision-ingestion-strategy`
**Area:** Ingestion & pipelines
**Severity:** CRITICAL when average batch is below 1,000 rows; HIGH when below 10,000
**Evidence:** Workload query 6 (inserts per hour, rows per insert), inventory query 6 (merges), DDL for mutation and `OPTIMIZE`

## Trigger

- Average rows per insert below 10,000, especially with more than 10 inserts per hour.
- Many inserts per hour producing one part each.
- `ALTER TABLE ... UPDATE` or `DELETE` in the query log.
- `OPTIMIZE TABLE ... FINAL` run on a schedule.
- Non-native insert format on a high-volume path (when the client is visible in the query text).

## Why it matters

Each insert creates a part. Small, frequent inserts create part churn, merge work, and write amplification. Mutations rewrite whole parts. `OPTIMIZE FINAL` fights background merges. All three are paid compute.

## False positives

- A small service with genuinely low volume.
- A one-off backfill.
- Streaming engines that already batch upstream.

## Fix

- Batch to 10,000–100,000 rows per insert.
- Enable async inserts for high-frequency small writes.
- Use native format on high-volume paths.
- Replace `ALTER UPDATE` with `ReplacingMergeTree` and a version column.
- Replace `ALTER DELETE` with lightweight `DELETE` or drop partitions.
- Stop scheduled `OPTIMIZE ... FINAL`.

## Effort

Low for batching, async inserts, and removing `OPTIMIZE`. High for an engine change.
