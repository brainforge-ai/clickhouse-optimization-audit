"""Offline validation for the plugin repository (maintainer tool, not shipped in the plugin).

Does not need the Claude CLI. Checks the manifest, marketplace, MCP config,
referenced paths, skill frontmatter, HTML placeholder, and the sample render.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugin"
errors: list[str] = []
warnings: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{path.relative_to(ROOT)}: {exc}")
        return {}


plugin = load(PLUGIN / ".claude-plugin" / "plugin.json")
market = load(ROOT / ".claude-plugin" / "marketplace.json")
mcp = load(PLUGIN / ".mcp.json")
example = load(ROOT / "examples" / "findings.example.json")

name = plugin.get("name", "")
check(bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)), "plugin name must be kebab-case")
check(bool(plugin.get("version")), "plugin version is required")
check(bool(plugin.get("description")), "plugin description is required")
check(isinstance(plugin.get("author"), dict) and bool(plugin["author"].get("name")), "plugin author.name is required")
check(plugin.get("license") == "Apache-2.0", "plugin license should be Apache-2.0")
check("defaultEnabled" not in plugin, "plugin.json must not set defaultEnabled; use the marketplace entry")
for key in ("homepage", "repository"):
    value = plugin.get(key, "")
    check(value.startswith("https://"), f"{key} must be an absolute https URL")

check(bool(market.get("name")), "marketplace name is required")
check(isinstance(market.get("owner"), dict) and bool(market["owner"].get("name")), "marketplace owner.name is required")
entries = market.get("plugins") or []
check(len(entries) == 1, "marketplace should list exactly one plugin")
if entries:
    entry = entries[0]
    check(entry.get("name") == name, "marketplace entry name must match plugin.json name")
    source = entry.get("source")
    check(isinstance(source, str) and not source.startswith(".."), "marketplace source must be a relative path without ..")
    if isinstance(source, str):
        check((ROOT / source).resolve().exists(), f"marketplace source does not exist: {source}")

servers = mcp.get("mcpServers") or {}
check("clickhouse" in servers, "mcpServers.clickhouse is required")
if "clickhouse" in servers:
    server = servers["clickhouse"]
    check(server.get("type") == "http", "ClickHouse MCP server type must be http")
    check(str(server.get("url", "")).startswith("https://"), "ClickHouse MCP server url must be https")

SKILL = PLUGIN / "skills" / "clickhouse-audit"
skill = SKILL / "SKILL.md"
check(skill.exists(), "skills/clickhouse-audit/SKILL.md is required")
if skill.exists():
    text = skill.read_text(encoding="utf-8")
    check(text.startswith("---\nname: clickhouse-audit\n"), "skill frontmatter name must be clickhouse-audit")
    check("description:" in text.split("---", 2)[1], "skill frontmatter description is required")
    for token in ("get_organizations", "run_select_query", "Never call", "No row data"):
        check(token in text, f"skill is missing guardrail or tool reference: {token}")

check((PLUGIN / "commands" / "audit.md").exists(), "plugin/commands/audit.md is required")
check((PLUGIN / "README.md").exists(), "plugin/README.md is required for the directory listing")
check((PLUGIN / "LICENSE").exists(), "plugin/LICENSE is required for the directory listing")
icon = plugin.get("icon")
check(not icon or (PLUGIN / icon).exists(), f"plugin icon not found: {icon}")
check(not list(PLUGIN.rglob("validate.py")) and not list(PLUGIN.rglob("update-vendor.sh")), "maintainer tools must stay outside plugin/")

html = (SKILL / "references" / "report-template.html").read_text(encoding="utf-8")
check(html.count("__FINDINGS_JSON__") == 1, "HTML template needs exactly one __FINDINGS_JSON__ placeholder")
check("application/json" in html, "HTML template must embed findings as application/json")

checks_dir = SKILL / "references" / "checks"
check(len(list(checks_dir.glob("*.md"))) >= 20, "expected at least 20 check files")
for path in checks_dir.glob("*.md"):
    body = path.read_text(encoding="utf-8")
    if path.name[0].isdigit():
        continue
    check("**Rule IDs:**" in body, f"{path.name} is missing a Rule IDs line")
    check("## Trigger" in body, f"{path.name} is missing a Trigger section")
    check("## Fix" in body, f"{path.name} is missing a Fix section")
    check("## Effort" in body, f"{path.name} is missing an Effort section")

VALID_AREAS = {"Service health", "Data model & storage", "Ingestion & pipelines", "Query efficiency", "Data lifecycle"}
for path in checks_dir.glob("*.md"):
    if path.name[0].isdigit():
        continue
    body = path.read_text(encoding="utf-8")
    match = re.search(r"^\*\*Area:\*\* (.+)$", body, re.M)
    check(bool(match) and match.group(1).strip() in VALID_AREAS,
          f"{path.name}: Area must be one of {sorted(VALID_AREAS)}")

for stale in ("infra-", "schema-", "architecture-", "cost-", "precomputation-"):
    leftovers = list(checks_dir.glob(stale + "*.md"))
    check(not leftovers, f"old check prefix {stale} still present: {[p.name for p in leftovers]}")

vendor = SKILL / "references" / "vendor" / "clickhouse"
for required in ("LICENSE", "NOTICE", "VENDORED.md", "clickhouse-best-practices", "clickhouse-architecture-advisor"):
    check((vendor / required).exists(), f"vendored ClickHouse content missing: {required}")
if (vendor / "VENDORED.md").exists():
    vendored = (vendor / "VENDORED.md").read_text(encoding="utf-8")
    check(bool(re.search(r"\*\*Commit:\*\* `[0-9a-f]{40}`", vendored)), "VENDORED.md must pin a 40-character commit SHA")

pricing = list((SKILL / "references" / "pricing").glob("clickhouse-cloud-*.md"))
check(bool(pricing), "a dated pricing file is required")
if pricing:
    check("clickhouse.com/pricing" in pricing[0].read_text(encoding="utf-8"), "pricing file must cite its source")

if example:
    result = subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "render_report.py"), "--findings", str(ROOT / "examples" / "findings.example.json"), "--check"],
        capture_output=True,
        text=True,
    )
    check(result.returncode == 0, f"sample findings failed validation: {result.stderr.strip()}")

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        html_out = Path(tmp) / "report.html"
        md_out = Path(tmp) / "report.md"
        result = subprocess.run(
            [
                sys.executable, str(SKILL / "scripts" / "render_report.py"),
                "--findings", str(ROOT / "examples" / "findings.example.json"),
                "--out", str(html_out), "--md-out", str(md_out),
            ],
            capture_output=True,
            text=True,
        )
        check(result.returncode == 0, f"sample render failed: {result.stderr.strip()}")
        if html_out.exists():
            rendered = html_out.read_text(encoding="utf-8")
            check("__FINDINGS_JSON__" not in rendered, "rendered HTML still contains the placeholder")
            check("demo-analytics" in rendered, "rendered HTML is missing the service name")
        if md_out.exists():
            rendered_md = md_out.read_text(encoding="utf-8")
            check("# ClickHouse Optimization Audit" in rendered_md, "rendered Markdown is missing the title")
            check("## Category detail" in rendered_md, "rendered Markdown is missing category detail")
            check("### Service health" in rendered_md, "rendered Markdown is missing area blocks")


# --- Rule ID traceability ------------------------------------------------
best_rules = {x.stem for x in (vendor / "clickhouse-best-practices" / "rules").glob("*.md")}
arch_rules = {x.stem for x in (vendor / "clickhouse-architecture-advisor" / "rules").glob("*.md")}
for path in sorted(checks_dir.glob("*.md")):
    body = path.read_text(encoding="utf-8")
    for rule_id in set(re.findall(r"`((?:schema|query|insert)-[a-z0-9-]+)`", body)):
        check(rule_id in best_rules, path.name + ": unknown ClickHouse rule ID: " + rule_id)
    for rule_id in set(re.findall(r"`architecture-advisor:([a-z0-9-]+)`", body)):
        check(rule_id in arch_rules, path.name + ": unknown architecture-advisor rule: " + rule_id)

# --- SQL guardrail lint for the evidence library -------------------------
FORBIDDEN = re.compile(r"^\s*(insert|alter|create|drop|truncate|optimize|system|set)\b", re.IGNORECASE)
sql_blocks = 0
for path in sorted(checks_dir.glob("*.md")):
    text = path.read_text(encoding="utf-8")
    for match in re.finditer(r"```sql\n(.*?)```", text, re.DOTALL):
        block = match.group(1).strip()
        if not block:
            continue
        first = next((line.strip() for line in block.splitlines() if line.strip() and not line.strip().startswith("--")), "")
        if FORBIDDEN.match(first):
            errors.append(path.name + ": evidence SQL starts with a forbidden statement: " + first[:40])
            continue
        sql_blocks += 1
        check("bf_audit" in block, path.name + ": SQL block is missing the bf_audit tag")
        if first.upper().startswith("SELECT"):
            check("LIMIT" in block.upper(), path.name + ": SELECT block is missing LIMIT")
            check("max_execution_time" in block, path.name + ": SELECT block is missing max_execution_time")

for warning in warnings:
    print(f"warning: {warning}")
if errors:
    for error in errors:
        print(f"error: {error}")
    print(f"FAIL ({len(errors)} errors)")
    raise SystemExit(1)

print("PASS")
print(f"plugin: {name} {plugin.get('version')}")
print(f"checks: {len(list(checks_dir.glob('*.md')))} files")
print(f"vendored: {len(list(vendor.rglob('*')))} entries")
print(f"sql blocks linted: {sql_blocks}")
