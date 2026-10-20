---
description: Run a read-only ClickHouse Cloud optimization audit and write Markdown + HTML reports
argument-hint: "[service name] [window: all|1d|7d|30d|<days>d]"
---

Follow the `clickhouse-audit` skill in this plugin from start to finish.

Arguments: `$ARGUMENTS`

Defaults:
- Window: full retained history by default (`all`). Honour `1d`, `7d`, `30d` or a custom number of days; if retention is shorter, use what is available and state the actual range.
- Service: choose interactively from the user's organizations and services. Never guess.

Do not skip the scope confirmation, the read-only guardrails, or the saved-file outputs.
