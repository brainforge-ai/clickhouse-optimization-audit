# ClickHouse Cloud pricing — pinned 2026-10

**Source:** https://clickhouse.com/pricing (retrieved 2026-10-20)
**Currency:** USD
**Month convention:** 732 hours (24 × 30.5)

These are published list rates, not a quote. ClickHouse can change them. Every report that uses this file shows this date and the source URL.

## Formula

```
compute/month = (RAM_GB ÷ 8) × active_hours × compute_unit_price × replicas
storage/month = compressed_TB × storage_price_per_TB
```

1 compute unit = 8 GiB RAM, 2 vCPU. Compute is metered per minute. Storage is metered on compressed bytes.

## Storage rates (all plans)

| Provider | Region | USD per TB-month |
| --- | --- | --- |
| AWS | us-east-1, us-east-2, us-west-2 | 25.30 |
| AWS | eu-west-1 | 25.30 |
| AWS | eu-west-2 | 26.40 |
| AWS | eu-central-1 | 26.95 |
| AWS | ap-northeast-1, ap-northeast-2, ap-south-1, ap-southeast-1, ap-southeast-2, ca-central-1, il-central-1 | 27.50 |
| Azure | eastus2, westus3 | 25.30 |
| Azure | germanywestcentral | 24.75 |
| GCP | us-central1, us-east1 | 22.00 |
| GCP | europe-west4, asia-southeast1 | 22.00 |
| GCP | europe-west2, asia-northeast1 | 25.30 |

## Compute rates — Enterprise ($ per compute-unit-hour)

| Provider | Region | Rate |
| --- | --- | --- |
| AWS | us-east-1 | 0.39030 |
| AWS | us-east-2 | 0.39030 |
| AWS | us-west-2 | 0.39030 |
| AWS | ca-central-1 | 0.43520 |
| AWS | eu-west-1 | 0.43520 |
| AWS | eu-west-2 | 0.45247 |
| AWS | eu-central-1 | 0.46974 |
| AWS | ap-northeast-2 | 0.48010 |
| AWS | ap-southeast-1 | 0.48701 |
| AWS | ap-southeast-2 | 0.49046 |
| AWS | ap-northeast-1 | 0.50428 |
| AWS | ap-south-1 | 0.42138 |
| AWS | il-central-1 | 0.45700 |
| Azure | eastus2 | 0.43138 |
| Azure | westus3 | 0.43138 |
| Azure | germanywestcentral | 0.51919 |
| GCP | us-central1 | 0.32727 |
| GCP | us-east1 | 0.32727 |
| GCP | europe-west4 | 0.36027 |
| GCP | asia-southeast1 | 0.39900 |
| GCP | europe-west2 | 0.41850 |
| GCP | asia-northeast1 | 0.42046 |

## Compute rates — Basic and Scale, AWS us-east-1 only

Derived from the worked examples on the pricing page (same page, 2026-10-20). The page publishes Basic and Scale examples only for AWS us-east-1, so do not apply these rates to other regions.

| Plan | USD per compute-unit-hour | Derivation |
| --- | --- | --- |
| Basic | 0.21809 | $39.91 ÷ (1 unit × 183 h) from the 6-hours-a-day example |
| Scale | 0.29846 | $436.95 ÷ (2 replicas × 732 h × 1 unit) |
| Enterprise | 0.39030 | $2,285.60 ÷ (2 replicas × 732 h × 4 units) |

## How to use these rates

1. Read plan, provider and region from `get_service_details`.
2. If all three are known, use the matching rate.
3. If the plan is Basic or Scale and the region is not AWS us-east-1, the rate is not published here. Ask the user, or use the Enterprise rate for that region as a conservative upper bound and set confidence to `low`.
4. If provider or region is unknown, ask. Do not guess.
5. If the pricing date is more than 90 days old, re-fetch the page and update this file.

## Excluded

Backups, data-transfer egress, and ClickPipes are billed separately and are not modeled. Name them as excluded in every report.

## Official examples used for verification

- Basic, 1 replica × 8 GiB, 6 h/day: compute $39.91; storage $25.30 for 500 GB data + 500 GB backup.
- Scale, 2 replicas × 16 GiB, always on: compute $873.89; storage $50.60 for 1 TB data + 1 TB backup.
- Enterprise, 2 replicas × 32 GiB, always on: compute $2,285.60; storage $253.00 for 5 TB data + 5 TB backup.

Use these to check the model before publishing a report.
