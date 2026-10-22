# model-json

**Rule IDs:** `schema-json-when-to-use`
**Area:** Data model & storage
**Severity:** MEDIUM
**Evidence:** Inventory query 4 (types), DDL for tables with JSON/Map/String payload columns

## Trigger

- `JSON`, `Map`, or a wide `String` column named `payload`, `properties`, `attributes`, `metadata`, or `event_data`, above 1 GB.
- Frequently filtered fields stored inside the JSON or Map instead of typed columns.

## Why it matters

ClickHouse reads only referenced paths in a JSON column, but typed columns are still faster and cheaper for fields that are filtered or aggregated often. Open-ended keys fit `Map`; a stable schema does not.

## False positives

- Genuinely dynamic event payloads should stay JSON.
- A `Map` used for open-ended keys is correct even if it is large.

## Fix

Promote the top filtered paths to typed columns; keep the rest in JSON. Show the new-table DDL and the projection or materialized view that fills the typed column.

## Effort

Medium to high.
