# model-partitioning

**Rule IDs:** `schema-partition-low-cardinality`, `schema-partition-lifecycle`, `schema-partition-query-tradeoffs`, `schema-partition-start-without`
**Area:** Data model & storage
**Severity:** HIGH
**Evidence:** Inventory queries 3 and 5 (`partition_key`, partition count, parts)

## Trigger

- More than 100 partitions on one table.
- Partition key uses a daily or sub-daily expression (`toYYYYMMDD`, `toDate`, `toStartOfHour`).
- Partition key has high cardinality (an ID or a raw timestamp) rather than a month.
- Partitioning exists with no TTL and no lifecycle need.

## Why it matters

Partitions are a data-management tool, not a general performance tool. Over-partitioning creates small parts, slow merges, and more memory. Partitioning by month with no filter on the partition column can make aggregations much slower.

## False positives

- Daily partitions can be justified for TTL expiry, where dropping a partition is cheaper than row-level TTL.
- Merge-oriented engines may benefit from one part per historical partition.
- A table with a few dozen partitions is fine.

## Fix

Propose `PARTITION BY toYYYYMM(event_time)`, or no partitioning, plus a TTL if retention is the goal. Show the new-table DDL and backfill. Never propose `ALTER ... PARTITION` as a performance fix.

## Effort

High.
