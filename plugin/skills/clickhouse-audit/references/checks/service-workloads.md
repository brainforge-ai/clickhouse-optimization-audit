# service-workloads

**Rule IDs:** `playbook:4-workload-isolation`, `playbook:4-sizing-and-scaling`, `architecture-advisor:decision-partitioning-timeseries`
**Area:** Service health
**Severity:** MEDIUM
**Evidence:** Workload queries 6 and 7, `get_service_details`

## Trigger

- Heavy analytical queries and sustained inserts share one service.
- Peak concurrency is a small fraction of capacity for most of the window.
- Long-running queries overlap peak ingest.
- One workload's memory spikes affect the other's latency.

## Why it matters

Mixing ingest and analytics on one compute service forces the service to be sized for the worst case. Separating compute while sharing storage lets each workload use the shape it needs.

## False positives

- Small services where separation costs more than it saves.
- Bursts that are rare and acceptable.

## Fix

Propose a warehouse split: a small ingest service and a separate analytical service sharing the same storage. Include the idle behavior for the analytical service. This is a recommendation only; the audit does not change services.

## Effort

Medium. Requires owner approval and a maintenance window.
