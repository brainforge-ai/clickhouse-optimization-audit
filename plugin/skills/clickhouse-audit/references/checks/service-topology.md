# service-topology

**Rule IDs:** `playbook:topology-fit`, `architecture-advisor:decision-partitioning-timeseries`
**Area:** Service health
**Severity:** MEDIUM
**Evidence:** `system.clusters`, `system.tables` with the `Distributed` engine

## Trigger

- More than one shard, and the audit's other checks assume a single shard.
- `Distributed` tables exist.
- `prefer_localhost_replica = 0` on a service with local replicas.
- A `Distributed` shard key that does not match the filters used by the top patterns.

```sql
/* bf_audit */
SELECT cluster, shard_num, replica_num, host_name, port
FROM system.clusters
ORDER BY cluster, shard_num, replica_num
LIMIT 500
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

```sql
/* bf_audit */
SELECT database, name, engine, engine_full, sorting_key
FROM system.tables
WHERE engine = 'Distributed'
  AND database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA', '_temporary_and_external_tables')
LIMIT 500
SETTINGS max_execution_time = 60, log_comment = 'bf_audit'
```

## Why it matters

On a single shard, read bytes and memory are one number. On many shards, each replica reports its own rows, and a `Distributed` query fans out. Without topology, the audit can under- or over-state read volume and memory, and can miss a shard key that sends every query to one shard.

## False positives

- A single-shard service, where the check is informational.
- A `Distributed` table that is genuinely used for cross-cluster reads only.

## Fix

- Align the shard key with the dominant filter, usually tenant or customer.
- Keep aggregations shard-local where possible.
- Set `prefer_localhost_replica = 1` for co-located reads.

## Effort

Low to document. High to change a shard key.
