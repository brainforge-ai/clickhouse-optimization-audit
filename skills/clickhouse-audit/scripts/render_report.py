#!/usr/bin/env python3
"""Render the self-contained HTML report from findings.json.

Usage:
  python3 render_report.py --findings findings.json --template report-template.html --out report.html
  python3 render_report.py --findings findings.json --check
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PLACEHOLDER = "__FINDINGS_JSON__"
SCORES = {"Red", "Yellow", "Green"}
AREAS = ("infrastructure", "schema", "architecture", "queries", "cost")
SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM"}
FINDING_AREAS = {"infrastructure", "schema", "architecture", "queries", "cost"}
LEVELS = {"high", "medium", "low"}
REQUIRED_FINDING = (
    "id", "rule_id", "area", "severity", "title", "object",
    "evidence", "impact", "fix", "effort", "confidence",
)


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def load_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        fail(f"findings file not found: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")
    if not isinstance(data, dict):
        fail("findings.json must be a JSON object")
    return data


def validate(data: dict) -> list[str]:
    problems: list[str] = []

    if data.get("schema_version") != "1.0":
        problems.append('schema_version must be "1.0"')

    scope = data.get("scope")
    if not isinstance(scope, dict):
        problems.append("scope must be an object")
    else:
        for key in ("service",):
            if scope.get(key) in (None, ""):
                problems.append(f"scope.{key} is required")
        days = scope.get("window_days", "__missing__")
        if days == "__missing__":
            problems.append("scope.window_days is required (a number of days, or null for full available history)")
        elif days not in (None, ""):
            if not isinstance(days, int) or days < 1:
                problems.append("scope.window_days must be a positive integer, or null for full available history")

    scores = data.get("scores")
    if not isinstance(scores, dict):
        problems.append("scores must be an object")
    else:
        for area in AREAS:
            if scores.get(area) not in SCORES:
                problems.append(f"scores.{area} must be one of {sorted(SCORES)}")

    areas = data.get("areas")
    if areas is not None:
        if not isinstance(areas, dict):
            problems.append("areas must be an object")
        else:
            for key, value in areas.items():
                if key not in AREAS:
                    problems.append(f"areas.{key} is not a scored area")
                    continue
                if not isinstance(value, dict):
                    problems.append(f"areas.{key} must be an object")
                    continue
                for field in value:
                    if field not in ("summary", "checked", "impact"):
                        problems.append(f"areas.{key}.{field} is not a recognised field")
                for field in ("summary", "impact"):
                    if field in value and not isinstance(value[field], str):
                        problems.append(f"areas.{key}.{field} must be a string")
                if "checked" in value and not (
                    isinstance(value["checked"], list)
                    and all(isinstance(item, str) for item in value["checked"])
                ):
                    problems.append(f"areas.{key}.checked must be an array of strings")

    not_run = data.get("checks_not_run")
    if not isinstance(not_run, list):
        problems.append("checks_not_run is required (use [] when every check ran)")
    else:
        for index, item in enumerate(not_run):
            if not isinstance(item, dict):
                problems.append(f"checks_not_run[{index}] must be an object")
                continue
            for key in ("area", "check", "why"):
                if not isinstance(item.get(key), str) or not item.get(key).strip():
                    problems.append(f"checks_not_run[{index}].{key} must be a non-empty string")

    findings = data.get("findings")
    if not isinstance(findings, list):
        problems.append("findings must be an array")
    else:
        for index, finding in enumerate(findings):
            if not isinstance(finding, dict):
                problems.append(f"findings[{index}] must be an object")
                continue
            if finding.get("metric") is not None and not isinstance(finding.get("metric"), str):
                problems.append(f"findings[{index}].metric must be a string")
            for key in REQUIRED_FINDING:
                if finding.get(key) in (None, ""):
                    problems.append(f"findings[{index}].{key} is required")
            if finding.get("severity") not in SEVERITIES:
                problems.append(f"findings[{index}].severity must be one of {sorted(SEVERITIES)}")
            if str(finding.get("area", "")).lower() not in FINDING_AREAS:
                problems.append(f"findings[{index}].area must be one of {sorted(FINDING_AREAS)}")
            for key in ("impact", "effort", "confidence"):
                if finding.get(key) not in LEVELS:
                    problems.append(f"findings[{index}].{key} must be one of {sorted(LEVELS)}")

    cost = data.get("cost")
    if not isinstance(cost, dict):
        problems.append("cost must be an object")
    else:
        dollars = cost.get("dollars")
        if isinstance(dollars, dict):
            if dollars.get("compute_monthly_savings") is not None and not dollars.get("compute_requires_shape_change"):
                problems.append(
                    "cost.dollars.compute_monthly_savings is set but no service-shape change is claimed"
                )
        else:
            warn("cost.dollars is missing; the report will show measured terms only")

    rewrites = data.get("rewrites")
    if not isinstance(rewrites, list):
        problems.append("rewrites must be an array")
    else:
        for index, rewrite in enumerate(rewrites):
            if not isinstance(rewrite, dict):
                problems.append(f"rewrites[{index}] must be an object")
                continue
            for key in ("rank", "finding_id", "title", "before", "after", "why", "expected_effect", "measure"):
                if rewrite.get(key) in (None, ""):
                    problems.append(f"rewrites[{index}].{key} is required")
    if not isinstance(data.get("gaps"), list):
        problems.append("gaps must be an array")
    if not isinstance(data.get("cta"), dict):
        problems.append("cta must be an object")

    # --- arithmetic and scoring consistency ---
    weights = data.get("score_weights") if isinstance(data.get("score_weights"), dict) else {}
    findings = data.get("findings") if isinstance(data.get("findings"), list) else []
    severity_weight = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1}
    area_findings = {area: [] for area in AREAS}
    seen_ids = set()
    for finding in findings:
        area = str(finding.get("area", "")).lower()
        if area in area_findings:
            area_findings[area].append(finding)
        finding_id = finding.get("id")
        if finding_id in seen_ids:
            problems.append(f"duplicate finding id: {finding_id}")
        seen_ids.add(finding_id)

    for area in AREAS:
        total = sum(severity_weight.get(str(f.get("severity", "")).upper(), 0) for f in area_findings[area])
        if area != "cost" and isinstance(weights.get(area), int) and weights[area] != total:
            problems.append(f"score_weights.{area} is {weights[area]} but its findings sum to {total}")
        if area == "cost":
            continue
        expected = "Red" if any(str(f.get("severity", "")).upper() == "CRITICAL" for f in area_findings[area]) or total >= 6 else ("Yellow" if total >= 2 else "Green")
        if scores.get(area) != expected:
            problems.append(f"scores.{area} is {scores.get(area)} but the rubric gives {expected} from weight {total}")

    cost = data.get("cost") if isinstance(data.get("cost"), dict) else {}
    measured = cost.get("measured") if isinstance(cost.get("measured"), dict) else {}
    storage_pct = measured.get("storage_reduction_pct")
    read_pct = measured.get("read_reduction_pct")
    if isinstance(storage_pct, (int, float)) or isinstance(read_pct, (int, float)):
        s_pct = storage_pct if isinstance(storage_pct, (int, float)) else 0
        r_pct = read_pct if isinstance(read_pct, (int, float)) else 0
        expected_cost = "Red" if (s_pct > 20 or r_pct > 30) else ("Yellow" if (10 <= s_pct <= 20 or 15 <= r_pct <= 30) else "Green")
        if scores.get("cost") != expected_cost:
            problems.append(f"scores.cost is {scores.get('cost')} but measured reductions give {expected_cost}")

    for label, before_key, after_key, pct_key in (
        ("storage", "storage_tb", "storage_tb_after", "storage_reduction_pct"),
        ("read", "read_tb_per_day", "read_tb_per_day_after", "read_reduction_pct"),
    ):
        before = measured.get(before_key)
        after = measured.get(after_key)
        claimed = measured.get(pct_key)
        if isinstance(before, (int, float)) and isinstance(after, (int, float)) and isinstance(claimed, (int, float)) and before:
            calculated = (before - after) / before * 100
            if abs(calculated - claimed) > 1.0:
                problems.append(f"measured.{pct_key} is {claimed} but {before_key} and {after_key} give {round(calculated, 1)}")

    dollars = cost.get("dollars") if isinstance(cost.get("dollars"), dict) else {}
    storage_savings = dollars.get("storage_monthly_savings")
    compute_savings = dollars.get("compute_monthly_savings")
    total_low = dollars.get("total_low")
    total_high = dollars.get("total_high")
    if isinstance(storage_savings, (int, float)) and isinstance(total_low, (int, float)) and compute_savings is None:
        if abs(total_low - storage_savings) > 0.01:
            problems.append("dollars.total_low must equal storage savings when compute savings are null")
    if compute_savings is None and isinstance(total_low, (int, float)) and isinstance(total_high, (int, float)) and abs(total_high - total_low) > 0.01:
        problems.append("dollars.total_low and total_high must match when compute savings are null")
    if isinstance(total_low, (int, float)) and isinstance(total_high, (int, float)) and total_high < total_low:
        problems.append("dollars.total_high is below total_low")

    level = {"high": 3, "medium": 2, "low": 1}
    for finding in findings:
        claimed_rank = finding.get("rank_score")
        if isinstance(claimed_rank, (int, float)):
            impact = level.get(str(finding.get("impact", "")).lower(), 0)
            confidence = level.get(str(finding.get("confidence", "")).lower(), 0)
            effort = level.get(str(finding.get("effort", "")).lower(), 0) or 1
            calculated_rank = impact * confidence / effort
            if abs(calculated_rank - claimed_rank) > 0.01:
                problems.append(f"finding {finding.get('id')}: rank_score is {claimed_rank} but impact x confidence / effort gives {round(calculated_rank, 2)}")

    known_ids = {finding.get("id") for finding in findings}
    for index, rewrite in enumerate(data.get("rewrites") or []):
        finding_id = rewrite.get("finding_id") if isinstance(rewrite, dict) else None
        if finding_id and finding_id not in known_ids:
            problems.append(f"rewrites[{index}].finding_id {finding_id} is not in findings")
        if isinstance(rewrite, dict) and "CREATE TABLE" in str(rewrite.get("after", "")).upper() and not rewrite.get("basis"):
            problems.append(f"rewrites[{index}] creates a table but has no basis; add basis such as system.columns for db.table")

    return problems


def embed(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    # Prevent </script> from closing the JSON block, and escape JS line separators.
    payload = payload.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return payload


def render(findings: Path, template: Path, out: Path) -> None:
    data = load_json(findings)
    problems = validate(data)
    if problems:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        raise SystemExit(2)

    try:
        html = template.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"template not found: {template}")

    if html.count(PLACEHOLDER) != 1:
        fail(f"template must contain exactly one {PLACEHOLDER} placeholder")

    rendered = html.replace(PLACEHOLDER, embed(data))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size:,} bytes)")



def _list(value) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return "" if value is None else str(value)


def _window_label(scope: dict) -> str:
    days = scope.get("window_days")
    if days in (None, ""):
        return "All available history"
    return f"{days} days"


def _num(value, digits: int = 0) -> str:
    if value is None or value == "":
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if digits:
        return f"{number:,.{digits}f}"
    return f"{number:,.0f}"


def render_markdown(data: dict) -> str:
    scope = data.get("scope", {})
    scores = data.get("scores", {})
    weights = data.get("score_weights", {})
    cost = data.get("cost", {})
    measured = cost.get("measured", {})
    dollars = cost.get("dollars", {})
    service = scope.get("service", "service")
    generated = data.get("generated_at", "")

    lines: list[str] = []
    lines.append(f"# ClickHouse Optimization Audit — {service}")
    lines.append("")
    lines.append(f"**Generated:** {generated}  ")
    lines.append(f"**Window:** {_window_label(scope)} ({scope.get('window_start', '')} → {scope.get('window_end', '')})  ")
    lines.append(f"**Service:** {service} · **Tier:** {scope.get('tier', '—')} · **Provider/Region:** {scope.get('provider', '—')} / {scope.get('region', '—')}  ")
    lines.append(f"**Tables audited:** {scope.get('tables_audited', '—')} · **Audit queries:** {scope.get('audit_queries', '—')}")
    lines.append("")

    lines.append("## Scope")
    lines.append("")
    lines.append(f"- **Databases:** {_list(scope.get('databases')) or '—'}")
    lines.append(f"- **Accessible system tables:** {_list(scope.get('accessible')) or '—'}")
    lines.append("")

    lines.append("## Executive summary")
    lines.append("")
    lines.append(data.get("summary", ""))
    lines.append("")

    lines.append("## Scorecard")
    lines.append("")
    lines.append("| Area | Score | Weight |")
    lines.append("| --- | --- | --- |")
    for key, label in (
        ("infrastructure", "Infrastructure"),
        ("schema", "Schema"),
        ("architecture", "Architecture"),
        ("queries", "Queries"),
        ("cost", "Cost efficiency"),
    ):
        weight = "derived" if key == "cost" else weights.get(key, "—")
        lines.append(f"| {label} | {scores.get(key, '—')} | {weight} |")
    lines.append("")

    lines.append("## Category detail")
    lines.append("")
    findings = data.get("findings", [])
    areas = data.get("areas") if isinstance(data.get("areas"), dict) else {}
    for key, label in (
        ("infrastructure", "Infrastructure"),
        ("schema", "Schema"),
        ("architecture", "Architecture"),
        ("queries", "Queries"),
        ("cost", "Cost efficiency"),
    ):
        status = scores.get(key, "—")
        area_findings = [f for f in findings if str(f.get("area", "")).lower() == key]
        note = areas.get(key) if isinstance(areas.get(key), dict) else {}
        weight = "derived" if key == "cost" else weights.get(key, "—")
        items = area_findings
        if not items and key == "cost":
            items = [
                {
                    "title": driver.get("driver", ""),
                    "object": "",
                    "metric": driver.get("monthly_impact", ""),
                    "evidence": driver.get("evidence", ""),
                    "fix": driver.get("fix", ""),
                }
                for driver in cost.get("drivers", [])
            ]
        plural = "" if len(items) == 1 else "s"
        detail = (f"derived, {len(items)} driver{plural}" if key == "cost" else f"score {weight}, {len(items)} finding{plural}")
        lines.append(f"### {label} — {status} ({detail})")
        lines.append("")
        summary = note.get("summary") or (
            f"The audit found {len(items)} issue{plural} in this area."
            if items else "No issues found in this area."
        )
        lines.append(f"**What we found.** {summary}")
        checked = note.get("checked")
        if isinstance(checked, list) and checked:
            lines.append(f"Checked: {', '.join(str(c) for c in checked)}.")
        lines.append("")
        lines.append("**Issues**")
        if items:
            for finding in items:
                metric = finding.get("metric") or finding.get("cost_note") or ""
                suffix = f" — {metric}" if metric else ""
                obj = f" (`{finding.get('object', '')}`)" if finding.get("object") else ""
                lines.append(f"- **{finding.get('title', '')}**{obj}{suffix}")
                if finding.get("evidence"):
                    lines.append(f"  - Evidence: {finding['evidence']}")
                if finding.get("false_positives"):
                    lines.append(f"  - Not an issue if: {finding['false_positives']}")
        else:
            lines.append("- None.")
        lines.append("")
        lines.append("**Recommendations**")
        if items:
            for finding in items:
                lines.append(f"- {finding.get('fix', '')}")
        else:
            lines.append("- No action required.")
        lines.append("")
        impact = note.get("impact") or ("" if items else "No material savings identified.")
        if not impact and key == "cost" and dollars.get("total_low") is not None:
            impact = f"About ${_num(dollars.get('total_low'), 2)}–${_num(dollars.get('total_high'), 2)} per month."
        if impact:
            lines.append(f"**Impact if improved.** {impact}")
            lines.append("")

    precomp = data.get("precomputation", [])
    if precomp:
        lines.append("## Pre-computation opportunities")
        lines.append("")
        for item in precomp:
            lines.append(f"### {item.get('title', '')}")
            lines.append("")
            lines.append(f"Replaces: {_list(item.get('replaces'))}  ")
            lines.append(f"Expected effect: {item.get('expected_effect', '')}  ")
            lines.append(f"Effort: {item.get('effort', '')} · Confidence: {item.get('confidence', '')}")
            lines.append("")
            if item.get("ddl"):
                lines.append("```sql")
                lines.append(str(item["ddl"]).strip())
                lines.append("```")
                lines.append("")

    lines.append("## Cost drivers and savings")
    lines.append("")
    lines.append("### Measured")
    lines.append("")
    lines.append("| Term | Current | After fixes |")
    lines.append("| --- | --- | --- |")
    lines.append(f"| Read volume | {_num(measured.get('read_tb_per_day'), 2)} TB/day | {_num(measured.get('read_tb_per_day_after'), 2)} TB/day ({_num(measured.get('read_reduction_pct'))}%) |")
    lines.append(f"| Storage (compressed) | {_num(measured.get('storage_tb'), 2)} TB | {_num(measured.get('storage_tb_after'), 2)} TB ({_num(measured.get('storage_reduction_pct'))}%) |")
    lines.append(f"| Parts created | {_num(measured.get('parts_per_day'))}/day | — |")
    lines.append(f"| Cache hit rate | {_num(measured.get('cache_hit_pct'), 1)}% | target {_num(measured.get('cache_target_pct'), 1)}% |")
    lines.append("")
    drivers = cost.get("drivers", [])
    if drivers:
        lines.append("### Drivers")
        lines.append("")
        lines.append("| Driver | Evidence | Monthly impact | Fix | Est. reduction | Confidence |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for driver in drivers:
            lines.append(
                f"| {driver.get('driver', '')} | {driver.get('evidence', '')} | {driver.get('monthly_impact', '')} | "
                f"{driver.get('fix', '')} | {_num(driver.get('est_reduction_pct'))}% | {driver.get('confidence', '')} |"
            )
        lines.append("")
    lines.append("### Estimate")
    lines.append("")
    if dollars.get("storage_monthly_savings") is not None:
        lines.append(f"- Storage savings: **${_num(dollars['storage_monthly_savings'], 2)}/month**")
    if dollars.get("compute_monthly_savings") is not None:
        lines.append(f"- Compute savings: **${_num(dollars['compute_monthly_savings'], 2)}/month**")
    else:
        lines.append("- Compute savings: **headroom only** — no service-shape change is claimed.")
    total_low = dollars.get("total_low")
    total_high = dollars.get("total_high")
    if total_low is not None and total_high is not None and total_low == total_high:
        lines.append(f"- Total estimate: **${_num(total_low, 2)}/month**")
    else:
        lines.append(f"- Total estimate: **${_num(total_low, 2)}–${_num(total_high, 2)}/month**")
    lines.append("")
    lines.append(
        f"> Estimate based on published ClickHouse Cloud rates "
        f"({cost.get('plan', '—')}, {cost.get('provider', '—')} {cost.get('region', '—')}) as of "
        f"{cost.get('pricing_date', '—')}. Not a quote. Verify at clickhouse.com/pricing. "
        f"Excludes {_list(dollars.get('excluded')) or 'backups, egress and ClickPipes'}."
    )
    lines.append("")

    rewrites = data.get("rewrites", [])
    if rewrites:
        lines.append("## Top rewrites")
        lines.append("")
        for rewrite in rewrites:
            lines.append(f"### {rewrite.get('rank', '')}. {rewrite.get('title', '')}")
            lines.append("")
            lines.append(f"**Finding:** {rewrite.get('finding_id', '')}  ")
            lines.append(f"**Why:** {rewrite.get('why', '')}  ")
            lines.append(f"**Expected effect:** {rewrite.get('expected_effect', '')}")
            lines.append("")
            lines.append("**Before**")
            lines.append("")
            lines.append("```sql")
            lines.append(str(rewrite.get("before", "")).strip())
            lines.append("```")
            lines.append("")
            lines.append("**After**")
            lines.append("")
            lines.append("```sql")
            lines.append(str(rewrite.get("after", "")).strip())
            lines.append("```")
            lines.append("")
            lines.append(f"**Measure:** {rewrite.get('measure', '')}")
            lines.append("")
            lines.append(f"> {rewrite.get('review_note', 'Review before applying')}")
            lines.append("")

    lines.append("## Gaps")
    lines.append("")
    not_run = data.get("checks_not_run", [])
    if not_run:
        lines.append("**Checks that did not run**")
        lines.append("")
        for item in not_run:
            lines.append(f"- {item.get('area', '')}: `{item.get('check', '')}` — {item.get('why', '')}")
        lines.append("")

    gaps = data.get("gaps", [])
    if gaps:
        for gap in gaps:
            lines.append(f"- **{gap.get('area', '')}:** {gap.get('gap', '')} — {gap.get('why', '')}")
    else:
        lines.append("No gaps. All checks ran with the permissions available.")
    lines.append("")

    cta = data.get("cta", {})
    lines.append("## Next step")
    lines.append("")
    lines.append(cta.get("text", "Want the full assessment? Brainforge can turn this audit into a scoped optimization plan."))
    lines.append("")
    if cta.get("url"):
        lines.append(f"[Book the assessment]({cta['url']})")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Read-only audit. No data was modified. Query literals were redacted. Findings cite ClickHouse best-practice rules vendored under Apache-2.0.*")
    lines.append("")
    return "\n".join(lines)


def open_report(path: Path) -> None:
    try:
        import webbrowser

        opened = webbrowser.open(path.resolve().as_uri())
        if opened:
            print(f"opened {path} in the default browser")
        else:
            print(f"could not open a browser; open {path} manually", file=sys.stderr)
    except Exception as exc:  # headless, no browser, or a blocked opener
        print(f"could not open a browser ({exc}); open {path} manually", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--findings", required=True, type=Path)
    parser.add_argument("--template", type=Path, default=Path(__file__).resolve().parent.parent / "references" / "report-template.html")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--md-out", type=Path, help="also write a Markdown report")
    parser.add_argument("--check", action="store_true", help="validate only, do not render")
    parser.add_argument("--open", dest="open_browser", action="store_true", help="open the HTML report in the default browser after writing it")
    args = parser.parse_args()

    if args.check:
        data = load_json(args.findings)
        problems = validate(data)
        if problems:
            for problem in problems:
                print(f"error: {problem}", file=sys.stderr)
            raise SystemExit(2)
        print(f"ok: {args.findings} is valid")
        return

    if not args.out:
        parser.error("--out is required unless --check is used")

    render(args.findings, args.template, args.out)

    if args.md_out:
        data = load_json(args.findings)
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(render_markdown(data), encoding="utf-8")
        print(f"wrote {args.md_out} ({args.md_out.stat().st_size:,} bytes)")

    if args.open_browser:
        open_report(args.out)


if __name__ == "__main__":
    main()
