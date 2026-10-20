# Changelog

## 0.1.0 — 2026-10-20

- Initial release.
- One command audits a ClickHouse Cloud service across infrastructure, schema, architecture, queries, pre-computation and cost.
- Read-only MCP allowlist; metadata and system tables only.
- 25 check files with evidence SQL, thresholds and rule IDs.
- Vendored ClickHouse best-practices and architecture-advisor at `69a8354b`.
- Markdown, self-contained HTML and `findings.json` outputs.
- Cost model in measured units and estimated dollars, with a pinned dated rate file.
- Fallback query-level review without MCP.
