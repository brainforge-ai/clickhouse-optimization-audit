# model-redundancy

**Rule IDs:** `playbook:column-redundancy`, `schema-types-native-types`
**Area:** Data model & storage
**Severity:** MEDIUM when redundant columns exceed 10% of a table
**Evidence:** Inventory query 4 (columns, compressed bytes, types)

## Trigger

- Two columns in the same table with identical `data_compressed_bytes` above 1 MB and the same type, which usually means one is a copy.
- A raw and a parsed copy of the same field (`price` and `price_str`, `id` and `id_text`), where one is never used.
- More than 100 columns where the widest 10 hold more than 80% of the bytes.

```sql
/* bf_audit */
SELECT
  database,
  table,
  groupArray((name, type, data_compressed_bytes)) AS same_size_columns,
  count() AS duplicates
FROM system.columns
WHERE database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA', '_temporary_and_external_tables')
  AND data_compressed_bytes > 1000000
GROUP BY database, table, data_compressed_bytes, type
HAVING count() > 1
ORDER BY max(data_compressed_bytes) DESC
LIMIT 500
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## Why it matters

Duplicated columns double the bytes for the same fact and make every rewrite carry both versions. Readers then disagree about which column is authoritative.

## False positives

- Two columns that legitimately hold the same size by coincidence, such as two independent 1 MB String columns.
- A deliberate raw copy kept for lineage or re-parsing.

## Fix

- Name the authoritative column, migrate readers, then drop the copy.
- Parse once at ingest instead of storing both forms.
- Measure before and after with `system.columns`.

## Effort

Low to drop an unused column. Medium to migrate readers.
