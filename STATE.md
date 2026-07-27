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

## Phase 0 — open: does `webDir` exclude the stage maps?

**Filed, not solved. This is a Phase 0 decision and it blocks nothing in
Phase 0a.**

Phase 0a moves `stage1_map_test.html` … `stage5_map.html` into `docs/` along
with every other web asset, because they are published today and three suites
load them over HTTP. That puts them inside `webDir`, which means **they will
ship inside the iOS bundle.**

CLAUDE.md deliberately keeps them out of the `sw.js` SHELL. The reasoning
there: a cached stage map looks like FieldGold, carries no land-status layer,
and shows nothing at all — a browser offline error is the more honest outcome.
`tests/test_stage_maps.py` asserts their absence from SHELL so a future
"helpful" addition trips a test.

Bundling them reintroduces that risk by a different route. The bundle is not
the service worker cache — the mechanism is different and the SHELL assertion
still holds — but a person who reaches one of these pages on a phone cannot
tell the difference. They carry a red ARCHIVED BUILD STAGE banner, and nothing
in `index.html` links to them (zero references; direct URL only). That is the
mitigation that exists today. It was written for a browser bookmark, not for a
page shipped inside an app icon.

Phase 0 must decide one of:

- ship them and rely on the banner plus their unreachability, or
- exclude them from `webDir` — which means `webDir` is no longer simply
  "the directory Pages serves", and something has to enforce the difference.

Do not resolve this by quietly deleting the stage maps. They are the build
history of `map.html` and CLAUDE.md keeps them on purpose.

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

The procedure for the Capacitor half is
**`.claude/skills/phase-0-shell/SKILL.md`** — Capacitor init, `cap add ios`,
signing, provisioning, first device install. That file is how; this file is
how far. Update the tables above as its steps land, and record the tier
([self-tested] / [fetched] / [externally-verified]) under Verified facts.
Phase 0a has no runbook — the breakage inventory above is what there is.
