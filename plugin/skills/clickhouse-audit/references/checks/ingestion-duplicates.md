# ingestion-duplicates

**Rule IDs:** `playbook:duplicate-tables`, `cost:storage`
**Area:** Ingestion & pipelines
**Severity:** HIGH when duplicates exceed 10% of stored bytes
**Evidence:** Inventory queries 3 and 4 (table sizes, columns)

## Trigger

Two tests. Run both.

**Exact copies.** Same row count, same byte size and same sorting key:

```sql
/* bf_audit */
SELECT
  groupArray(database) AS databases,
  groupArray(name) AS tables,
  count() AS copies,
  any(total_rows) AS rows,
  any(total_bytes) AS bytes,
  formatReadableSize(any(total_bytes)) AS readable_size,
  any(sorting_key) AS sorting_key
FROM system.tables
WHERE database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA', '_temporary_and_external_tables')
  AND engine NOT IN ('View', 'MaterializedView', 'LiveView', 'WindowView')
  AND total_rows > 0
GROUP BY total_rows, total_bytes, sorting_key, primary_key
HAVING count() > 1
ORDER BY bytes DESC
LIMIT 500
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

**Same shape, different key.** Identical column names and types, different sizes:

```sql
/* bf_audit */
WITH signatures AS (
  SELECT
    database,
    table,
    groupArray(name ORDER BY position) AS columns,
    groupArray(type ORDER BY position) AS types,
    sum(data_compressed_bytes) AS bytes
  FROM system.columns
  WHERE database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA', '_temporary_and_external_tables')
  GROUP BY database, table
)
SELECT
  a.database, a.table, b.database, b.table,
  formatReadableSize(a.bytes) AS a_size,
  formatReadableSize(b.bytes) AS b_size
FROM signatures AS a
INNER JOIN signatures AS b
  ON a.columns = b.columns AND a.types = b.types
 AND (a.database, a.table) < (b.database, b.table)
WHERE a.bytes > 1000000000
ORDER BY greatest(a.bytes, b.bytes) DESC
LIMIT 200
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## Why it matters

Copies are pure waste. They also hide the real table: readers split across copies, caches are colder, and a schema fix has to be applied more than once.

## False positives

- A deliberate snapshot or backup table inside the same service.
- A staging table that is rebuilt on every load.
- Two tables that legitimately hold the same shape for different tenants or regions.

## Fix

- Name the canonical table with the owner, then drop or archive the others.
- Point readers at the canonical table before the drop.
- Report the bytes removed and the number of copies.

## Effort

Low to identify. Medium to retire a copy with reader sign-off.
