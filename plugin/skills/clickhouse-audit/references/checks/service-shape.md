# service-shape

**Rule IDs:** `playbook:4-sizing-and-scaling`, `playbook:4-workload-isolation`
**Area:** Service health
**Severity:** MEDIUM
**Evidence:** `get_service_details`, workload queries 6 and 7

## Trigger

- Sustained peak concurrency is far below the capacity the service is sized for, or
- A small ingest service and heavy analytical queries share one service, or
- The service is idle for most of the window but sized for peak.

## Why it matters

Compute is billed by size × active time × replicas. Matching shape to workload is the only direct way query optimization turns into dollars.

## False positives

- Short windows hide monthly peaks. Use 30 days when the user can.
- Scale-to-zero already handles idle services.
- Burst capacity may be a deliberate SLA choice.

## Fix

- Split ingest and analytics into separate compute services sharing storage.
- Reduce replicas or memory only when peak evidence supports it.
- Use autoscaling limits and idle behavior deliberately.

## Effort

Medium. This is a service-shape change and needs the owner's approval.
