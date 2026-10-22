# query-precomputation-mv

**Rule IDs:** `query-mv-incremental`, `query-mv-refreshable`, `architecture-advisor:decision-real-time-preaggregation`
**Area:** Query efficiency
**Severity:** HIGH
**Evidence:** Workload query 1 (repeated normalized patterns with aggregation), inventory query 3 (existing MVs and their targets), workload query 5 (MV targets with no reads)

## Trigger

- The same aggregation pattern runs frequently with a high read volume (for example, daily rollups by tenant and day).
- An existing materialized view's target table has no reads in the window.
- A nested chain of views wraps a full scan.

## Why it matters

Pre-computing a repeated aggregation turns a scan of raw data into a scan of a small rollup. It reduces both compute and cache pressure.

## False positives

- A pattern that runs a few times a day may not justify the write cost.
- An MV target with no reads may be read by a downstream service the audit cannot see. Ask.
- Incremental MVs only fire on inserts to the source table; refreshable MVs are for complex joins.

## Fix

Propose:

- An incremental MV with an `AggregatingMergeTree` target, or
- A refreshable MV for a complex join, or
- A summary table loaded on a schedule.

Include the DDL, the exact query patterns it replaces, and the expected read-volume reduction.

## Effort

Medium.
