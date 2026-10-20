# ingestion-engines

**Rule IDs:** `playbook:3-pick-an-engine`, `architecture-advisor:decision-late-arriving-upserts`, `architecture-advisor:decision-real-time-preaggregation`
**Area:** Ingestion & pipelines
**Severity:** HIGH
**Evidence:** Inventory query 3 (engine), DDL, workload query 6

## Trigger

- `ReplacingMergeTree` with no version column, while updates are expected.
- `MergeTree` with frequent `ALTER UPDATE` or `DELETE`.
- High-volume append-only facts stored in a non-MergeTree engine.
- A materialized view target that is not an `AggregatingMergeTree` or `SummingMergeTree` when it pre-aggregates.
- A large time-series table with no TTL.

## Why it matters

The engine encodes correctness and merge behavior, not just speed. The wrong variant can be a correctness problem, and it forces expensive mutations or `FINAL`.

## False positives

- A `ReplacingMergeTree` without a version column is fine when last-write-wins by insert order is acceptable and `FINAL` is not required.
- `MergeTree` is correct for append-only analytics.

## Fix

Propose the engine change with the new-table DDL, version or sign column, and backfill. For TTL, show `TTL event_time + INTERVAL 90 DAY DELETE`.

## Effort

High for an engine change. Low for adding TTL to a new table.
