# Implementation notes

## Verified against current docs

- `.mcp.json` remote server shape: `{ "type": "http", "url": "https://mcp.clickhouse.cloud/mcp" }`. OAuth is triggered by the server; no extra config. Source: code.claude.com/docs/en/mcp.
- Plugin manifest fields: `name`, `displayName`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, `defaultEnabled`. Source: code.claude.com/docs/en/plugins/manifest-reference.
- Marketplace file: `.claude-plugin/marketplace.json` with `name`, `owner`, `plugins[].source`. Source: code.claude.com/docs/en/plugin-marketplaces.
- Plugin MCP servers start automatically when the plugin is enabled. Source: code.claude.com/docs/en/mcp#plugin-provided-mcp-servers.
- Remote MCP on claude.ai chat is listed on the plugin's Connectors tab and needs one Connect click. Source: claude.com/docs/plugins/platform-support.
- ClickHouse remote MCP exposes 13 read-only tools, including billing, backup and ClickPipes. The audit allowlist excludes those. Source: clickhouse.com/docs/products/cloud/features/ai-ml/remote-mcp.
- ClickHouse pricing formula and rates. Source: clickhouse.com/pricing, retrieved 2026-10-20.

## Deviations from the plan

1. **Command file is `commands/audit.md`, not `commands/clickhouse-audit.md`.** A command and a skill with the same name would produce the same namespaced command. The skill remains `clickhouse-audit`; the command is `/clickhouse-optimization-audit:audit`.
2. **Check files are grouped by concern, not one file per rule ID.** There are 25 files, each listing the rule IDs it implements. This avoids 31 near-duplicate files while preserving rule-level traceability in every finding. The plan's requirement — rule ID on every finding — is met.
3. **No subagents in v1.** The plan lists per-area subagents as a v2 option. Kept out to reduce setup complexity.
4. **Pricing coverage.** The public page publishes Enterprise rates by region, and Basic/Scale examples only for AWS us-east-1. The pinned file includes derived Basic/Scale us-east-1 rates and instructs the audit to ask or use a conservative upper bound elsewhere.
5. **No dollar figure without a shape change.** The plan's rule is enforced in `skills/clickhouse-audit/scripts/render_report.py` validation, not just in prose.

## Deliberate limits

- No row data is read, so `LowCardinality` and `Enum` candidates are name/size heuristics with medium confidence. The fix template tells the user to verify cardinality.
- Saved queries are not available in system tables. The report lists this as a gap.
- Host, CPU and disk metrics are unavailable through the remote MCP. Infrastructure findings use parts, merges, cache counters and service metadata.
- `EXPLAIN` may be rejected by the MCP. The audit falls back to `read_rows / result_rows` and lowers confidence.

## Open items

- Test live mode against a real ClickHouse Cloud service with MCP enabled.
- Create the public GitHub repository `brainforge-ai/clickhouse-optimization-audit` and push.
- Submit to Anthropic's directory (`claude.ai/directory/manage`) and record the listing URL.
- Confirm the default CTA page (`https://www.brainforge.ai/free-consultation-call`) with marketing.
