# Changelog

## 0.8.0 — 2026-10-21

- `render_report.py --open` opens the finished HTML report in the default browser. The audit passes it when a local desktop session is available and skips it in cloud or SSH sessions.

## 0.7.0 — 2026-10-21

- Default window is full retained history (`window_days: null`), not 7 days. A run can still ask for 1, 7, 30 or a custom number of days.
- The measured log range sets `window_start` and `window_end`. A long-range timeout halves the range and records the reduced range as a gap.

## 0.6.0 — 2026-10-21

- Stale-table detection: last read time per table across the full log retention, with thresholds for never read, 90+ days and 30 to 90 days.
- Duplicate-table detection: exact copies by rows, bytes and sorting key, plus same-shape tables under a different key.
- Grain mismatch detection: repeated GROUP BY on a base table when an aggregate table, materialized view or projection already covers the grain.
- Schema redundancy check: duplicate columns and raw/parsed pairs.

## 0.5.0 — 2026-10-21

- The renderer now validates the arithmetic: area weights and scores, storage and read reduction percentages, dollar totals and rank scores. Impossible figures fail the run.
- New checks: query errors, replication health, disk headroom, dictionary health and refreshable materialized view freshness.
- New log coverage probe records the real `query_log` range and is used as the report window.
- Rewrites that create a table must name their `basis` (the `system.columns` read they came from); DDL from memory is rejected.

## 0.4.0 — 2026-10-21

- Audit scope is the full service by default: every user database, table and column. Lists are paged until they match preflight counts.
- Added a preflight step: table, column and part counts plus `log_queries`, run before any analysis.
- Cluster name is read from `system.clusters` and substituted into every `clusterAllReplicas` call instead of being hardcoded.
- Numbers rule: every figure must come from a query in the run; no estimates and no derived percentages without both inputs.
- Added `checks_not_run`. A check that could not run blocks a Green score for its area and appears in the gaps.

## 0.3.0 — 2026-10-21

- New report structure: summary, at-a-glance, scorecard, then one block per category with what we found, issues, recommendations and impact if improved.
- `findings.json` gains per-area notes (`summary`, `impact`, optional `checked`) and an optional `metric` per finding.
- Cost efficiency lists cost drivers as issues when no finding is scored there.
- Category blocks use plain-English bullets, no full solutions; rewrites stay in the appendix.

## 0.2.1 — 2026-10-21

- Remove `defaultEnabled` from `plugin.json`. The marketplace entry still sets it, and older Claude Code builds (and the SDK) strip the manifest field as unknown.

## 0.2.0 — 2026-10-21

- Score statuses are Red / Yellow / Green (was Red / Amber / Green).
- Report design is enforced: the HTML is always rendered from the bundled Brainforge template, with brand colors, an at-a-glance strip, a scorecard and a booking link.
- Runtime files (checks, rubric, templates, renderer) now ship inside `skills/clickhouse-audit/`, so the report renders even when the plugin is installed as a bare skill.
- Added report writing rules to remove filler and repeated metrics.
- Window defaults to 7 days. Users can pick 1, 7, 30, a custom number of days, or the full retained history. If retention is shorter than the requested window, the audit uses what is available and reports the actual range.


## 0.1.0 — 2026-10-20

- Initial release.
- One command audits a ClickHouse Cloud service across infrastructure, schema, architecture, queries, pre-computation and cost.
- Read-only MCP allowlist; metadata and system tables only.
- 25 check files with evidence SQL, thresholds and rule IDs.
- Vendored ClickHouse best-practices and architecture-advisor at `69a8354b`.
- Markdown, self-contained HTML and `findings.json` outputs.
- Cost model in measured units and estimated dollars, with a pinned dated rate file.
- Fallback query-level review without MCP.
