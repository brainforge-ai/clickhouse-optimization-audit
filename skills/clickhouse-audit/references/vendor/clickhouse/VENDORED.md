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

One local modification, required for the plugin directory's security policy:

- Removed `clickhouse-best-practices/rules/agent-connect-mcp.md`.
- Removed section 4.2 "Connect AI Agents to ClickHouse" from `clickhouse-best-practices/AGENTS.md`, and its references in `clickhouse-best-practices/SKILL.md`.

That guidance tells an agent to read database credentials from environment variables and connect with `clickhouse-client`. This plugin never does that; it authenticates only through ClickHouse Cloud OAuth via the remote MCP server. Modified files carry a notice at the top. Everything else is copied verbatim. The audit skill reads these files as reference documents; they are not loaded as active skills.

## Why vendor instead of depend

- No extra marketplace for the user to add.
- Works offline.
- The audit is reproducible against a known rule set.

## Update

Run:

```bash
./scripts/update-vendor.sh <commit-sha>
```

The script reapplies the modification above. Then review the diff, update this file's commit and date, and re-run the plugin validation.
