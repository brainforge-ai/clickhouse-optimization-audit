# Rewrite patterns

Every rewrite is a proposal. Label it **Review before applying**. Include a before/after measurement. Never execute it.

## Ordering key

Before:
```sql
ORDER BY (event_id, ts)
```
After:
```sql
ORDER BY (tenant_id, event_type, ts)
```
Why: low-cardinality filters first, then time. Include a new `CREATE TABLE ... AS SELECT` plan and a backfill, not `ALTER`.

Measure: `EXPLAIN indexes = 1` on the top query; compare `Granules: read/total`.

## Type right-sizing

Before:
```sql
status String,
amount Float64,
event_time DateTime64(9)
```
After:
```sql
status LowCardinality(String),
amount Decimal(18, 2),
event_time DateTime
```
Why: smaller types read and compress better; `Decimal` is correct for money.
Caveat: verify `uniqExact(status)` before choosing `LowCardinality`.

Measure: compare `system.columns.data_compressed_bytes` and query `read_bytes` after the new parts are written.

## Time filter rewrite

Before:
```sql
WHERE toDate(event_time) = today()
```
After:
```sql
WHERE event_time >= today() AND event_time < today() + 1
```
Why: the key column is no longer wrapped in a function, so the index can prune.

## Partitioning

Before:
```sql
PARTITION BY toYYYYMMDD(event_time)
```
After:
```sql
PARTITION BY toYYYYMM(event_time)
TTL event_time + INTERVAL 90 DAY DELETE
```
Why: fewer, larger partitions; TTL drops whole partitions.
Caveat: keep daily partitions only when TTL needs them.

## Codec

Before:
```sql
event_time DateTime
```
After:
```sql
event_time DateTime CODEC(Delta, ZSTD(1))
```
Why: monotonic timestamps compress better with Delta. Effect applies to new parts.

## Skip index

Before:
```sql
-- no index on total_votes
```
After:
```sql
INDEX idx_total_votes total_votes TYPE minmax GRANULARITY 4
```
Why: avoids granules when filtering on a non-key column.
Caveat: verify the filter is selective; do not index low-selectivity columns.

## Projection

Before:
```sql
-- one sort order only
```
After:
```sql
ALTER TABLE events ADD PROJECTION by_user (SELECT * ORDER BY user_id, event_time)
```
Why: serves queries that filter by `user_id` without a second table.
Caveat: roughly doubles the storage of the projected data.

## Incremental materialized view

Before:
```sql
SELECT tenant_id, toDate(event_time) AS day, count()
FROM events
GROUP BY tenant_id, day
```
After:
```sql
CREATE MATERIALIZED VIEW events_daily
ENGINE = AggregatingMergeTree
ORDER BY (tenant_id, day)
AS SELECT tenant_id, toDate(event_time) AS day, countState() AS count
FROM events
GROUP BY tenant_id, day;
```
Why: replaces repeated scans of raw events with a small rollup.
Caveat: fires only on inserts to the source table; historical data needs a one-time backfill.

## Async inserts

Before: many small inserts per second.
After:
```sql
SET async_insert = 1;
SET wait_for_async_insert = 1;
```
Why: server-side batching reduces part creation and merge work.
Caveat: adds a small latency to visibility.

## Join

Before:
```sql
SELECT ... FROM big b JOIN small s ON b.small_id = s.id
WHERE b.event_date = today()
```
After:
```sql
SELECT ...
FROM (SELECT ... FROM big WHERE event_date = today()) AS b
JOIN (SELECT ... FROM small WHERE active) AS s ON b.small_id = s.id
```
Why: filter before joining; the right side is built in memory.

## LIMIT

Before:
```sql
SELECT * FROM events LIMIT 100
```
After:
```sql
SELECT tenant_id, event_time, status
FROM events
ORDER BY event_time DESC
LIMIT 100
```
Why: read only needed columns; order so the limit is meaningful.
