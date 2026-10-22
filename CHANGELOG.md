# Changelog

## 1.1.3 — 2026-10-22

- Move the plugin into `plugin/`. Maintainer tools (`validate.py`, `update-vendor.sh`), CI and fixtures stay outside it, so they are no longer installed or scanned as part of the plugin. Directory plugin path is now `plugin`.
- Split the README: `plugin/README.md` is the user guide; the root README covers the repository and releasing.

## 1.1.2 — 2026-10-22

- Remove the vendored "agent connect" guidance that read database credentials from environment variables. The plugin authenticates only through ClickHouse Cloud OAuth via MCP. Clears the directory's credential policy holds.
- Replace the PNG icon with an SVG of the Brainforge mark, so the directory can inspect it as text.

## 1.1.1 — 2026-10-21

- Add directory listing metadata: icon, documentation, support, privacy policy and terms URLs.
- Add a data handling section to the README for the directory's security review.

## 1.1.0 — 2026-10-21

- New checks: stuck mutations, insert backpressure, query-level settings, shard topology, TTL that does not delete, storage tiering, MergeTree settings, query cache, aggregate correctness, Kafka consumer lag.
- Unread-table recommendations now check views, MVs and dictionaries for dependents before suggesting a drop.
- Preflight reads the available `query_log` columns and disables checks that need a column this version lacks.
- Workload profile adds the hourly shape and labels read bytes as a sum across replicas and shards.
- Ranking breaks ties by measured footprint; impact guidance is percentage-first.

## 1.0.1 — 2026-10-21

- Five scored areas by lever: Service health, Data model & storage, Ingestion & pipelines, Query efficiency, Data lifecycle. Cost is a derived panel, not a score.
- Full-service audit by default, over the full retained history. Preflight counts reconcile every list; nothing is sampled or truncated.
- Checks cover stale and never-read tables, duplicate tables, grain mismatch against existing aggregates, schema redundancy, query errors, replication, disk headroom, dictionaries and refreshable MV freshness.
- Measured numbers only. The renderer validates area scores, reduction percentages, dollar totals and rank scores.
- Rewrite sketches need a `basis` from `system.columns` and live in a collapsed appendix.
- Correctness risk flag, collapsible category report, and automatic browser open.
