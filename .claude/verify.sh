#!/usr/bin/env bash
# FieldGold verification gate.
#
# This repo's tests are NOT pytest tests. There is not a single `def test_*`
# or `class Test*` in tests/ — each suite is a standalone script with its own
# check() harness, run directly. `pytest tests/` collects nothing useful and,
# because these files execute at module scope (they stand up HTTP servers and
# launch browsers), collection would run them with their exit codes swallowed.
# Two of the thirteen suites are .js and pytest would never see them at all.
#
# On a PLAIN run every suite exits 0 on pass, 1 on failure. The split,
# inverted convention CLAUDE.md warns about applies ONLY inside each suite's
# `if MUTATE:` branch, so it does not affect this gate. Do not add --mutate
# here without reading that section first.
#
# This gate must never report green over a suite it did not run. If a
# prerequisite is missing it says which, names the suites that went unrun,
# and fails.

set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

NODE_SUITES=(tests/test_land_status.js tests/test_photo_land_context.js)
PY_SUITES=(
  tests/test_app_land_status.py
  tests/test_map_sites.py
  tests/test_offline_map.py
  tests/test_panel_reachability.py
  tests/test_photo_app.py
  tests/test_reactive_refresh.py
  tests/test_seed_drift.py
  tests/test_shell_divergence.py
  tests/test_stage_maps.py
  tests/test_state_claims.py
  tests/test_sw_lifecycle.py
)

FAILED=()
UNRUN=()

for s in "${NODE_SUITES[@]}"; do
  if node "$s" >/dev/null 2>&1; then echo "  ok    $s"; else echo "  FAIL  $s"; FAILED+=("$s"); fi
done

# playwright lives in .venv — the Homebrew python is externally managed
# (PEP 668) and must not be installed into.
PY=""
for cand in .venv/bin/python python3; do
  if "$cand" -c "import playwright" 2>/dev/null; then PY="$cand"; break; fi
done

if [ -z "$PY" ]; then
  echo "  playwright not importable by any python found."
  echo "  ${#PY_SUITES[@]} suites did NOT run:"
  printf '    %s\n' "${PY_SUITES[@]}"
  echo "  provision with: python3 -m venv .venv && .venv/bin/python -m pip install playwright"
  UNRUN=("${PY_SUITES[@]}")
else
  for s in "${PY_SUITES[@]}"; do
    if "$PY" "$s" >/dev/null 2>&1; then echo "  ok    $s"; else echo "  FAIL  $s"; FAILED+=("$s"); fi
  done
fi

echo
if [ ${#FAILED[@]} -eq 0 ] && [ ${#UNRUN[@]} -eq 0 ]; then
  echo "VERIFY PASSED — all $(( ${#NODE_SUITES[@]} + ${#PY_SUITES[@]} )) suites ran and passed"
  exit 0
fi

[ ${#FAILED[@]} -gt 0 ] && echo "FAILED: ${FAILED[*]}"
[ ${#UNRUN[@]} -gt 0 ] && echo "UNRUN:  ${#UNRUN[@]} suites (see above) — a skipped suite is not a pass"
exit 1
