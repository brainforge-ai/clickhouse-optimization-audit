# Cost model

Cost is reported twice: measured units first, estimated dollars second. Dollars are only claimed where the arithmetic supports them.

## 1. Measured terms (always shown)

| Term | Source |
| --- | --- |
| Read volume per day | `sum(read_bytes)` from `system.query_log` ÷ window days ÷ 1e12, in TB/day |
| Read volume after fixes | Sum of the projected read reduction from ranked findings |
| Storage (compressed) | `sum(bytes_on_disk)` from active parts ÷ 1e12, in TB |
| Storage after fixes | Storage minus the projected removal from TTL, drop, types, and codecs |
| Parts created per day | `system.parts` creation over the window, or insert count when parts history is unavailable |
| Cache hit rate | `ProfileEvents` cache vs source reads |

These are measurements, not estimates. Show them even when no dollar figure is claimed.

## 2. Dollar estimate

Use the pinned file in `references/pricing/` for the plan, provider and region.

```
storage_month = compressed_TB × storage_rate_per_TB
storage_savings = (TB_before − TB_after) × storage_rate_per_TB
```

Storage savings are direct arithmetic. Confidence: high.

```
units = RAM_GB ÷ 8
compute_month = units × active_hours × rate × replicas
compute_savings =
  (units_before × hours_before × replicas_before − units_after × hours_after × replicas_after) × rate
```

Compute savings are claimed **only** when a finding names a service-shape change:

- fewer replicas,
- smaller memory per replica,
- more idle time, or
- splitting a mixed workload into separate compute services.

If none of those is named, set `compute_monthly_savings` to `null` and report **headroom**: faster queries and lower peak load, with no direct dollar saving at the current shape.

Never multiply saved bytes by a compute rate. Bytes are not the billing unit.

## 3. Active hours

| Situation | Hours to use |
| --- | --- |
| Always on | 732 |
| Scales to zero when idle | Hours with activity from the query log, rounded up to the nearest hour, stated as an assumption |
| User states a schedule | The stated schedule |

If the audit cannot tell, use 732 and state the assumption. A wrong lower number overstates savings.

## 4. Worked example

Scale, AWS us-east-1, 2 replicas × 16 GiB, always on.

```
compute = (16 ÷ 8) × 732 × 0.29846 × 2 = $873.88/month
storage = 8.4 TB × 25.30 = $212.52/month
```

Findings: remove 3.3 TB and move from 16 GiB to 12 GiB per replica.

```
storage savings = 3.3 × 25.30 = $83.49/month
compute after   = (12 ÷ 8) × 732 × 0.29846 × 2 = $655.42/month
compute savings = 873.88 − 655.42 = $218.46/month
total           = $301.95/month
```

Only include the compute line if the report also says which evidence supports 16 → 12 GiB.

## 5. Reporting rules

- Round dollars to the nearest dollar in Markdown and HTML; keep cents in `findings.json`.
- Give a low/high range when the shape change is a scenario. Low = storage only. High = storage + compute.
- Every figure carries: “Estimate based on published ClickHouse Cloud rates as of <date>. Not a quote. Verify at clickhouse.com/pricing.”
- Name the excluded items: backups, egress, ClickPipes.
- If the plan or region is unknown, ask before producing dollars. If the user declines, show measured units only.

## 6. Confidence

| Claim | Confidence |
| --- | --- |
| Storage removed by dropping or TTL | high |
| Storage reduced by types or codecs | medium |
| Compute reduced by a named shape change | medium |
| Compute reduced without a shape change | not claimed |
| Read-volume reduction | high for measured patterns, medium for projections |
