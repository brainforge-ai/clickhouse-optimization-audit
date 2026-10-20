# model-parts

**Rule IDs:** `playbook:4-ingest-lifecycle`, `architecture-advisor:decision-ingestion-strategy`
**Area:** Data model & storage
**Severity:** HIGH
**Evidence:** Inventory query 5 (active parts, partitions)

## Trigger

- More than 3,000 active parts on one table, or
- More than 100 active parts in one partition, or
- Parts per day growing faster than merges can consolidate (merge backlog in `infra-merges`).

## Why it matters

Every part is a directory of files. Too many parts slows merges, increases memory, and makes every query open more files. ClickHouse guidance treats parts climbing toward 10,000 per table as a warning sign.

## False positives

- Small tables with few rows but many parts are cheap. Require `rows > 1,000,000` or `bytes_on_disk > 1 GB`.
- ReplacingMergeTree and CollapsingMergeTree intentionally keep more parts for `FINAL` performance.

## Fix

1. Batch inserts to 10,000–100,000 rows.
2. Enable async inserts for high-frequency small writes.
3. Stop daily or hourly partitioning unless TTL requires it.
4. Let background merges finish before adding more partitions.

## Effort

Low for batching and async inserts. Medium for a partition-key change, which needs a new table and backfill.
