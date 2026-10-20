# cost-compute

**Rule IDs:** `cost:compute`, plus the query, schema, and architecture findings that cause it
**Area:** Cost
**Severity:** HIGH when read volume can drop by 30% or more
**Evidence:** Workload queries 1, 6, 7, 8; `get_service_details`

## Trigger

- Top patterns read far more than they return.
- Repeated heavy aggregations that a rollup would replace.
- Peak concurrency far below provisioned size for most of the window.
- Ingest and analytics contending on one service.

## Why it matters

Compute is billed by size × active time × replicas. Query optimization alone does not reduce the bill unless it changes service shape or idle time.

## Rules

- Report read-volume reduction in TB/day. That is measured.
- Claim compute dollars only when a fix names a service-shape change: fewer replicas, smaller memory, or more idle time.
- Otherwise report **headroom**, not dollars.
- Never multiply saved bytes by a compute rate. Bytes are not the billing unit.

## Fix

Tie each compute saving to a named shape change and show the arithmetic. If no shape change is justified, say so.

## Effort

Medium to high.
