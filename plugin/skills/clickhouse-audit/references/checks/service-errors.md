# service-errors

**Rule IDs:** `playbook:6-errors-and-limits`
**Area:** Service health
**Severity:** MEDIUM
**Evidence:** Workload query 10 (query_log exceptions) and `system.errors`

## Trigger

- Any error code in `system.errors` with `value > 0` in the window, or
- More than 0.5% of finished queries carry a non-zero `exception_code`.

## Why it matters

Errors are the cheapest signal for memory pressure, timeouts, quota limits and broken ingestion. A service that fails silently is worse than a slow one.

## False positives

- Errors from the audit's own queries (excluded with `query NOT LIKE '%bf_audit%'`).
- A single failed experiment from a developer session.

## Fix

- Group errors by code and name, then read the top three messages.
- For memory limits, reduce the query or raise the per-query cap.
- For timeouts, fix pruning or raise `max_execution_time` deliberately.

## Effort

Low to inspect. Medium to fix the query or setting behind each code.
