# model-compression

**Rule IDs:** `playbook:3.2-data-types`, `playbook:3.6-other-design-levers`, `schema-types-native-types`, `schema-types-lowcardinality`
**Area:** Data model & storage
**Severity:** MEDIUM
**Evidence:** Inventory queries 4 and 5 (compressed vs uncompressed bytes)

## Trigger

- Table compression ratio below 3× and `bytes_on_disk > 1 GB`, or
- A single column above 1 GB with a ratio below 2×.

## Why it matters

Storage is billed on compressed bytes. Poor compression also means more bytes scanned per query. Type choice and codecs drive both.

## False positives

- Already-compressed payloads (images, parquet blobs) do not compress further. Exclude columns whose names or types suggest binary payloads.
- Tiny tables are noise.

## Fix

- Right-size types: `LowCardinality(String)` for repeated strings, `Enum` for fixed sets, smallest integer width, `DateTime` instead of `DateTime64(9)`.
- Add codecs: `Delta`/`DoubleDelta` for timestamps and monotonic counters, `Gorilla` for floats, `ZSTD(1)` for mixed strings.
- Remove unnecessary `Nullable`, which adds a mask column.

## Effort

Low for codecs on new parts. High for a type change, which needs a new table and backfill.
