# ClickHouse Optimization Audit

Source repository for the ClickHouse Optimization Audit plugin for Claude, by Brainforge. The plugin itself lives in [`plugin/`](plugin/README.md). Its README is the user guide: requirements, setup, what it checks, data handling and limits.

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

## Repository layout

```text
plugin/                              the plugin bundle (what users install and the directory scans)
  .claude-plugin/plugin.json         manifest
  .mcp.json                          ClickHouse Cloud remote MCP
  commands/audit.md                  entry point
  skills/clickhouse-audit/           the audit skill: SKILL.md, checks, rubric, templates, render_report.py
  README.md  LICENSE  NOTICE  icon.svg
.claude-plugin/marketplace.json      marketplace catalog (source: ./plugin)
tools/validate.py                    offline repository checks (not shipped)
tools/update-vendor.sh               re-vendor the ClickHouse rules (not shipped)
examples/findings.example.json       fixture the validator renders
.github/workflows/validate.yml       CI
```

Maintainer tools live outside `plugin/` on purpose, so they are never part of the installed or submitted bundle.

## Development

```bash
python3 tools/validate.py
claude plugin validate plugin --strict

# Render the fixture
python3 plugin/skills/clickhouse-audit/scripts/render_report.py \
  --findings examples/findings.example.json \
  --out examples/output/report.html --md-out examples/output/report.md
```

## Releasing

`main` is development. `release` is what the plugin directory tracks, with plugin path `plugin`.

1. Bump `version` in `plugin/.claude-plugin/plugin.json`.
2. Run `python3 tools/validate.py` and `claude plugin validate plugin --strict`.
3. Open a pull request from `main` to `release` and merge it.
4. Tag the merge commit and push the tag:
   ```bash
   git tag -a v<version> -m "v<version>"
   git push origin v<version>
   ```
5. Publish the new version in the directory portal, or let auto-publish handle a passing scan.

Never commit directly to `release`; it is protected and only takes merges from `main`.

## Updating the vendored ClickHouse rules

```bash
./tools/update-vendor.sh <commit-sha>
```

The script reapplies the local modification recorded in `plugin/skills/clickhouse-audit/references/vendor/clickhouse/VENDORED.md`.

## License

Apache-2.0. The vendored ClickHouse agent skills are Apache-2.0, Copyright ClickHouse, Inc. See `LICENSE` and `NOTICE`.
