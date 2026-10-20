# ClickHouse Optimization Audit

A free Claude plugin from Brainforge. It audits one ClickHouse Cloud service read-only and returns a 360° optimization report: infrastructure, schema, architecture, queries, pre-computation and cost.

No backend. No hosting. No telemetry. Everything runs inside Claude through ClickHouse Cloud's managed remote MCP server.

## What you get

- **Scorecard** — Red / Yellow / Green for infrastructure, schema, architecture, queries and cost efficiency.
- **Ranked findings** — every one cites measured evidence and a ClickHouse best-practice rule ID.
- **Top 3 rewrites** — concrete DDL or SQL, why it helps, and a before/after measurement query.
- **Pre-computation opportunities** — materialized views, projections and summary tables, with the exact patterns they replace.
- **Cost** — read volume, storage, parts and cache hit rate in measured units, then estimated dollars where the arithmetic supports it.
- **Three files** — Markdown, a self-contained HTML report, and `findings.json`.

## Requirements

- Claude Code, Cowork, or claude.ai with plugins.
- A ClickHouse Cloud service.
- **MCP enabled on that service** (see below).
- A role that can `SELECT` from `system.query_log`, `system.parts`, `system.tables` and `system.columns`.

## Install

In Claude Code:

```text
/plugin marketplace add brainforge-ai/clickhouse-optimization-audit
/plugin install clickhouse-optimization-audit@brainforge-plugins
```

From a shell:

```bash
claude plugin marketplace add brainforge-ai/clickhouse-optimization-audit
claude plugin install clickhouse-optimization-audit@brainforge-plugins
```

The plugin declares the ClickHouse remote MCP server in `.mcp.json`, so installing it is the only setup. No API keys, no config file edits.

## Before the first run

**Enable MCP on the service.** The plugin cannot do this.

1. Open the service in the ClickHouse Cloud console.
2. Click **Connect**.
3. Select **MCP**.
4. Click **Enable**.

This needs the `control-plane:service:manage-mcp` permission.

## Connect

The first connection opens a browser for ClickHouse OAuth. That login is the only manual step after enabling MCP.

| Surface | Where |
| --- | --- |
| Claude Code | `/mcp` → `plugin:clickhouse-optimization-audit:clickhouse` → Authenticate |
| claude.ai chat | Customize → Plugins → ClickHouse Optimization Audit → **Connectors** → Connect |
| Cowork | The plugin's **Connectors** tab → Connect |

On Claude Code and Cowork the server starts with the plugin. On claude.ai chat it appears on the plugin's Connectors tab and needs one Connect click.

## Run

```text
/clickhouse-optimization-audit:audit
```

Or ask: “Audit my ClickHouse service.”

Optional arguments: a service name and a window (`1d`, `7d`, `30d`, a custom number of days, or `all` for the full retained history). Default window: 7 days. If the service retains less than the requested window, the audit uses what is available and states the actual range. If the organization or service is ambiguous, the plugin asks. It never guesses.

Before querying, the plugin states the window, the approximate query count (around 40), and that an idle service will wake and incur compute. It asks for one confirmation.

## What it checks

| Area | Examples |
| --- | --- |
| **Infrastructure** | Parts per partition, merge backlog, compression ratio, cache hit rate, service shape vs sustained load |
| **Schema** | Empty or `tuple()` ordering keys, high-cardinality leading columns, key order, missing filter columns, String vs LowCardinality/Enum, oversized integers, Nullable, DateTime64(9), Float for money, partition count and key, TTL, codecs, skip indexes |
| **Architecture** | Insert batch size and cadence, async inserts, engine choice, ReplacingMergeTree without a version, `FINAL`, join algorithms and memory, mixed workloads |
| **Queries** | Top patterns by reads, duration and memory; full-scan ratio; `SELECT *`; non-key filters; functions on key columns; `LIMIT` without `ORDER BY`; missed `PREWHERE` |
| **Pre-computation** | Repeated heavy aggregations; unused materialized views; nested view chains; projection candidates |
| **Cost** | Storage and compute drivers tied to the findings that would reduce them |

The reasoning is grounded in ClickHouse's own guidance. The plugin vendors `clickhouse-best-practices` and `clickhouse-architecture-advisor` from [ClickHouse/agent-skills](https://github.com/ClickHouse/agent-skills) (Apache-2.0) at a pinned commit. See `skills/clickhouse-audit/references/vendor/clickhouse/VENDORED.md`.

## Read-only guarantee

- Allowed tools: `get_organizations`, `get_services_list`, `get_service_details`, `list_databases`, `list_tables`, `run_select_query`.
- Never calls billing, backup, ClickPipes or service-management tools.
- Only `SELECT`, `EXPLAIN` and subqueries. No writes, no DDL, no `SYSTEM`, no `SET`.
- Reads metadata and `system.*` tables only. **No row data from user tables.**
- Every query has a `LIMIT` and `max_execution_time`.
- No network calls other than the ClickHouse MCP server.
- Query literals are redacted in every report.

## Cost estimates

Cost is shown twice:

1. **Measured units** — read TB/day, compressed storage TB, parts/day, cache hit rate.
2. **Estimated dollars** — using the published ClickHouse Cloud formula and a pinned, dated rate file.

```text
compute/month = (RAM_GB ÷ 8) × active_hours × compute_unit_price × replicas
storage/month = compressed_TB × storage_price_per_TB
```

Storage savings are direct arithmetic. Compute savings are claimed **only** when a fix names a service-shape change: fewer replicas, smaller memory, more idle time, or a workload split. Otherwise the report shows headroom, not dollars.

Every dollar figure carries the pricing date and this footer: *Estimate based on published ClickHouse Cloud rates. Not a quote. Verify at clickhouse.com/pricing.* Backups, egress and ClickPipes are excluded.

## Limits

- **Saved queries are not auditable.** ClickHouse Cloud stores them in console metadata, not a system table. Views and materialized views are audited; saved queries only if pasted.
- **Infrastructure is partial.** The remote MCP exposes no CPU, disk or host metrics. The audit uses parts, merges, cache counters and service metadata.
- **`system.query_log` is a rolling window.** Short retention or missing permission is reported as a gap.
- **SharedMergeTree services** do not have classic replica lag. The audit skips that check rather than reporting a false finding.
- **Dollar figures are estimates.** Pricing changes. The pinned rate file is dated and the report says so.

## Fallback mode

No MCP? Paste a query and optional DDL. The plugin runs static checks only: full scans, `SELECT *`, non-key filters, type choices, join shape and partitioning. The output is labeled **Query-level review**, with no scorecard and no service-wide cost.

## Outputs

Saved in the current directory:

```text
clickhouse-audit-<service>-<YYYY-MM-DD>.md
clickhouse-audit-<service>-<YYYY-MM-DD>.html
clickhouse-audit-<service>-<YYYY-MM-DD>.json
```

The HTML is one self-contained file: offline, light and dark themes, collapsible findings, print styles, inline SVG cost chart.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| No ClickHouse tools | Plugin not enabled, or MCP server not connected. Run `/mcp` (Claude Code) or open the Connectors tab. |
| 401 / auth error | Complete the browser sign-in, then retry. |
| “MCP not enabled” | Enable MCP on the service in the Cloud console. |
| `system.query_log` denied | Use a role with `SELECT` on system tables, or accept a metadata-only report with a gap. |
| Short retention | Choose a shorter window. The report states the actual range. |
| Query timeout | The plugin reduces the window or adds a filter, then records a gap. |
| `EXPLAIN` rejected | The plugin falls back to the read/result proxy and lowers confidence. |

## Development

```bash
# Validate the plugin
claude plugin validate --strict .

# Validate the sample findings and render the HTML
python3 skills/clickhouse-audit/scripts/render_report.py --findings examples/findings.example.json --check
python3 skills/clickhouse-audit/scripts/render_report.py --findings examples/findings.example.json \
  --out examples/output/report.html --md-out examples/output/report.md

# Refresh the vendored ClickHouse skills
./skills/clickhouse-audit/scripts/update-vendor.sh <commit-sha>
```

Layout:

```text
.claude-plugin/plugin.json      manifest
.claude-plugin/marketplace.json marketplace catalog
.mcp.json                       ClickHouse Cloud remote MCP
skills/clickhouse-audit/        the only active skill (references + scripts ship inside it)
commands/audit.md               thin entry point
skills/clickhouse-audit/references/checks/   evidence SQL, thresholds, rule IDs
skills/clickhouse-audit/references/vendor/   pinned Apache-2.0 rules
skills/clickhouse-audit/scripts/render_report.py   findings.json → self-contained HTML
```

## License and attribution

Apache-2.0. The vendored ClickHouse agent skills are Apache-2.0, Copyright ClickHouse, Inc. See `LICENSE`, `NOTICE`, and `skills/clickhouse-audit/references/vendor/clickhouse/`.
