# FieldGold — migration state

Last updated: 2026-07-26

## Active phase

**Phase 0 — Capacitor shell**

Goal: FieldGold launches from a real app icon on Alan's iPhone, with zero
changes to app code.

## Status

| Step | State |
|---|---|
| Capacitor installed | not started |
| `capacitor.config` webDir confirmed | decided — `"docs"`, contingent on Phase 0a |
| iOS platform added | not started |
| Builds in Xcode | not started |
| Signing configured | not started |
| Installed on device | not started |
| Launches and renders | not started |

## Verified facts

<!-- Append only. Each entry: claim + tier + date. -->
<!-- Example: Apple Developer Program enrolled [externally-verified] 2026-07-26 -->

- SessionStart hook fires and injects STATE.md [externally-verified] 2026-07-25

## Decisions made

- **`webDir` is `"docs"`.** GitHub Pages currently serves branch `main` at
  path `/`, and there is no `docs/` directory yet — so this value is not
  usable until Phase 0a moves the web assets. Pages maps `docs/` onto the
  site root, so the public URL is unchanged by that move.

  `"."` was rejected. `webDir` is the directory Capacitor copies into the
  native bundle, and at the repo root that sweeps `ios/`, `.git/`, `.claude/`,
  the `.0009-backup-*` directories, `tests/` and `tools/` into the app.

## Phase 0a — move web assets to docs/

A prerequisite that Phase 0 uncovered. Not in the original 0-4 plan.

Phase 0 cannot set a safe `webDir` until the web assets sit in a directory
that contains only web assets. Phase 0a does that move and nothing else.

Ordering: after Phase 0's `webDir` decision, before Phase 1.

| Step | State |
|---|---|
| Move web assets into `docs/` | not started |
| Flip Pages source `/` -> `/docs` | not started |
| Repoint test suites at the new web root | not started |
| Repoint `tools/build_loader.py` | not started |
| Full suite green | not started |

Known to break on the move (inspected 2026-07-26, no changes made):

- All 10 Python suites compute `ROOT = __file__.parent.parent` and serve it as
  the HTTP document root, then fetch `/map.html`, `/index.html`,
  `/load_rem_benches.html`. Those 404.
- ~17 direct `ROOT / "<file>"` joins across 8 suites — the mutation-injection
  targets. A mutant that cannot find its file aborts exit 2 rather than
  reporting a false pass.
- Both `.js` suites: `path.join(path.dirname(__dirname), 'fieldgold-data.js')`.
- `tools/build_loader.py` `_ROOT` — both `SRC`/`DST` and `DATA_JS` writes.
- `tests/test_seed_drift.py` copies those two files plus the generator by
  `ROOT/name`.
- `tests/test_state_claims.py:480` needs **both** roots in one tree: it
  copytrees the root and runs `tools/build_loader.py` inside it. This one
  needs a genuine `REPO` / `WEB` split, not a one-line constant change.

Not affected: in-app links, `manifest.json` (`start_url` and `scope` are
relative), the `sw.js` SHELL (all `./`-relative), and the service worker
registration. Served URLs are identical after the move, so the move alone
does not require a cache version bump.

## Open decisions

- Apple Developer Program ($99/yr) vs free 7-day provisioning.
  Free tier requires re-signing weekly — likely unworkable for field use.
  **Not yet decided.**

## Deliberately not built yet

These were considered and deferred. Do not start them without Alan saying so.

- MCP verification server (ARDF / BLM / USGS)
- iOS build automation in CI
- Any Phase 1-4 work

## Next action

Phase 0a: move the web assets to `docs/`, then install Capacitor.
