# schema-codecs

**Rule IDs:** `playbook:3.6-codecs`
**Area:** Schema
**Severity:** MEDIUM
**Evidence:** Inventory query 4 (`compression_codec`, column bytes, type)

## Trigger

A column above 1 GB with the default codec where the type has a better fit:

- `DateTime` / `DateTime64` / monotonic integers → `Delta` + `ZSTD`
- Slowly changing counters → `DoubleDelta`
- Floats / metrics → `Gorilla`
- Low-variance integers → `T64`
- Mixed strings → `ZSTD(1)` (already the Cloud default)

## Why it matters

Codecs are per-column and cheap to change on new parts. They reduce both storage and read bytes.

## False positives

- Already-compressed or encrypted payloads.
- Columns that are read once and never scanned.
- Codec changes only affect new parts; existing parts keep their codec until merged.

## Fix

Show `ALTER TABLE ... MODIFY COLUMN col TYPE ... CODEC(...)`. State that the effect appears on new parts and after merges.

## Effort

Low.
