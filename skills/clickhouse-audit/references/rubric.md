# Scoring, ranking, and `findings.json`

## Weights

| Severity | Weight |
| --- | --- |
| CRITICAL | 3 |
| HIGH | 2 |
| MEDIUM | 1 |

Sum the weights of all findings in an area.

| Area total | Score |
| --- | --- |
| Any CRITICAL finding, or total ≥ 6 | Red |
| 2–5 | Yellow |
| 0–1 | Green |

Areas: `infrastructure`, `schema`, `architecture`, `queries`, `cost`.

Pre-computation findings are scored under `queries`, so every finding belongs to a scored area. Keep the `query-mv-*` rule ID to show the link.

Cost scoring is derived from the cost drivers, not from a separate findings list:

| Potential reduction | Score |
| --- | --- |
| Storage > 20% or read volume > 30% | Red |
| Storage 10–20% or read volume 15–30% | Yellow |
| Below those | Green |

Do not double-count a finding. A pruning problem is one finding in `queries`; its cost effect appears in the Cost Drivers table, not as a second finding.

## Impact, confidence, effort

| Field | Values | Meaning |
| --- | --- | --- |
| `impact` | high / medium / low | Effect on latency, cost, or correctness if fixed |
| `confidence` | high / medium / low | How strongly the evidence supports the finding |
| `effort` | low / medium / high | Work to apply the fix safely |

Confidence rules:

- **high** — directly measured (parts count, type, DDL, granules ratio, read bytes).
- **medium** — inferred from a proxy (read/result ratio, name-based type heuristic, cache counters).
- **low** — requires an assumption the audit could not verify.

## Ranking

```
rank_score = impact_value × confidence_value ÷ effort_value
impact_value     = high 3, medium 2, low 1
confidence_value = high 3, medium 2, low 1
effort_value     = low 1, medium 2, high 3
```

Sort descending. Break ties in favour of CRITICAL, then lower effort.

## Rewrites

Take the top 3 findings by rank that have a safe rewrite. A finding without a safe rewrite is skipped; take the next one. Every rewrite carries `"review_note": "Review before applying"`.

## `findings.json` schema

Write exactly this shape. The HTML renderer reads it directly. `scope.window_days` is a number of days, or `null` for the full history the service retains.

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-10-20T12:00:00Z",
  "scope": {
    "service": "analytics-prod",
    "service_id": "e5b1...",
    "organization": "Brainforge",
    "tier": "Scale",
    "provider": "AWS",
    "region": "us-east-1",
    "window_days": 7,
    "window_start": "2026-10-13",
    "window_end": "2026-10-20",
    "databases": ["default"],
    "tables_audited": 42,
    "accessible": ["system.query_log", "system.parts", "system.tables", "system.columns"],
    "audit_queries": 38
  },
  "scores": {
    "infrastructure": "Yellow",
    "schema": "Red",
    "architecture": "Yellow",
    "queries": "Red",
    "cost": "Red"
  },
  "score_weights": {
    "infrastructure": 4,
    "schema": 9,
    "architecture": 4,
    "queries": 6,
    "cost": 0
  },
  "summary": "Three to four sentences. What is wasting the most, and what to fix first.",
  "findings": [
    {
      "id": "F1",
      "rule_id": "schema-pk-cardinality-order",
      "rule_ids": ["schema-pk-cardinality-order", "schema-pk-prioritize-filters"],
      "area": "Schema",
      "severity": "CRITICAL",
      "title": "Ordering key leads with a UUID",
      "object": "default.events",
      "evidence": "ORDER BY (event_id, ts); top 10 patterns prune 0 of 12,204 granules.",
      "impact": "high",
      "fix": "Reorder to (tenant_id, event_type, ts) in a new table, then backfill.",
      "effort": "high",
      "confidence": "high",
      "cost_impact": "high",
      "cost_note": "Reads 1.9 TB/day; expected to fall by about 70%."
    }
  ],
  "precomputation": [
    {
      "id": "P1",
      "title": "Daily tenant rollup",
      "replaces": ["F4"],
      "ddl": "CREATE MATERIALIZED VIEW ...",
      "patterns": ["SELECT tenant_id, toDate(ts), count() ..."],
      "expected_effect": "Replaces 38 full scans per day with a scan of a 2 GB rollup.",
      "effort": "medium",
      "confidence": "high"
    }
  ],
  "rewrites": [
    {
      "rank": 1,
      "finding_id": "F1",
      "title": "New ordering key for default.events",
      "before": "ORDER BY (event_id, ts)",
      "after": "ORDER BY (tenant_id, event_type, ts)",
      "why": "Aligns the key with the filters used by 8 of the top 10 patterns.",
      "expected_effect": "Cuts granules read on the heaviest pattern from 12,204 to under 400.",
      "measure": "EXPLAIN indexes = 1 <query> before and after the backfill.",
      "review_note": "Review before applying"
    }
  ],
  "cost": {
    "pricing_date": "2026-10",
    "pricing_source": "https://clickhouse.com/pricing",
    "plan": "Scale",
    "provider": "AWS",
    "region": "us-east-1",
    "measured": {
      "read_tb_per_day": 4.2,
      "read_tb_per_day_after": 1.3,
      "read_reduction_pct": 69,
      "storage_tb": 8.4,
      "storage_tb_after": 5.1,
      "storage_reduction_pct": 39,
      "parts_per_day": 4200,
      "cache_hit_pct": 41,
      "cache_target_pct": 80
    },
    "drivers": [
      {
        "driver": "Three tables never queried",
        "evidence": "0 reads, 1.8 TB stored",
        "finding_ids": ["F2"],
        "monthly_impact": "1.8 TB removed",
        "fix": "TTL 90 days, archive",
        "est_reduction_pct": 21,
        "confidence": "high"
      }
    ],
    "dollars": {
      "currency": "USD",
      "storage_monthly_savings": 45.54,
      "compute_monthly_savings": null,
      "compute_requires_shape_change": true,
      "total_low": 45.54,
      "total_high": 45.54,
      "excluded": ["backups", "egress", "ClickPipes"]
    }
  },
  "gaps": [
    {
      "area": "Queries",
      "gap": "EXPLAIN indexes = 1 unavailable",
      "why": "The MCP rejected EXPLAIN; pruning uses the read/result proxy."
    }
  ],
  "cta": {
    "text": "Want the full assessment? Brainforge can turn this audit into a scoped optimization plan.",
    "url": "https://www.brainforge.ai/free-consultation-call"
  }
}
```

Rules for the JSON:

- `dollars.compute_monthly_savings` is `null` unless a service-shape change is named.
- `cost.total_low` and `total_high` are the bounds of the estimate. If only storage is claimed, they are equal.
- `gaps` is required, even when empty.
- `scores.cost` is derived as above; `score_weights.cost` is `0`.
- Every finding has a `rule_id`. If a finding comes from the Playbook rather than a vendored rule, use a `playbook:` or `architecture-advisor:` prefix.
