# Changelog

## 1.0.1 — 2026-10-21

- Five scored areas by lever: Service health, Data model & storage, Ingestion & pipelines, Query efficiency, Data lifecycle. Cost is a derived panel, not a score.
- Full-service audit by default, over the full retained history. Preflight counts reconcile every list; nothing is sampled or truncated.
- Checks cover stale and never-read tables, duplicate tables, grain mismatch against existing aggregates, schema redundancy, query errors, replication, disk headroom, dictionaries and refreshable MV freshness.
- Measured numbers only. The renderer validates area scores, reduction percentages, dollar totals and rank scores.
- Rewrite sketches need a `basis` from `system.columns` and live in a collapsed appendix.
- Correctness risk flag, collapsible category report, and automatic browser open.
