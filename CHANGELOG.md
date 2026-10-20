# Changelog

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
