---
name: clickhouse-audit
description: Audit a ClickHouse Cloud service for optimization opportunities across service health, data model and storage, ingestion and pipelines, query efficiency, and data lifecycle. Use when the user asks to audit, review, profile, optimize, or reduce cost on ClickHouse, or runs /clickhouse-optimization-audit:audit.
---

# ClickHouse Optimization Audit

Run a read-only, evidence-backed audit of one ClickHouse Cloud service. Produce:
1. A Markdown report in the conversation, also saved as a file.
2. A self-contained HTML report saved next to it.
3. `findings.json`, the machine-readable source both reports render from.

The audit reads metadata and system tables only. It never reads row data from user tables, never writes, and never executes DDL.

## Runtime paths (resolve once)

`ROOT` is the folder that contains this `SKILL.md`:

- Plugin install: `${CLAUDE_PLUGIN_ROOT}/skills/clickhouse-audit`
- Bare skill install: the folder holding `SKILL.md`

All paths below are relative to `ROOT`. If a referenced file is missing, stop and name it. Do not substitute your own template or schema.

## Hard rules

Read these before the first tool call. They are not negotiable.

- **Allowed MCP tools:** `get_organizations`, `get_services_list`, `get_service_details`, `list_databases`, `list_tables`, `run_select_query`.
- **Never call:** billing, backup, ClickPipes, or service-management tools. They exist on the server and are out of scope.
- **Only** `SELECT`, `EXPLAIN`, and subqueries. Reject anything else before sending. No `INSERT`, `ALTER`, `CREATE`, `DROP`, `OPTIMIZE`, `SYSTEM`, or `SET`.
- **No row data.** Every query must read `system.*` tables or execute `EXPLAIN`. If a query would return user rows, do not run it.
- **Every query** carries `LIMIT` and `SETTINGS max_execution_time = 60`.
- **Tag every audit query** with the comment `/* bf_audit */` at the start and `SETTINGS log_comment = 'bf_audit'`, so the audit can exclude itself from the workload profile. If the setting is rejected, keep the comment.
- **No network calls** other than the ClickHouse MCP server. No telemetry.
- **Redact literals** (strings, numbers, emails, IDs) from every query shown in a report. Replace with `?`.
- **No evidence, no finding.** Every finding must cite a query result.
- **Full service, not a sample.** Every user database, table and column is in scope. Lists are paged until they match the preflight counts, never truncated.
- **Real numbers only.** Every figure in the report comes from a query in this run. Do not compute a percentage unless both numbers are in the run. Do not estimate storage, reads, memory or cost. If a number is missing, say so in the gaps.
- **State gaps.** Missing permissions, short retention, disabled logs, and unavailable metrics are listed, never silently skipped.
- **One report design.** The HTML report is produced only by rendering `findings.json` through the bundled template. Never hand-write HTML, restyle the report, or invent a second JSON shape. If the renderer fails, stop and report the error.
- **Plain engineering prose.** The report reads like an engineer wrote it for another engineer. No marketing language, no filler, no restating the same number in three places.

## Prerequisites to explain to the user

Two things must be true before the audit runs. The plugin can do neither for them.

1. **MCP is enabled on the service.** In the ClickHouse Cloud console: open the service → **Connect** → **MCP** → **Enable**. This needs the `control-plane:service:manage-mcp` permission.
2. **The user has signed in.** The first connection opens a browser for ClickHouse OAuth:
   - Claude Code: `/mcp` → `plugin:clickhouse-optimization-audit:clickhouse` → Authenticate
   - claude.ai chat: the plugin's **Connectors** tab → Connect
   - Cowork: same Connectors tab

If the MCP tools are absent, the server is not connected. If a tool returns 401/403 or an auth error, the user has not completed sign-in. If a tool returns "MCP is not enabled" or the service rejects the connection, send them to prerequisite 1.

## Workflow

### Step 1 — Confirm the connection

Call `get_organizations` with no arguments.

- Success → continue.
- Missing tool → stop and give the connect instructions above.
- Auth error → stop and ask the user to complete the browser sign-in, then retry once.
- "MCP not enabled" → stop and give the console steps.

### Step 2 — Choose the service

1. `get_organizations` → if more than one, ask which organization.
2. `get_services_list(organizationId)` → if more than one service, list them with name, state and size, and ask which to audit. Never guess.
3. `get_service_details(organizationId, serviceId)` → record tier, region, provider, replicas, memory, and state if present. If a field is absent, record `null`; do not invent it.

Keep `organizationId` and `serviceId` for the rest of the run. Pass `serviceId` to `list_databases`, `list_tables`, and `run_select_query` on every call.

### Step 3 — State scope and get one confirmation

Before the first query, tell the user:
- Scope: the full service. All user databases, tables and columns.
- Service name and tier.
- Window: full history by default, meaning everything the service still retains in `system.query_log` and `system.part_log`. Offer 1, 7, 30, or a custom number of days.
- Read the measured log range in the preflight. Set `scope.window_days` to `null` for full history, and set `window_start` and `window_end` from that measured range.
- If the service retains less than a requested window, use the shorter available range and state the actual start and end in the report.
- If a full-history query hits the 60 second limit, halve the range, record the reduced range as a gap, and never guess.
- Roughly 40 queries, mostly against `system.query_log`, `system.parts`, `system.tables` and `system.columns`.
- "If the service is idle, this will wake it and incur compute."
- Access limits: the audit can only see what the signed-in role can read.

Ask **once**: "Proceed?" Do not ask again during the run.

### Step 4 — Preflight and inventory (pass 1)

Run the preflight counts first (`00-inventory.md` section 0): tables, columns, active parts, and `log_queries`. These counts are the completeness budget for every list that follows.

If `log_queries` is `0`, stop the workload profile and report it as the finding.

Then collect:
- Version, timezone, cluster name.
- Databases and tables (metadata).
- Engines, sorting/primary/partition keys, TTL presence, views and MVs.
- Columns, types, compressed and uncompressed sizes, codecs, key membership.
- Active parts, partitions, merge backlog.
- Skipping indices and projections where available.

Resolve the log source once. Read the cluster name from `system.clusters` and record it as `<cluster>`. Every `system.query_log` read uses `clusterAllReplicas('<cluster>', system.query_log)` so all replicas are covered. If the list is empty, read `system.query_log` and record a gap.

Reconcile each list with its preflight count. If a list is short, page it. If a page fails, record the gap; never present a partial list as complete.

### Step 5 — Workload profile (pass 2)

Follow `$ROOT/references/checks/01-workload.md`. For the chosen window:
- Top query patterns by read bytes, duration and memory.
- Hot tables and tables with no reads.
- Insert cadence and average batch size.
- Peak vs baseline concurrency.
- Pruning proxy: `read_rows / result_rows`.
- Cache read vs source read from `ProfileEvents`.

Exclude the audit's own queries with `query NOT LIKE '%bf_audit%'`.

### Step 6 — Deep dive (pass 3)

Follow `$ROOT/references/checks/02-deep-dive.md`. Take the top 3 patterns and run `EXPLAIN indexes = 1` on each. Record Parts and Granules read vs total. If `EXPLAIN` is rejected by the MCP, mark it as a gap and fall back to the pruning proxy.

### Step 7 — Analyze

Load every check file for every area. Each check file lists its rule IDs, evidence, trigger threshold, false positives, fix and effort. Run the check against the evidence you collected.

A check you cannot evaluate is not a pass. Add it to `checks_not_run` with the reason, and the area it belongs to cannot score Green.

Areas and files:

| Area | Key | Files |
| --- | --- | --- |
| Service health | `service_health` | `$ROOT/references/checks/service-shape.md`, `$ROOT/references/checks/service-cache.md`, `$ROOT/references/checks/service-errors.md`, `$ROOT/references/checks/service-replication.md`, `$ROOT/references/checks/service-disk.md`, `$ROOT/references/checks/service-workloads.md`, `$ROOT/references/checks/service-compute.md`, `$ROOT/references/checks/service-mutations.md`, `$ROOT/references/checks/service-topology.md` |
| Data model & storage | `data_model` | `$ROOT/references/checks/model-order-by.md`, `$ROOT/references/checks/model-types.md`, `$ROOT/references/checks/model-partitioning.md`, `$ROOT/references/checks/model-json.md`, `$ROOT/references/checks/model-codecs.md`, `$ROOT/references/checks/model-skip-indexes.md`, `$ROOT/references/checks/model-mv-refresh.md`, `$ROOT/references/checks/model-redundancy.md`, `$ROOT/references/checks/model-parts.md`, `$ROOT/references/checks/model-merges.md`, `$ROOT/references/checks/model-compression.md`, `$ROOT/references/checks/model-settings.md`, `$ROOT/references/checks/model-aggregate-correctness.md` |
| Ingestion & pipelines | `ingestion` | `$ROOT/references/checks/ingestion-batch.md`, `$ROOT/references/checks/ingestion-engines.md`, `$ROOT/references/checks/ingestion-dictionaries.md`, `$ROOT/references/checks/ingestion-duplicates.md`, `$ROOT/references/checks/ingestion-pressure.md`, `$ROOT/references/checks/ingestion-kafka.md` |
| Query efficiency | `query_efficiency` | `$ROOT/references/checks/query-pruning.md`, `$ROOT/references/checks/query-patterns.md`, `$ROOT/references/checks/query-joins.md`, `$ROOT/references/checks/query-joins-strategy.md`, `$ROOT/references/checks/query-grain-mismatch.md`, `$ROOT/references/checks/query-precomputation-mv.md`, `$ROOT/references/checks/query-precomputation-projections.md`, `$ROOT/references/checks/query-settings.md`, `$ROOT/references/checks/query-cache.md` |
| Data lifecycle | `data_lifecycle` | `$ROOT/references/checks/lifecycle-storage.md`, `$ROOT/references/checks/lifecycle-unused-tables.md`, `$ROOT/references/checks/lifecycle-ttl.md`, `$ROOT/references/checks/lifecycle-tiering.md` |

Cost is not a scored area. It is a derived panel built from `cost.measured` and `cost.drivers`. A cost driver references finding IDs; it never creates a second finding.

Cross-check reasoning against the vendored rules under `$ROOT/references/vendor/clickhouse/`. Cite the rule ID, not the vendor file name.

### Step 8 — Score and rank

Use `$ROOT/references/rubric.md`.

- Five scored areas: `service_health`, `data_model`, `ingestion`, `query_efficiency`, `data_lifecycle`. Cost is derived, not scored.
- Weight: CRITICAL 3, HIGH 2, MEDIUM 1.
- Per area: Red if any CRITICAL or total ≥ 6; Yellow 2–5; Green 0–1.
- Every finding carries one area and one `rule_id`. A finding that is really a correctness risk (stale MV, failed dictionary, replication lag, TTL deleting live data) sets `"risk": true`. Risk findings still score in their area.
- Rank findings by `impact × confidence ÷ effort`.
- The top 3 findings that have a safe rewrite get one from `$ROOT/references/rewrites.md`, with a before/after measurement query. If a finding has no safe rewrite, skip it and take the next finding.
- Label every rewrite "Review before applying". Never execute it.
- Only write a rewrite when its column list came from `system.columns` in this run. Set `basis` to that source, for example `system.columns for default.events`. Never write DDL from memory.
- Write one `areas` entry for each of the five scored areas. `summary` is one sentence: what the audit checked and why the status is what it is. `impact` is one line: what fixing the area is worth, or "No material savings identified." For a green area, list what was checked in `checked`.

### Step 9 — Cost

Use `$ROOT/references/cost-model.md` and `$ROOT/references/pricing/`.

Report measured units first (read volume, storage, parts/day, cache hit), then dollars. Claim compute dollars only when a fix names a service-shape change. Every dollar figure carries the pricing date and the not-a-quote footer.

If plan, provider, or region is missing from `get_service_details`, ask the user before producing any dollar figure. If they decline, show measured units only.

### Step 10 — Write the outputs

Build `findings.json` with the schema in `$ROOT/references/rubric.md`. Then:

1. Write `findings.json` to disk. Validate it:
   ```
   python3 "$ROOT/scripts/render_report.py" --findings clickhouse-audit-<service>-<date>.json --check
   ```
2. Render both reports. If Bash is available:
   ```
   python3 "$ROOT/scripts/render_report.py" \
     --findings clickhouse-audit-<service>-<date>.json \
     --template "$ROOT/references/report-template.html" \
     --out clickhouse-audit-<service>-<date>.html \
     --md-out clickhouse-audit-<service>-<date>.md \
     --open
   ```
   `--open` opens the HTML in the default browser. Pass it only when the run has a local shell and a desktop session. Skip it in a cloud or SSH session, or when the user says not to open a window. If it cannot open a browser, the script prints the path and carries on.
   If Bash is not available, stop and say the HTML report needs a shell. Do not hand-write the HTML.
3. Verify the rendered HTML before showing anything:
   ```
   grep -c 'id="findings-data"' clickhouse-audit-<service>-<date>.html
   grep -c 'class="hero-cta"' clickhouse-audit-<service>-<date>.html
   grep -c '3FA93A' clickhouse-audit-<service>-<date>.html
   ```
   All three must return at least 1. If any is missing, the wrong file was written. Re-render from the template; do not patch the HTML by hand.
4. Show the Markdown in the conversation.
5. Use the current directory, or the directory the user asks for. Name the files with the service lowercased and non-alphanumerics replaced by `-`, and the date as `YYYY-MM-DD`.

Default CTA: "Want the full assessment? Brainforge can turn this audit into a scoped optimization plan with projected savings and a delivery sequence." with `https://www.brainforge.ai/free-consultation-call`.

End the conversation with the executive summary, the scorecard, the top 3 findings, the cost opportunity, and the paths to the saved files.

## Report writing

The reader is a data engineer or platform owner. Every sentence carries a fact or an action. The report is bullets and short lines, not prose.

Structure, in this order:

1. Executive summary: three sentences.
2. At a glance: measured numbers.
3. Scorecard: five areas with status.
4. Category detail, one block per area: what we found, issues, recommendations, impact if improved.
5. Cost impact (derived), rewrites, gaps, next step.

- Summary: three sentences maximum. Sentence one states the largest problem with its measured size. Sentence two names the cause. Sentence three names the first action. No greeting, no "this report", no adjectives like healthy, robust, powerful, or real opportunity.
- Category detail: `summary` explains the status in one sentence. Issues are one bullet per finding: title, object, and one measured number. Recommendations are one high-level line per finding, no DDL, no steps, no full solution. Impact is one line. A green area says what was checked, "No issues found", "No action required", and either the savings or none.
- Findings: object and number first. `learn.reviews holds 6.10 GB and had zero reads in 6.3 days.` Avoid "we observed that", "it appears that", "there may be".
- Fixes: imperative, one action per sentence. `Drop the two duplicate tables.` Not "it would be advisable to consider".
- Do not repeat a metric that already appears in At a glance, the scorecard, or Cost. Findings add evidence, not repetition.
- Observations: at most seven bullets, one fact each, only when the fact is not already in a finding, the cost section, or the gaps list.
- State uncertainty only in the gap or false-positive field, in one clause.
- Active voice. No em dashes in prose; use commas or full stops.
- No emoji, no exclamation marks, no "AI-powered", no "leverage".
- Do not restate a finding inside its own recommendation. The issue says what is wrong; the recommendation says what to do.

After writing `findings.json`, read the three output files back. If any sentence breaks these rules, rewrite the JSON field and re-render.

## Query templates

Use these wrappers exactly. They keep every read bounded and tagged.

```sql
/* bf_audit */
SELECT ...
FROM system.<table>
WHERE ...
LIMIT 200
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

For `clusterAllReplicas`, keep the same trailer:

```sql
/* bf_audit */
SELECT ...
FROM clusterAllReplicas('default', system.query_log)
WHERE event_date >= today() - 7 AND event_time >= now() - INTERVAL 7 DAY
  AND type = 'QueryFinish' AND is_initial_query = 1
  AND query NOT LIKE '%bf_audit%'
LIMIT 200
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

If ClickHouse rejects `log_comment` or `max_execution_time` for the role, retry once without `SETTINGS` and record a gap. Never retry an unbounded query.

## Fallback mode (no MCP)

When the user cannot or will not connect MCP, accept a pasted query and optional DDL. Run static checks only:

- `SELECT *`
- filters on non-key columns
- functions wrapping key columns
- `LIMIT` without `ORDER BY`
- join shape and join order
- type choices
- partition key

Output is labeled **Query-level review**. No scorecard, no service-wide cost, no dollar figures beyond a query-level read estimate. Do not imply the rest of the service was reviewed.

## Error handling

| Symptom | Action |
| --- | --- |
| MCP tools absent | Connect instructions, stop |
| 401/403 or auth error | Ask for browser sign-in, retry once |
| "MCP not enabled" | Console steps, stop |
| `system.query_log` empty or permission denied | Record a gap; continue with metadata-only checks |
| Window shorter than requested | Use the available range; state it in Scope and Gaps |
| Query timeout | Reduce the window or add a filter; retry once; then record a gap |
| `clusterAllReplicas` fails | Use `system.query_log`; record a partial-workload gap |
| `EXPLAIN` rejected | Use the pruning proxy; record a gap |
| No tables or no reads | Produce a short report that says so; do not invent findings |

## Files

- `$ROOT/references/checks/` — evidence SQL, thresholds, rule IDs
- `$ROOT/references/rubric.md` — weights, scoring, ranking, `findings.json` schema
- `$ROOT/references/rewrites.md` — rewrite patterns
- `$ROOT/references/cost-model.md` — cost formulas and rules
- `$ROOT/references/report-template.html` — self-contained HTML report
- `$ROOT/references/pricing/` — dated ClickHouse Cloud rates
- `$ROOT/references/vendor/clickhouse/` — pinned ClickHouse best-practice rules (Apache-2.0)
