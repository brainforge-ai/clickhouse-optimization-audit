# model-aggregate-correctness

**Rule IDs:** `playbook:aggregate-correctness`, `playbook:materialized-view-freshness`
**Area:** Data model & storage
**Severity:** HIGH when a wrong aggregate feeds a dashboard, MEDIUM otherwise
**Evidence:** DDL for `AggregatingMergeTree`, `SummingMergeTree`, `ReplacingMergeTree` and `MaterializedView`

## Trigger

- `SummingMergeTree` over a column that is not additive, such as a rate, a price or an average.
- `AggregatingMergeTree` column not typed `AggregateFunction(...)`, or an MV inserts plain values into state columns.
- A `ReplacingMergeTree` without a version column, read with `FINAL` only sometimes.
- A materialized view whose select contains `JOIN`, `now()`, `rand()` or `dictGet` with a mutable dictionary.
- An MV whose target table has more rows than its source in the same period.

```sql
/* bf_audit */
SELECT database, name, engine, create_table_query, as_select
FROM system.tables
WHERE (
    engine IN ('AggregatingMergeTree', 'SummingMergeTree', 'ReplacingMergeTree', 'CollapsingMergeTree')
    OR engine = 'MaterializedView'
  )
  AND database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA', '_temporary_and_external_tables')
LIMIT 2000
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## Why it matters

These tables return plausible but wrong numbers after a schema or ingestion change. No error appears, so nobody notices until a decision is made on the number. This is the highest-cost class of defect an audit can find.

## False positives

- A `SummingMergeTree` used only for counters that are additive.
- An MV with a `JOIN` against an immutable dimension table.

## Fix

- Use `AggregateFunction` states and `*Merge` combinators consistently.
- Replace `SummingMergeTree` with `AggregatingMergeTree` for rates and averages.
- Add a version column to every `ReplacingMergeTree` and read with `FINAL` or a dedup view.
- Rebuild or backfill the affected rollup, then verify against the source.

## Effort

Medium to fix the model. High to backfill and reconcile.
