# infra-disk

**Rule IDs:** `playbook:disk-headroom`
**Area:** Infrastructure
**Severity:** HIGH
**Evidence:** `system.disks` and `system.parts` by disk

## Trigger

- Any disk above 80% used, or
- Free space on any disk below 20% of total.

## Why it matters

A full disk stops merges and then inserts. Headroom is a hard limit, not a performance tuning choice.

## False positives

- Object storage backed disks that report total capacity rather than quota.
- A temporary spike from a backfill that the operator already tracks.

## Fix

- Identify the largest tables and parts on the full disk.
- Remove unread tables or shorten TTL.
- Move cold parts to object storage where the engine supports it.

## Effort

Low to inspect. Medium to reclaim space. High to change storage policy.
