# schema-mv-refresh

**Rule IDs:** `playbook:materialized-view-freshness`
**Area:** Schema
**Severity:** MEDIUM
**Evidence:** `system.view_refreshes`, `system.tables` for refreshable MVs

## Trigger

- A refreshable view with `status != 'Scheduled'` or `'Finished'`,
- `last_refresh_time` older than twice its `refresh_interval`, or
- A non-empty `last_refresh_exception`.

## Why it matters

A stale refreshable materialized view serves old numbers with no error. Dashboards look fine and are wrong.

## False positives

- A view configured to refresh on demand or by a manual trigger.
- A view created inside the audit window that has not reached its first refresh.

## Fix

- Read `last_refresh_exception` and fix the source query.
- Align the refresh interval with the source update rate.
- Drop views that no query reads.

## Effort

Low to inspect. Medium to repair.
