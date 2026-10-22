# model-merges

**Rule IDs:** `playbook:4-insert-strategy`, `architecture-advisor:decision-ingestion-strategy`
**Area:** Data model & storage
**Severity:** MEDIUM
**Evidence:** Inventory query 6 (active merges, rows read)

## Trigger

- More than 50 active merges at once, or
- Merge `rows_read` over the window approaching the rows written, which means write amplification.

## Why it matters

Merges are background compute you pay for. If merges read many times what inserts write, the insert pattern or partition scheme is creating avoidable work.

## False positives

- A large backfill or a one-off `OPTIMIZE` produces a temporary spike. Ask before flagging.
- Small services during a bulk load can legitimately show a backlog.

## Fix

- Batch inserts and enable async inserts.
- Reduce partition count.
- Avoid `OPTIMIZE TABLE ... FINAL` on a schedule.
- Check for frequent mutations (`ALTER UPDATE`/`DELETE`), which rewrite parts.

## Effort

Low for insert batching. Medium for partition or mutation changes.
