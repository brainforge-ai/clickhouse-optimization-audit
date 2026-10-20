# Changelog

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
