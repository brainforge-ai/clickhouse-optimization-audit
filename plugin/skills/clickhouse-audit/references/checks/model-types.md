# model-types

**Rule IDs:** `schema-types-native-types`, `schema-types-minimize-bitwidth`, `schema-types-lowcardinality`, `schema-types-enum`, `schema-types-avoid-nullable`
**Area:** Data model & storage
**Severity:** CRITICAL
**Evidence:** Inventory query 4 (types, sizes, codecs)

## Data boundary

The audit does not read row data, so it cannot compute exact cardinality. Use the heuristics below and mark confidence `medium` at best. The fix template tells the user how to verify cardinality before applying it.

## Trigger

- `String` column with a name that suggests a small fixed set (`status`, `type`, `country`, `currency`, `category`, `channel`, `plan`, `region`), above 1 GB compressed.
- `Enum` candidate: same pattern, with evidence in the DDL comment or a known fixed list.
- Integer wider than needed: `UInt64`/`Int64` for IDs or counters that fit 32 bits, with column size above 1 GB.
- `Nullable(T)` where a default value would do, especially in the sorting key.
- `DateTime64(9)` where millisecond or second precision is enough.
- `Float32`/`Float64` for a column whose name suggests money or currency.

## Why it matters

Every byte of type width and every Nullable mask is read on every scan and stored on every part. Right-sizing cuts both storage and query time.

## False positives

- A `String` that is genuinely high-cardinality should stay `String`.
- Nullable is legitimate when “unknown” is different from the default.
- FixedString can waste space when values vary in length.

## Fix

Show the `ALTER TABLE ... MODIFY COLUMN` or new-table DDL. For LowCardinality, include the verification query:
`SELECT uniqExact(col) FROM table` (the user runs it; the audit does not).

## Effort

Medium for an in-place type change on a small column. High for a key column or a full backfill.
