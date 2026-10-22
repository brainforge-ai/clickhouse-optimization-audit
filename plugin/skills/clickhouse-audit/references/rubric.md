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

Scored areas, by key and label:

| Key | Label |
| --- | --- |
| `service_health` | Service health |
| `data_model` | Data model & storage |
| `ingestion` | Ingestion & pipelines |
| `query_efficiency` | Query efficiency |
| `data_lifecycle` | Data lifecycle |

Pre-computation findings are scored under `query_efficiency`. Every finding belongs to exactly one scored area.

**Cost is not a scored area.** It is a derived panel: `cost.measured` holds the measured terms, `cost.drivers` holds one entry per saving with the finding IDs that cause it. A cost driver never repeats a finding.

A finding that is a correctness risk sets `"risk": true`. Examples: stale refreshable MV, failed dictionary, replication lag, TTL that deletes live data. Risk findings still score in their area; the flag only changes how the report labels them.

Do not double-count a finding. A pruning problem is one finding in `query_efficiency`; its cost effect appears in the Cost Drivers table, not as a second finding.

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

Sort descending. Break ties in favour of CRITICAL, then lower effort, then the larger measured footprint (bytes or read volume touched).

The `impact` label must match the measured footprint:

| Impact | Rule of thumb |
| --- | --- |
| high | More than 30% of the area's waste, or more than 100 GB/day of reads, or a correctness defect |
| medium | 5 to 30% of the waste, or 10 to 100 GB/day |
| low | Below 5%, or a single small table |

A threshold is a percentage of the service footprint with an absolute floor, never an absolute number alone. One gigabyte is large on a 10 GB service and noise on a 10 PB one.

## Rewrites

Take the top 3 findings by rank that have a safe rewrite. A finding without a safe rewrite is skipped; take the next one. Every rewrite carries `"review_note": "Review before applying"`.

## `findings.json` schema

Write exactly this shape. The HTML renderer reads it directly. `scope.window_days` is `null` for the default full-history run, or a number of days when the user picks a window.

```json
{
  "schema_version": "2.0",
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
    "service_health": "Yellow",
    "data_model": "Red",
    "ingestion": "Yellow",
    "query_efficiency": "Red",
    "data_lifecycle": "Red"
  },
  "score_weights": {
    "service_health": 4,
    "data_model": 9,
    "ingestion": 4,
    "query_efficiency": 6,
    "data_lifecycle": 2
  },
  "summary": "Three sentences. What is wasting the most, why, and the first action.",
  "areas": {
    "service_health": {
      "summary": "One sentence on what the audit checked and why the status is what it is.",
      "checked": ["active parts per table", "merge backlog", "service shape"],
      "impact": "One line on what fixing the area is worth. Use No material savings identified for a green area with none."
    },
    "data_model": {
      "summary": "One sentence.",
      "impact": "One line."
    }
  },
  "findings": [
    {
      "id": "F1",
      "rule_id": "schema-pk-cardinality-order",
      "rule_ids": ["schema-pk-cardinality-order", "schema-pk-prioritize-filters"],
      "area": "Data model & storage",
      "severity": "CRITICAL",
      "risk": false,
      "title": "Ordering key leads with a UUID",
      "object": "default.events",
      "metric": "12,204 granules read per query, 0 pruned",
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
      "basis": "system.columns for default.events",
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
  "checks_not_run": [
    {
      "area": "Queries",
      "check": "query-pruning",
      "why": "EXPLAIN rejected by the MCP; pruning proxy used instead."
    }
  ],
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

`areas` is required for every scored area. `summary` says what was checked and why the status is what it is, in one sentence. `impact` is one line, in plain English. `checked` is optional and is used for green areas, where it explains what the audit looked at.

`metric` is the one measured number a reader needs for the finding, for example `8.20 GB of 10.73 GB unread`. Keep it short. The full evidence stays in `evidence`.

Rules for the JSON:

- `dollars.compute_monthly_savings` is `null` unless a service-shape change is named.
- `cost.total_low` and `total_high` are the bounds of the estimate. If only storage is claimed, they are equal.
- `checks_not_run` is required, even when empty. An area with any entry cannot score Green.
- `gaps` is required, even when empty. Each gap states what is missing and the consequence for the score.
- `scores` has exactly the five scored keys. There is no `scores.cost`.
- `score_weights` matches the sum of finding weights per area. `data_lifecycle` weight comes from its findings, not from storage percentages.
- `risk` is optional and defaults to false.
- Every finding has a `rule_id`. If a finding comes from the Playbook rather than a vendored rule, use a `playbook:` or `architecture-advisor:` prefix.
