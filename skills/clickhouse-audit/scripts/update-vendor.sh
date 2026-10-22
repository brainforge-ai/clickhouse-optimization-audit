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

# Local modification: drop the agent connection guidance, which reads
# credentials from environment variables. See VENDORED.md "Changes".
python3 - "$DEST/clickhouse-best-practices" <<'PY'
import re
import sys
from pathlib import Path

base = Path(sys.argv[1])
note = ("<!-- Modified by Brainforge: removed the agent connection section (agent-connect-mcp), "
        "which reads database credentials from environment variables. This plugin authenticates "
        "only through ClickHouse Cloud OAuth via the remote MCP server. -->\n\n")

(base / "rules" / "agent-connect-mcp.md").unlink(missing_ok=True)

agents = base / "AGENTS.md"
lines = agents.read_text().splitlines(keepends=True)
start = next((i for i, l in enumerate(lines) if l.startswith("### ") and "Connect AI Agents to ClickHouse" in l), None)
if start is not None:
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith(("### ", "## "))), len(lines))
    lines = lines[:start] + lines[end:]
lines = [l for l in lines if "Connect AI Agents to ClickHouse" not in l and "agent-connect-mcp" not in l]
agents.write_text(note + "".join(lines))

skill = base / "SKILL.md"
text = skill.read_text()
text = "\n".join(l for l in text.splitlines() if "agent-connect-mcp" not in l) + "\n"
skill.write_text(text)
PY

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
