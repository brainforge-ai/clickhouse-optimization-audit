#!/usr/bin/env bash
set -euo pipefail

# Re-vendor ClickHouse agent skills at a pinned commit.
# Usage: ./scripts/update-vendor.sh <commit-sha>

SHA="${1:-}"
if [[ -z "$SHA" ]]; then
  echo "usage: $0 <commit-sha>" >&2
  echo "tip: git ls-remote https://github.com/ClickHouse/agent-skills.git HEAD" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/references/vendor/clickhouse"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

git clone --quiet --filter=blob:none --no-checkout https://github.com/ClickHouse/agent-skills.git "$TMP/agent-skills"
git -C "$TMP/agent-skills" checkout --quiet "$SHA"

rm -rf "$DEST/clickhouse-best-practices" "$DEST/clickhouse-architecture-advisor"
cp -R "$TMP/agent-skills/skills/clickhouse-best-practices" "$DEST/"
cp -R "$TMP/agent-skills/skills/clickhouse-architecture-advisor" "$DEST/"
cp "$TMP/agent-skills/LICENSE" "$TMP/agent-skills/NOTICE" "$DEST/"

python3 - "$DEST/VENDORED.md" "$SHA" <<'PY'
import sys
from datetime import date
from pathlib import Path
path = Path(sys.argv[1])
sha = sys.argv[2]
text = path.read_text()
lines = []
for line in text.splitlines():
    if line.startswith("**Commit:**"):
        line = f"**Commit:** `{sha}`"
    elif line.startswith("**Vendored:**"):
        line = f"**Vendored:** {date.today().isoformat()}"
    lines.append(line)
path.write_text("\n".join(lines) + "\n")
PY

echo "vendored ClickHouse agent skills at $SHA"
echo "review the diff, then run: claude plugin validate --strict ."
