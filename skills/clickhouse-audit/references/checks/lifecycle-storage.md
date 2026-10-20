# lifecycle-storage

**Rule IDs:** `cost:storage`, plus the schema and infra findings that cause it
**Area:** Data lifecycle
**Severity:** HIGH when savings exceed 20% of stored bytes
**Evidence:** Inventory queries 3–5, workload query 5

## Trigger

Any of:

- Tables with no reads holding more than 5% of stored bytes.
- Large tables with no TTL and no retention need.
- Compression ratio below 3× on a large table.
- Type right-sizing that would cut a large column materially.

## Why it matters

Storage is billed on compressed bytes, monthly, continuously. Unused and over-wide data is the most reliable saving in the report.

## False positives

- Data kept for compliance or audit, even if not queried.
- A table read by an external service the audit cannot see.
- Recently loaded data before the first compaction.

## Fix

Quantify: `GB removed × storage rate`. Propose TTL, archive, drop, type change, or codec change. Label every dollar figure as an estimate.

## Effort

Low for TTL. Medium for type or codec changes. High for archive and drop.
