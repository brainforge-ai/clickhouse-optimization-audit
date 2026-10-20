# Vendored ClickHouse agent skills

**Source:** https://github.com/ClickHouse/agent-skills
**Commit:** `69a8354b05b5942e5cea77b6c87be7788303fc18`
**Vendored:** 2026-10-20
**License:** Apache-2.0 (see `LICENSE` and `NOTICE` in this directory)

## What is included

- `clickhouse-best-practices/` — 31 rules covering schema, query, insert and agent guidance
- `clickhouse-architecture-advisor/` — 5 decision frameworks for ingestion, joins, late-arriving data, partitioning and pre-aggregation

## What is not included

`chdb-datastore`, `chdb-sql`, `clickhouse-js-node-*`, `infra-clickhouse`, `infra-postgres`, `clickstack-otel-collector`, and `clickhouse-managed-postgres-rca`. They do not apply to a read-only audit of a running Cloud service.

## Changes

None. Files are copied verbatim. The audit skill reads them as reference documents; they are not loaded as active skills.

## Why vendor instead of depend

- No extra marketplace for the user to add.
- Works offline.
- The audit is reproducible against a known rule set.

## Update

Run:

```bash
./scripts/update-vendor.sh <commit-sha>
```

Then review the diff, update this file's commit and date, and re-run the plugin validation.
