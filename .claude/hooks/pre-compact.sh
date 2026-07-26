#!/usr/bin/env bash
# PreCompact hook.
# Fires immediately before conversation compaction.
# Purpose: compaction is lossy and silent. Snapshot the full transcript
# first so nothing is only ever recoverable from a summary.

set -uo pipefail
cd "$(dirname "$0")/../.." || exit 0

BACKUP_DIR=".claude/backups"
mkdir -p "$BACKUP_DIR"

STAMP=$(date +%Y%m%d-%H%M%S)
INPUT=$(cat)

# Hook input arrives as JSON on stdin, including transcript_path and trigger
# ("manual" or "auto").
TRANSCRIPT=$(printf '%s' "$INPUT" | python3 -c \
  'import json,sys; print(json.load(sys.stdin).get("transcript_path",""))' \
  2>/dev/null)
TRIGGER=$(printf '%s' "$INPUT" | python3 -c \
  'import json,sys; print(json.load(sys.stdin).get("trigger","unknown"))' \
  2>/dev/null)

DEST="$BACKUP_DIR/$STAMP-$TRIGGER"
mkdir -p "$DEST"

if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
  cp "$TRANSCRIPT" "$DEST/transcript.jsonl"
fi

[ -f STATE.md ] && cp STATE.md "$DEST/STATE.md"

git rev-parse HEAD > "$DEST/head.txt" 2>/dev/null
git status --short > "$DEST/dirty.txt" 2>/dev/null

exit 0
