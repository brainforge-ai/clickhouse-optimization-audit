# ClickHouse Optimization Audit — {{scope.service}}

**Generated:** {{generated_at}}  
**Window:** {{scope.window_days}} days ({{scope.window_start}} → {{scope.window_end}})  
**Service:** {{scope.service}} · **Tier:** {{scope.tier}} · **Provider/Region:** {{scope.provider}} / {{scope.region}}  
**Tables audited:** {{scope.tables_audited}} · **Audit queries:** {{scope.audit_queries}}

## 1. Scope

{{scope_narrative}}

- **Databases:** {{scope.databases}}
- **Accessible system tables:** {{scope.accessible}}
- **Not reviewed:** {{scope.not_reviewed}}

## 2. Executive summary

{{summary}}

## 3. Scorecard

| Area | Score | Weight | Why |
| --- | --- | --- | --- |
| Infrastructure | {{scores.infrastructure}} | {{score_weights.infrastructure}} | {{score_reasons.infrastructure}} |
| Schema | {{scores.schema}} | {{score_weights.schema}} | {{score_reasons.schema}} |
| Architecture | {{scores.architecture}} | {{score_weights.architecture}} | {{score_reasons.architecture}} |
| Queries | {{scores.queries}} | {{score_weights.queries}} | {{score_reasons.queries}} |
| Cost efficiency | {{scores.cost}} | 0 | {{score_reasons.cost}} |

## 4. Ranked findings

<!-- Repeat for each finding, highest rank first. -->

### {{finding.rank}}. {{finding.title}} — {{finding.severity}}

**Object:** `{{finding.object}}`  
**Rule:** `{{finding.rule_id}}` (also: {{finding.rule_ids}})  
**Impact:** {{finding.impact}} · **Confidence:** {{finding.confidence}} · **Effort:** {{finding.effort}}

**Evidence:** {{finding.evidence}}

**Fix:** {{finding.fix}}

**Cost impact:** {{finding.cost_note}}

## 5. Pre-computation opportunities

<!-- Repeat for each item in precomputation. Omit the section if empty. -->

### {{precomputation.title}}

Replaces: {{precomputation.replaces}}  
Expected effect: {{precomputation.expected_effect}}  
Effort: {{precomputation.effort}} · Confidence: {{precomputation.confidence}}

```sql
{{precomputation.ddl}}
```

Patterns it replaces:

```sql
{{precomputation.patterns}}
```

## 6. Cost drivers and savings

### Measured

| Term | Current | After fixes |
| --- | --- | --- |
| Read volume | {{cost.measured.read_tb_per_day}} TB/day | {{cost.measured.read_tb_per_day_after}} TB/day ({{cost.measured.read_reduction_pct}}%) |
| Storage (compressed) | {{cost.measured.storage_tb}} TB | {{cost.measured.storage_tb_after}} TB ({{cost.measured.storage_reduction_pct}}%) |
| Parts created | {{cost.measured.parts_per_day}}/day | — |
| Cache hit rate | {{cost.measured.cache_hit_pct}}% | target {{cost.measured.cache_target_pct}}% |

### Drivers

| Driver | Evidence | Monthly impact | Fix | Est. reduction | Confidence |
| --- | --- | --- | --- | --- | --- |
{{cost_driver_rows}}

### Estimate

- Storage savings: **${{cost.dollars.storage_monthly_savings}}/month**
- Compute savings: **{{cost_compute_line}}**
- Total estimate: **${{cost.dollars.total_low}}–${{cost.dollars.total_high}}/month**

> Estimate based on published ClickHouse Cloud rates ({{cost.plan}}, {{cost.provider}} {{cost.region}}) as of {{cost.pricing_date}}. Not a quote. Verify at clickhouse.com/pricing. Excludes {{cost.dollars.excluded}}.

## 7. Top 3 rewrites

<!-- Repeat for each rewrite. -->

### {{rewrite.rank}}. {{rewrite.title}}

**Finding:** {{rewrite.finding_id}}  
**Why:** {{rewrite.why}}  
**Expected effect:** {{rewrite.expected_effect}}

**Before**

```sql
{{rewrite.before}}
```

**After**

```sql
{{rewrite.after}}
```

**Measure:** {{rewrite.measure}}

> {{rewrite.review_note}}

## 8. Gaps

<!-- Repeat for each gap. If none: "No gaps. All checks ran with available permissions." -->

- **{{gap.area}}:** {{gap.gap}} — {{gap.why}}

## 9. Next step

{{cta.text}}

[Book the assessment]({{cta.url}})

---

*Read-only audit. No data was modified. Query literals were redacted. Findings cite ClickHouse best-practice rules vendored under Apache-2.0.*
