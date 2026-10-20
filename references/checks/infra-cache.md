# infra-cache

**Rule IDs:** `playbook:4-caching-and-the-latency-cliff`
**Area:** Infrastructure
**Severity:** MEDIUM
**Evidence:** Workload query 9 (cache vs source reads)

## Trigger

- Cache hit below 50% on a read-heavy service, or
- `source_read_bytes` more than 2× `cache_read_bytes`.

## Why it matters

In ClickHouse Cloud, object storage reads are roughly 500× slower than local SSD and cost compute time. Low cache locality shows up as latency and compute spend.

## False positives

- A cold start, a new deployment, or a one-off backfill.
- Services with genuinely random access over data much larger than cache.

## Fix

- Pre-warm common ranges before users arrive.
- Partition-prune by time so only relevant parts are fetched.
- Pre-aggregate repeated heavy queries with a materialized view or projection.
- Consider a larger replica for more cache, but only after reducing reads.

## Effort

Low for pre-warming. Medium for pre-aggregation. High for a service-shape change.
