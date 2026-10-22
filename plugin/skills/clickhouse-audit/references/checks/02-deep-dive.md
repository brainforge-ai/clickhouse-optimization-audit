# Deep dive (pass 3)

Prove whether the ordering key and indexes are doing any work for the heaviest patterns.

## Procedure

1. Take the top 3 `normalized_query_hash` values from workload query 1.
2. Take `sample_query` for each.
3. Strip the audit comment, trailing `SETTINGS`, and any `LIMIT` you added.
4. Run `EXPLAIN indexes = 1` on the remaining SELECT.

```sql
/* bf_audit */
EXPLAIN indexes = 1
SELECT ...
```

`EXPLAIN` is read-only and does not execute the query. Keep the original query text intact apart from the removed comment and trailer; do not rewrite it.

## What to read

The output contains lines for each table:

- `Parts: <read>/<total>`
- `Granules: <read>/<total>`

Record both. A ratio near 1.0 means no pruning. A ratio near 0 means the key is pruning well.

Also record whether the plan shows:

- `ReadFromMergeTree` with a primary-key condition
- a skip-index condition
- a full scan with no condition

## If EXPLAIN is rejected

The MCP may only allow `SELECT`. If the call fails:

1. Mark `EXPLAIN unavailable` as a gap.
2. Use the pruning proxy from workload query 8.
3. Reduce confidence on any pruning finding to `medium`.

## Per-table interpretation

| Observation | Likely cause | Check file |
| --- | --- | --- |
| Granules read ≈ total, filter column not in key | key/filter mismatch | `query-pruning.md`, `schema-order-by.md` |
| Granules read low but duration high | reading many columns, heavy aggregation, join memory | `query-patterns.md`, `query-joins.md` |
| Parts read high for a narrow time filter | partition key mismatch or over-partitioning | `schema-partitioning.md` |
| Skip index present but not used | wrong index type or expression | `schema-skip-indexes.md` |

Do not claim pruning effectiveness from `read_rows / result_rows` alone when EXPLAIN succeeded. Use the measured granules.
