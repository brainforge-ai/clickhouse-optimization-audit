# model-settings

**Rule IDs:** `playbook:mergetree-settings`, `schema-types-native-types`
**Area:** Data model & storage
**Severity:** LOW to MEDIUM
**Evidence:** table DDL (`create_table_query`) from inventory query 3

## Trigger

- `index_granularity` below 8192 on a table with large scans.
- `min_bytes_for_wide_part` set high enough to create many small wide parts.
- `ttl_only_drop_parts = 0` on a table with TTL.
- `max_bytes_to_merge_at_max_space_in_pool` lowered far below the default.
- A non-default `storage_policy` that no part uses.

```sql
/* bf_audit */
SELECT
  database,
  name,
  engine,
  extract(create_table_query, 'SETTINGS(.*)$') AS settings
FROM system.tables
WHERE engine LIKE '%MergeTree%'
  AND database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA', '_temporary_and_external_tables')
LIMIT 5000
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## Why it matters

These settings decide part shape, merge behaviour and how much of a scan is skipped. A wrong `index_granularity` or a tiny wide-part threshold quietly multiplies parts and metadata.

## False positives

- A deliberate small `index_granularity` for point lookups.
- Settings inherited from a profile rather than the DDL; the extracted text may be empty.

## Fix

- Keep `index_granularity` at the default unless point lookups dominate.
- Set `min_bytes_for_wide_part` so small parts stay compact.
- Turn on `ttl_only_drop_parts` when the TTL drops whole partitions.

## Effort

Low to change a setting on a new table. Medium to rebuild an existing one.
