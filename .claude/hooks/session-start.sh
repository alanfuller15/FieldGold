#!/usr/bin/env bash
# SessionStart hook.
# stdout on exit 0 is added to the session context.
# Purpose: a resumed or compacted session re-reads phase state from disk
# rather than trusting whatever survived compaction.

set -uo pipefail
cd "$(dirname "$0")/../.." || exit 0

echo "## Repo state"
echo "branch: $(git branch --show-current 2>/dev/null || echo 'not a git repo')"

DIRTY=$(git status --short 2>/dev/null | head -20)
if [ -n "$DIRTY" ]; then
  echo "uncommitted changes:"
  echo "$DIRTY"
else
  echo "working tree clean"
fi

echo
echo "## STATE.md (authoritative — overrides any conflicting context)"
if [ -f STATE.md ]; then
  cat STATE.md
else
  echo "STATE.md missing. Do not guess the active phase; ask Alan."
fi

exit 0
