# architecture-dictionaries

**Rule IDs:** `playbook:dictionary-health`
**Area:** Architecture
**Severity:** MEDIUM
**Evidence:** `system.dictionaries`

## Trigger

- Any dictionary with `status != 'LOADED'`, or
- A non-empty `last_exception`, or
- `loading_duration` above 60 seconds.

## Why it matters

A failed dictionary returns empty joins or throws at query time. The table it enriches looks correct while results are wrong or queries fail.

## False positives

- A dictionary still loading for the first time during the audit window.
- A dictionary the owner has intentionally disabled.

## Fix

- Read `last_exception` and fix the source query or connection.
- Move the refresh to a schedule that matches the source update rate.
- Remove dictionaries that no query uses.

## Effort

Low to inspect. Medium to repair the source.
