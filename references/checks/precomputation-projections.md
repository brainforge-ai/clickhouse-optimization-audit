# precomputation-projections

**Rule IDs:** `query-mv-incremental`, `playbook:3.4-materialized-views-and-projections`
**Area:** Pre-computation
**Severity:** MEDIUM
**Evidence:** Inventory query 8 (existing projections), workload query 1, deep dive

## Trigger

- The same table is queried with two different dominant sort orders.
- A repeated aggregation filters on a column that is not the table's ordering key.
- A projection exists but no query uses it.

## Why it matters

A projection maintains an alternate sort order on the same table, transparently. It can remove the need for a second copy of the data or a separate MV.

## False positives

- Projections roughly double the storage of the projected data.
- A one-off query does not justify one.
- An unused projection is pure write and storage cost.

## Fix

Propose `ALTER TABLE ... ADD PROJECTION` with the alternate key, plus the measurement query. If a projection is unused, propose dropping it.

## Effort

Medium.
