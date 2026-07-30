# FieldGold — repository guide

A static progressive web app carried into the field for gold prospecting in the
Hatcher Pass / Little Susitna area, Alaska. Served from GitHub Pages at
`alanfuller15.github.io/FieldGold/`.

## Ground rules for anyone (human or model) changing this repo

**This app is used offline, on a phone, in terrain, to decide where a person
physically walks.** That constrains everything below.

1. **No build step for the web app.** No bundler, no framework. Plain HTML,
   CSS and JS that a browser loads directly. If a change would require
   building the app's own source, the answer is no.

   Exception, scoped: the Capacitor native shell installs npm packages to
   produce the iOS wrapper. It does not transform app source — `webDir`
   points at the same files GitHub Pages serves today. This exception covers
   the shell only. It does not license a bundler or framework for app code.

   **What that exception does not answer: how app code reaches a plugin.**
   Phases 2, 3 and 4 all need one — SQLite, filesystem, background location.
   The shell exception covers *installing* those packages. It says nothing
   about app code *importing* from `node_modules`, and a bare module specifier
   normally needs a bundler, which is the thing this rule forbids. Two routes
   avoid one. **Neither is ratified; this is the state of the question, not a
   decision.**

   - **The Capacitor bridge global** — `window.Capacitor.Plugins.*` at runtime.
     No specifier is resolved and nothing is transformed, so it needs no new
     exception at all. Untested here for the specific plugins.
   - **An import map** — `<script type="importmap">`, plain markup, no build.
     Grounded rather than assumed: Safari shipped import maps in **16.4**
     (Apple's Safari release notes; the Can I Use and MDN entries for
     `script type=importmap` agree), and the device runs **26.5.2**, so the
     platform supports them. Three properties are load-bearing before anyone
     designs around it. The tag **rejects `src`, `async`, `defer`, `integrity`
     and `crossorigin`** — the JSON must be inline, so it is one copy per page,
     four pages, and four copies of anything drift apart. The same duplication
     already has to be managed for the per-page chrome markup that carries the
     back control. The map must be declared **before** any module that imports
     through it. And see the cross-reference under rule 6: **changing an import
     map changes what the browser loads with no diff in the importing module**,
     which is rule 6's signature failure arriving through a new mechanism.

   **Genuinely untested, and it must stay marked so: whether import maps
   resolve under `capacitor://localhost` in WKWebView.** Three web platform
   features have already behaved differently there — Service Worker absent
   entirely, `target="_blank"` handed to iOS and refused, `env(safe-area-inset-*)`
   reading 0 — so "Safari 16.4 supports it" is not the same claim as "it works
   in the shell." One command establishes it: load a page in the shell that
   declares a map and imports through it, and read whether the specifier
   resolved. **Establish that before Phase 2 designs around it.**
2. **No new runtime dependencies from a CDN.** The app must work with no signal.
   Anything fetched at page load is a failure mode at the trailhead.
3. **Never invent coordinates.** Latitude and longitude values in this repo trace
   back to a lidar-derived REM analysis and to DNR land-status queries. If a
   change moves a coordinate, that change is wrong unless the issue explicitly
   says otherwise and gives the source.
4. **Never soften a land-status warning.** Candidates are tiered clean /
   not-checked / avoid. "Not checked" must never be presented as safe, and
   "avoid" must never be quietly dropped from a list to make the UI tidier.

   **Routing is a way of deleting a page, the same way layout is a way of
   deleting text.** That is not a prediction; it is the next level of a class
   this repo has now hit four times, each at a different level, each shipping
   green through the suites of its day:

   | level | instance | how the warning was deleted |
   |---|---|---|
   | content | the **z-index tie** — `#panel` at 1000 against Leaflet's containers at 1000, broken by DOM order | 21 sample points inside warning text painted over on a 390x664 phone |
   | layout | the **unreachable tail** — no `max-height`, no scroller, body cannot scroll | 102 of 256 warning sample points physically unreachable. And the run log: `linesVisibleAtRest` **4 of 12**, the four that report nothing wrong |
   | control | the **untappable toggle** — auto-collapse at phone width, the reopen control at y=22..41 inside a 47px status bar | every warning in the panel unreadable, while the suite reported 291 of 291 reachable |
   | **perception** | **colour as the only channel** — a bench diamond's tier is its fill: `#4E9A5F` clean, `#D29A3A` unchecked, `#B2402F` avoid, with no glyph, no tooltip and no `title`. The tier is in words only inside the popup, behind a tap | under red-green colour vision deficiency clean and avoid converge, so the map shows encumbered ground as cleared. Filed as **Phase 1 item E** in `STATE.md`; verified there against the marker code, not assumed |

   Nothing was edited out in any of the four. The text was correct in the diff
   in all of them. **Phase 1 adds a fifth level — the page itself.** A router
   decides what is reachable, so a route that renders a bench list before its
   tier is resolved, a route that reaches the photo screen without its banner,
   or a screen that exists only on a route nothing links to, deletes a warning
   by the same mechanism one level up. The measurement trap comes with it:
   **a green obtained by a route the user does not have is not a green** — the
   reachability suite got that green by calling `classList.remove('collapsed')`,
   and a router offers an even easier way to make the same mistake, because a
   test can navigate to a route no control on screen reaches.

   **This app makes claims about LAND STATUS. It makes no claim about PHYSICAL
   SAFETY, and it must not be readable as making one.** Approved by Alan
   2026-07-29 as an addition to this rule.

   The gap it closes: everything above governs **legal encumbrance** — clean,
   not checked, avoid. None of it governs terrain. Meanwhile the app already
   plots physical hazards without naming them as such. **ARDF occurrences are
   documented mine workings**, which means shafts and adits, and the scan button
   draws them wherever the map is panned. The working reach is avalanche terrain
   with cold water, no cell coverage, and bears.

   **The asymmetry is what makes this a rule 4 matter and not a disclaimer.** An
   app that says ground is clean has implicitly said it is walkable. Being wrong
   about an encumbrance is a legal problem for the user; being wrong about
   terrain is a physical one. A `clean` tier that reads as "go here" is a
   softened warning by the same logic this rule already applies to "not checked"
   reading as safe.

   What the rule requires:

   - **A tier is visibly a statement about encumbrance and nothing else.**
     `clean` means "no claim found in the registers checked" — never "safe".
     `STATUS_META.clean.long` is already worded that way ("Land status checked —
     no closing order, lease or park boundary found"); the requirement is that
     nothing added later shortens it into a verdict on the ground.
   - **The app does not present physical hazard information it has not
     assessed, and does not imply it has assessed any.**
   - **ARDF occurrences are plotted as documented mine workings**, and whatever
     the app says about them must not read as a recommendation to visit. Same
     shape as the existing treatment of the terrain score and the federal claims
     layer: the information stays, it stops being the thing you read at a
     glance.

   **What this does NOT do, stated so a later session does not over-read it: it
   does not make FieldGold a safety system.** That is a different application
   requiring data this project does not have. This rule constrains what the app
   **claims**, not what it must provide. Do not read it as licence to add
   avalanche, weather or route-safety features, and do not read it as requiring
   them.

   A ship-gate rides with this and is recorded in `STATE.md` under "Ship gates":
   before this app is used by anyone other than Alan, the disclaimers need review
   by a lawyer familiar with recreational-use liability in Alaska. That is a
   gate, not a task, and nothing in this repo can discharge it.
5. **State uncertainty in the UI.** Where the data is unverified, the page says
   so. Do not remove those notices as "clutter"; they are the point.
6. **Never hand-edit a generated file.** `load_rem_benches.html` is written by
   `tools/build_loader.py`. Edit the STATUS table in the generator and re-run
   it (`python3 tools/build_loader.py`; running it twice is a byte-exact
   no-op). A hand edit survives until the next generator run and then vanishes
   with no diff to read, which is the exact failure the patch workflow exists
   to prevent.

   **The corollary, learned in 0007: a derived field must not be inheritable.**
   `SRC` and `DST` are the same file, so every derived field already present in
   the record the generator reads is the *previous run's own output*. Delete an
   assignment and the value keeps appearing on all 20 records — assertions
   green, output byte-identical, nothing to see. A mutation test that deleted
   `nb["state_claim"] = "none"` passed, which is how this was found. The
   generator now pops every name in `DERIVED` off the carried-forward dict
   before writing, so a field that stops being derived *disappears* and both
   the assertions and `tests/test_state_claims.py` catch it. `geo_score` and
   `geo_rank` are the deliberate exception — they must be inherited; the reason
   is recorded at their assignment. **If you add a derived field, add it to
   `DERIVED`.**

   **KNOWN GAP — Phase 4 cannot comply with this rule as written.** Filed
   2026-07-29, unresolved. Background location cannot be configured without
   **hand-maintained keys in Capacitor-generated iOS files**: the
   `UIBackgroundModes` entry and its usage-description string in
   `ios/App/App/Info.plist`, and the corresponding capability in
   `App.xcodeproj/project.pbxproj`. Both files are written by
   `npx cap add ios`. There is no config-as-code route recorded here that
   expresses them.

   **The `Package.resolved` carve-out does not cover this.** That one says
   ground rule 6 "is about hand-*editing* generated files, not about refusing
   to track a lock" — it licensed **tracking** a generated file. This is
   **editing** one. The distinction is the whole content of that carve-out and
   it does not stretch.

   The failure mode is this rule's own signature: **a regenerated project loses
   the key, background location silently stops, and there is no diff to read.**
   Same shape as a hand edit vanishing on the next generator run, and same
   shape as the 0007 inheritance bug — assertions green, nothing to see.

   **DRAFT wording, NOT RATIFIED — Alan has not approved this and drafting is
   not ratifying:**

   > *Exception, scoped: the background-mode entries in `ios/App/App/Info.plist`
   > and the corresponding capability in `project.pbxproj` are hand-maintained,
   > because Capacitor's config cannot express them. Each hand-maintained key is
   > listed in this file with its reason, and a test asserts its presence, so a
   > regenerated project that loses it fails rather than silently disabling
   > background location.*

   **The tripwire is the part that would make it an exception rather than a
   hole.** Without the presence assertion, the wording licenses exactly the
   silent loss this rule exists to catch. Do not adopt the first sentence
   without the last one.

   **Cross-reference — a second mechanism with this rule's failure signature.**
   An import map (see rule 1's exception) changes what the browser loads **with
   no diff in the importing module**. The `import` line is byte-identical, the
   bytes executed are different, and nothing in the changed file records it.
   That is this rule's failure arriving through a route rule 6 was not written
   about. If an import map ships, it is a file whose edits must be read as
   carefully as a generator's STATUS table.
7. **The model-facing prompt is not a safety control.** `VISION_PROMPT` in
   `index.html` is sent to a vision model along with a land-status block built
   by `FieldGoldData.landBriefForPrompt`. Instructing a model to withhold pan
   advice on encumbered ground is a request, not a guarantee. The control that
   actually holds is `landBanner()`, drawn by the app from
   `contextForPoint()` before the request is even sent. If you change this
   screen, the banner renders on every path — success, HTTP error, network
   failure, and re-opening an old photo — or the change is wrong.

   **"Before the request is even sent" is free today only because
   `contextForPoint()` is synchronous.** It reads `localStorage` and returns.
   Phase 2 removes that: plugin storage APIs are promise-based, so the read
   becomes a `Promise` and **there is a window in which the screen exists and
   the banner does not.** The required order is: **await context, draw banner,
   send.** The tempting inversion — fire the request, draw the banner when the
   read resolves — defeats the rule while looking like a performance
   improvement, because it puts a request for pan advice in flight over ground
   whose status the screen has not yet stated. It will also test green on a warm
   store, where the promise resolves before the response does. The consequence
   for design: the photo screen either awaits its context before it can send, or
   is handed an already-resolved context and never reads storage itself.

## Layout

Since Phase 0a (2026-07-27) **every web asset lives under `docs/`** and nothing
else does; `tests/` and `tools/` stay at the repo root and must never ship in
the app bundle. Paths below are written out in full, because the bare filenames
this table used to carry sent sessions looking at the repo root for files that
had moved.

| file | role |
|---|---|
| `docs/index.html` | entry point / launcher |
| `docs/fieldgold-data.js` | shared data layer — `localStorage` key `fieldgold_record` |
| `docs/load_rem_benches.html` | loads the 20 REM bench candidates with land status |
| `docs/bench_hunter.html` | bench working view |
| `docs/creek_manual.html` | reference text |
| `docs/map.html` | **the map.** The only field map screen |
| `docs/stage1_map_test.html` … `docs/stage5_map.html` | **archived build stages** of `map.html`, kept for history. Not field tools — see below |
| `docs/sw.js`, `docs/manifest.json`, `docs/icon-*.png` | PWA shell — offline caching and install |
| `docs/.nojekyll` | empty marker — keeps the Pages build deterministic. See the deploy section |
| `tools/build_loader.py` | **generator.** Holds the STATUS table — the land-status call for all 20 candidates with the reasoning for each — and writes **two** files from that one payload: `docs/load_rem_benches.html` in place, and the `REM_BENCHES` seed array inside `docs/fieldgold-data.js` between its BEGIN/END GENERATED markers. See "one payload, two files" below |
| `docs/vendor/leaflet/` | **vendored Leaflet 1.9.4** — not written here; see `docs/vendor/leaflet/PROVENANCE.md` |
| `.claude/verify.sh` | **the verification gate.** Runs all twelve suites plainly and refuses to report green over a suite it could not run |
| `capacitor.config.json` | Capacitor shell config — `appId` `io.github.alanfuller15.fieldgold`, `webDir` `docs`. The `appId` cannot change without a new app identity |
| `package.json`, `package-lock.json` | the scoped dependency exception in ground rule 1 — Capacitor CLI/core/ios only. Nothing here transforms app source |
| `ios/` | **generated by `npx cap add ios`.** Tracked, but `ios/.gitignore` (Capacitor's own) excludes build output and `App/App/public` — the web assets there are a *copy* of `docs/` regenerated by `npx cap sync`, and must never be tracked as a second source of truth. **`App/App.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved` is tracked on purpose** — Capacitor's `.gitignore` does not cover it (`git check-ignore` exits 1), so it is not ignored, merely easy to leave untracked. It is the SPM dependency lock. `CapApp-SPM/Package.swift` already pins `exact: "8.4.2"`, so what the lock adds is the **commit revision** `9b9fb0a` — a git tag is mutable and can be re-pointed upstream, so `exact:` fixes the version string and only the lock fixes the bytes. Same position that made Leaflet vendored and hash-verified: **dependencies are pinned, not floating.** Do not delete it as generated noise — it is regenerated by Xcode, but ground rule 6 is about hand-*editing* generated files, not about refusing to track a lock |
| `tests/` | **twelve suites, 501 assertions** — re-measured 2026-07-29 by running all twelve and summing each suite's own printed total (30/50 node; 30, 31, 39, 48, 29, 25, 15, **121**, 68, 15 python). `test_stage_maps.py` gained 12 in the BLM request-parameter tripwire. The figure here read 488. `test_land_status.js`, `test_photo_land_context.js` (node); `test_app_land_status.py`, `test_photo_app.py`, `test_map_sites.py`, `test_offline_map.py`, `test_seed_drift.py`, `test_stage_maps.py`, `test_state_claims.py`, `test_reactive_refresh.py`, `test_sw_lifecycle.py`, `test_panel_reachability.py` (playwright) — **eleven of the twelve** take `--mutate`, **68 mutants** (66 distinct names — `no-banner` and `stale-cache` each appear in two suites). `test_app_land_status.py` does not, and that gap is open. **The "all caught" run covered 63 of them.** Counted off the tree 2026-07-26: 57 mutants at `35adc6f`, 66 at `72e8815`, 66 on 2026-07-26, **68 on 2026-07-29** (+2 `claims-sr`/`claims-layer`, both verified caught by running all nine of that suite's mutants and reading a named FAILED line rather than only the exit code). The 63 was never the tree's count — three mutants have never appeared in a verified-all-caught run, and which three is not recorded. The conclusion that the 63 were caught still stands; only the number was wrong. **The exit convention is split and this file got it wrong twice** — verified empirically 2026-07-26 by running those 63. Inverting (caught → 0, survived → 1): `test_offline_map.py`, `test_sw_lifecycle.py`, `test_reactive_refresh.py`, `test_seed_drift.py`, `test_panel_reachability.py`. Exit 1 on any failure: `test_map_sites.py`, `test_photo_app.py`, `test_stage_maps.py`, `test_state_claims.py`, and both `.js` suites. **Do not read this table — run one known mutant per suite and observe the code.** Whatever a runner assumes, half the suites report the opposite, and the failure mode is a runner that prints green over a survived mutant. A mutation whose `replace()` matches nothing must abort with exit 2 rather than report a pass — but see below: exit 2 does not catch everything |

## Every document in this repo

Built from `git ls-files '*.md'` on 2026-07-26 and rebuilt with the same
command on 2026-07-28, not from memory. Until the first of those dates nothing
pointed at any of these, so a session reading this file never learned they
existed. A document nothing links to is a document nobody reads. The 2026-07-28
rebuild found **no orphans** — five documents, five rows, no `.md` in the tree
that this table does not name.

**Control: any new or moved `.md` gets its line here in the same change.**
Deliberately not "the same commit" — a pure-rename commit is the case that
forced the wording: Phase 0a moved `PROVENANCE.md` in a commit that had to stay
content-free to be reviewable as a move, so the index correction landed in the
commit after it. Rebuild the list with the command above rather than appending
from recollection — a hand-maintained index drifts exactly the way the counts
in the tests row did.

| document | lines | role |
|---|---|---|
| `CLAUDE.md` | 837 | this file — the whole brief for anyone changing the repo |
| `STATE.md` | 2853 | **source of truth for the active migration phase.** Read it first; do not infer phase from conversation history. Points at the phase-0 runbook for procedure |
| `PHASE1-DESIGN.md` | 797 | **the Phase 1 design — approved 2026-07-29, amended once since, nothing built.** Consolidation of the five documents into one, the working set (multi-point selection distinct from saved Sites), layer defaults and tile honesty, and the feature popup. `STATE.md` is how far; this is what the work is. Records the D7 scope ruling, N1–N3, five premises it had to correct against the tree, what survives from PR #6, and what it does not address. Not a web asset: it stays at the repo root and must never ship in `docs/` |
| `README.md` | 200 | the public-facing README, written for a prospector. What GitHub renders. Re-read 2026-07-28 against the moved tree — it names no file paths, so Phase 0a did not stale it |
| `docs/vendor/leaflet/PROVENANCE.md` | 137 | where the vendored Leaflet bytes came from and how they were verified. Moved into `docs/` with the bytes it documents in Phase 0a. Carries a 2026-07-28 correction: the `.gitattributes` it cited does not exist |
| `PRIOR-ART-PHASE1.md` | 719 | **the prior-art pass over `PHASE1-DESIGN.md`, run 2026-07-29 before any of it was built.** Six items in the protocol's report shape, both queries recorded verbatim for each. None returned "no prior art found". Two conflicts and four gaps are collected at the end, reported rather than resolved — the design was not amended by this pass |
| `.claude/skills/phase-0-shell/SKILL.md` | 210 | Phase 0 runbook — Capacitor init, `cap add ios`, signing, first device install. Defers to `STATE.md` for status |
| `.claude/agents/failure-classes.md` | 394 | **the one subagent.** Read-only; checks a change against this project's recorded failure classes and reports which one it may reintroduce, citing the instance. Added 2026-07-29. It has no expertise the base model lacks — its value is generator–evaluator separation, reliable recall of a fixed catalogue, and absorbing the reading. Entries cite `CLAUDE.md`/`STATE.md`; two sections are marked **added** because they are recorded but were not in the brief that established it. **A second agent is justified by an instance this one missed, not by a category** |
| `ios/App/CapApp-SPM/README.md` | 5 | **generated by `cap add ios`, not written here.** Five lines saying the SPM package hosts Capacitor's Swift dependencies and not to edit it. Indexed because the control above says every tracked `.md` gets a row, and a generated file is exactly the kind that otherwise accumulates unlisted. Regenerated by Capacitor — do not hand-edit (ground rule 6 applies) |

**The prior-art protocol is not in this repo, and that is deliberate.** It lives
in the `genesis` plugin and is invoked as **`genesis:prior-art`**. A project copy
existed briefly at `.claude/skills/prior-art/SKILL.md` — this repo was where the
protocol was first written — and it was **deleted 2026-07-29** once the plugin
generalised it: the plugin's version is a superset in substance, and two
protocols under one name would have drifted apart. Verified before deleting: both
were live, listed as `prior-art` (the fork) and `genesis:prior-art` (the plugin),
so which protocol you got depended on which name you typed.

What the deleted copy carried that a general protocol should not, kept here
because these are **bindings, not protocol**:

- **"Field vocabulary, not project vocabulary" means our vocabulary.** The names
  this repo invents and then cannot find prior art under: "working set", "view
  registry", "problem row", "land status", "the record".
- **"Label practitioner-only sources as a tier" means the three tiers in this
  file** — `[self-tested]` / `[fetched]` / `[externally-verified]` — and a
  search-result summary is not a fetch.
- **"A pattern is knowledge, a library is a dependency" is ground rule 1.** The
  protocol delivers the first and is never an argument for the second.
- **The recorded pass is `PRIOR-ART-PHASE1.md`.** Read it before running another
  one; six items, none of which returned "no prior art found".

What this index found when it was first built, both now fixed:

- **`README.md` was a two-line stub** (`# FieldGold` / `Prospecting app`) and
  was the only document GitHub rendered. The real 173-line README sat at
  `README_FieldGold.md`, which nothing linked to. Every correction made to it
  landed in a file no visitor saw. The real one is now `README.md`; the old
  path is deleted, having had no inbound references.
- **`STATE.md` and the phase-0 runbook were a pair that did not reference each
  other.** STATE.md named the next action; the runbook was how to perform it.
  They now link both ways, and the precedence is stated in both: the runbook
  is *how*, STATE.md is *how far*.

## The shared data layer

`fieldgold-data.js` exposes `FieldGoldData` with `get`, `put`, `replaceKind`,
`remove`, `readAll`, `onChange`, `seedREM`, and `KEY`. Records live under the single `localStorage` key
`fieldgold_record`. Every record has `id`, `kind`, `lat`, `lon`, `source`,
`created`; `kind` is one of `site`, `bench`, `occurrence`, `photo`. `put()`
upserts by `id`, so re-running a loader replaces its own entries rather than
duplicating them.

### Land status is part of the schema

`land_status` is a first-class field on bench records, tiered `clean` /
`unchecked` / `avoid`, with `statusOf`, `statusMeta`, `isAvoid`, `isVisitable`,
`sortByStatus` and `statusCounts` exposed alongside it. **Anything unrecognised
— a missing field, a typo, a null, a number, a record written by an older
version of a tool — normalises to `unchecked`, never to `clean`.** If you change
`normalizeStatus` or `statusOf` so an unknown value falls through to `clean`,
you have converted a data gap into a green light on a page read at a trailhead.

`stampStatus` applies the field on write, for `kind === 'bench'` only, and it
stamps **both registers** — `land_status` and `state_claim` — normalising each
independently. It is called from `put()`, from `replaceKind()`, and from the
seeder. A bench cannot enter the record without a tier on both, so a tool
written before either field existed still produces `unchecked`/`unchecked`
rather than a blank the UI has to guess about.

### The seed, and why it carries a version

`seedREM()` runs once on load and writes the 20 REM bench candidates —
generated payload, land status included — onto a device that has none. Its
flag is `fieldgold_rem_seeded_v2`, and there is a **second** flag,
`fieldgold_rem_seeded_v1`, that exists only to be read.

v1 already shipped. It seeded the same twenty coordinates with **no land status
at all**, so a phone that ran it is holding twelve encumbered benches drawn as
if nothing were known against them. A plain "seeded already, skip" would leave
that device wrong forever, and a plain re-seed would resurrect benches the user
deliberately deleted. So the seeder distinguishes three states: never seeded →
write all twenty; seeded under v1 → **upgrade in place**, stamping both
registers onto the records that are still there and adding nothing that is not;
seeded under v2 → do nothing.

**The seeder must never resurrect a deleted bench.** Deleting a record is a
user decision and the flag is what remembers that the offer was already made.
`tests/test_reactive_refresh.py` covers all four paths — virgin, v1 upgrade,
pruned v1, and re-run idempotence — because three of them only exist on devices
that are already in the field.

### Reactive refresh

`onChange(fn)` registers a listener; the layer fires it on a same-tab write
(via `fireAfterWrite`), on a cross-tab `storage` event, and on a `pageshow`
restore. `map.html` and `index.html` both subscribe, so a bench that moves from
NOT CHECKED to AVOID in one tab cannot keep showing amber in another until
somebody happens to reload. The screen and the record are not allowed to
disagree about a closing order.

Two constraints on that code, both learned the hard way:

- **The `pageshow` listener is guarded on `e.persisted`, and the guard is not
  optional.** `pageshow` fires on every ordinary load, not just a back/forward
  cache restore — right after the page has already drawn itself from current
  data. Unguarded, every page draws twice. That is invisible for markers, which
  are cleared and rebuilt, and *not* invisible for the appending status log:
  "site dropped — no usable coordinates" printed once per bad record became
  twice per bad record, and five malformed sites read as ten.
- **A throwing listener must not silence the ones behind it.** `fire()` wraps
  each call in its own `try`. One subscriber blowing up on a malformed record
  is a bug in that subscriber; it is not a reason for the other screens to stop
  updating.

Subscribers guard on `FieldGoldData.onChange` existing before calling it, because
an older cached `fieldgold-data.js` does not have it and the page must still
render rather than throw on the way to the first row.

### One payload, two files

The twenty seed records exist in two places — `const REM_BENCHES` in
`load_rem_benches.html` and `var REM_BENCHES` in `fieldgold-data.js` — and
**one** thing writes both: `tools/build_loader.py`. Neither copy is hand-edited
(rule 6). The generator constructs both strings, fails on anything wrong, and
only then writes either, so a half-applied run cannot leave the loader and the
seeder disagreeing about which ground is encumbered. It then reads both back
off disk and asserts they carry the same twenty records, which makes "one
payload, two files" a checked fact rather than a comment. `tests/test_seed_drift.py`
asserts it again from outside.

`contextForPoint(lat, lon)` answers the different question "what is known about
the ground under THIS position", for photo analysis. Its asymmetry is
deliberate and load-bearing: `avoid` propagates outward because closing orders
and leasehold orders cover polygons, while `clean` does not propagate at all,
because it was established by a point query. **The function never reports a
position as clean.** Do not add a tier that does.

Three radii govern it, and they were set by measuring the twenty checked
candidates against each other, not chosen by feel — the comment above them in
`fieldgold-data.js` records the numbers:

| constant | value | meaning |
|---|---|---|
| `AVOID_HARD_M` | 250 m | this close, an `avoid` bench overrides even a nearer clean one |
| `CONTEXT_RADIUS_M` | 1500 m | past this, no bench says anything about your position |
| `AVOID_MENTION_M` | 2000 m | past `CONTEXT_RADIUS_M` but inside this, encumbered ground is still **named, with its distance**, in the detail of every tier |

An earlier draft used a single flat 2000 m avoid radius. Against the real
geometry that reads seven of the eight clean benches as encumbered — a warning
that fires everywhere gets dismissed everywhere, including the once it is
right. If you widen `AVOID_HARD_M`, re-measure first; the observed clean→avoid
separations are 151, 739, 747, 947, 1066, 1650, 1666 and 2103 m. The
`mention` string is the compensating control and must not be dropped: not
controlling is not the same as not warned.

`replaceKind(kind, entries, opts)` takes an optional `opts.where` predicate.
A tool that owns part of a kind must pass one. An unscoped
`replaceKind('bench', ...)` previously destroyed the REM records — data that
took DNR queries to establish and that nothing in the app can regenerate. The
same bug shape lived on in `syncSitesToMap`, which called
`replaceKind('site', ...)` unscoped on every `openTools()` and wiped any site
record another tool had written; it now passes
`{ where: e => e.source === 'fieldbrain' }`. If you add a tool that writes a
kind somebody else also writes, the `where` is not optional.

### Score is not status

`map.html` colours your logged site markers from `contextForPoint()`, never
from the terrain score. The two answer different questions: the score says
"does this look like a bench worth walking to", the status says "may you
legally dig here". Only the second one earns the colour, because the colour is
what gets read at a glance. **A site marker is never green** — a DNR check is a
point query against a bench candidate and says nothing about a spot you logged
somewhere else, so the best available honest answer for a logged site is amber.
The score is in the popup as text, with the caveat that a high score on
encumbered ground is still encumbered ground.

The legacy `fieldgold_sites` localStorage blob, written by an older Field
Brain, is treated as untrusted input: coordinates are range-checked, strings
are escaped into popup HTML, and **dropped records are counted and reported in
the status log**, never silently skipped. A site that vanishes without comment
is indistinguishable from a site you never logged.

**Only the bench diamonds can be green.** A DNR check is a point query against
a bench candidate. It says nothing about a spot you logged somewhere else, and
nothing about an ARDF occurrence that happens to sit nearby. Site dots and
scanned occurrences are amber or rust, never green, and `test_stage_maps.py`
asserts that no map page in the repo contains a green `circleMarker` call at
all.

**Still open:** `site` records carry no `land_status` field of their own — the
map derives context at draw time instead.

### Which government you asked is part of the answer

`map.html` queries BLM's `BLM_AK_Federal_Mining_Claims` service. That service
holds **federal** mining claims, and a federal claim can only exist on federal
land. Hatcher Pass is **state** land: GS 1222, state patent 50-87-0076. Every
encumbrance this project has found here — MCO 549, LLO 5, ADL 229824 — is a
state instrument, held in DNR's `ME112` and `ME13` layers, which BLM's service
does not carry.

Measured, not assumed: that federal layer returns **one** polygon across the
whole reach envelope and none over the four upper benches, against **143** in a
same-size envelope near Fairbanks. The query works. The zeros are real. They
are the wrong government's zeros — and **an empty answer from the wrong
authority renders on a phone exactly like a clean answer from the right one.**

That is why:

- the toggle is labelled **"BLM FEDERAL claims only"**, not "Mining claims —
  DON'T dig here", and carries a note saying blank here is not "no claims";
- the function is called `federalClaimAt()`. It was called `isClaimed()`, and
  that name is what let a federal answer be read as *the* answer. Do not rename
  it back;
- the scan button says **"Scan documented gold occurrences"**, not "Find PROVEN
  + OPEN ground", and colours every occurrence from `contextForPoint()`. The
  federal result is still shown — as text, named as federal, with what it does
  not cover stated. Same shape as the terrain score: the information stays, it
  just stops being the thing you read at a glance.

### The state register is a second register, and it stays separate

`land_status` answers "did DNR's encumbrance battery find a closing order, a
leasehold order, a lease or a park closure on this point". It does **not**
answer "is there an active state mining claim here". That is layer `ME112`, and
a bench can be clean on every encumbrance layer and still sit inside somebody's
claim. So the claim answer is its own field — `state_claim`, tiered `none` /
`claimed` / `unchecked`, with `stateClaimOf`, `stateClaimMeta` and
`stateClaimCheckedOn` alongside it. **Unknown normalises to `unchecked`, never
to `none`**, for the same reason `land_status` normalises to `unchecked`: "we
did not ask" and "we asked and the answer was no" must not render the same way.
Do not merge the two tiers to tidy the popup — merging lets an unchecked claim
inherit a clean encumbrance call.

Counted 2026-07-25 against
`Mapper/Mineral_Estate_Layers/MapServer/112` (active) and `/13` (pending):

| register | in the reach envelope | in the box holding REM-1/11/19/20 |
|---|---|---|
| BLM federal claims | 1 | 0 |
| DNR `ME112` active | **22** | **3** |
| DNR `ME13` pending | 0 | — |

All 20 bench points were queried against `ME112` and **all 20 returned empty**;
five were re-fetched directly to confirm. No bench sits inside a claim.

**What is NOT known is how near the nearest claim is.** Per-bench proximity was
never measured — the fetch proxy began rejecting the envelope-count form
partway through and it was not routed around. Every record therefore carries
`state_claim_proximity: "unknown"`, the map says so in words, and
`test_state_claims.py` asserts the page never prints a distance. If you measure
it later, that is the field to fill; until then a zero there would be a
fabrication.

**A claim check has a shelf life.** `state_claim` without
`state_claim_checked` is a rumour, not a result — claims can be staked any day.
The date rides on every record and prints in every popup, and where a record
has no date the popup says "no check date on this record" rather than omitting
the line.

**A live query is still the wrong shape for this app.** Rule 2 forbids runtime
network dependencies because the app is opened at a trailhead with no signal, so
a live claims query fails exactly where it is needed — and it fails by drawing
nothing, which is the blank screen that caused the federal-register bug in the
first place. Whether `arcgis.dnr.alaska.gov` answers a cross-origin request from
a phone browser is **still untested**, and JSONP support is untested too; both
probes were blocked. Do not ship a live layer on the assumption that either
works. Query server-side, ship the answer dated, and say on screen how old it is.

### The stage maps are archived

`stage1_map_test.html` … `stage5_map.html` are the build history of `map.html`,
stage by stage: 1 adds Leaflet + ARDF, 2 adds geochem, 3 adds the claims
overlay, 4 adds the occurrence scan, 5 adds geochem points and terrain.
`map.html` is the superset of all five.

Four of them wore the same heading, layer names and colours as the real app,
and opened from a bookmark there was nothing on screen saying otherwise. Each
now carries a red **ARCHIVED BUILD STAGE — not a field tool** banner at the top
of the panel. Do not remove it, and do not develop these pages further; fix
`map.html` instead.

**They DO ship inside the iOS bundle, by decision, and that is not the same
question as the SHELL.** `webDir` is all of `docs/`, so Capacitor copies these
five into the app. Alan decided that 2026-07-28; `STATE.md` records the
reasoning, what the decision accepts, and the Phase 1 item that revisits it.
Do not read the SHELL exclusion below as "stage maps are kept off devices" —
it is narrower than that, and the two mechanisms are independent.

**They are deliberately NOT in the `sw.js` SHELL, and that is a decision, not an
omission.** Every pixel they draw comes from the network — USGS WMS/WFS, OSM
tiles, the BLM export. Caching their HTML would produce a page that looks like
FieldGold, carries no land-status layer, and shows nothing at all. A browser
offline error is the more honest outcome. `test_stage_maps.py` asserts their
absence from SHELL so a future "helpful" addition trips a test rather than
shipping.

### Leaflet is vendored, the tiles are not

`docs/vendor/leaflet/` holds Leaflet 1.9.4 — see `docs/vendor/leaflet/PROVENANCE.md` for
where the bytes came from and how they were verified against a publisher
independent of the one that served them. Every map page loads it by relative
path. Do not repoint any page at a CDN: rule 2 above forbids it, and the
failure was measured, not theorised — with no network `window.L` was undefined
and the map did not exist.

**This fixed the library, not the imagery.** Basemap tiles still come from
OpenStreetMap, Esri and OpenTopoMap over the network. Offline the app draws
your benches, your logged sites, their land-status colours and their popups on
a blank background. `map.html` watches the tile layers and says so on screen —
"basemap tiles unavailable — no signal", followed by the statement that the
points and their colours are still correct. Do not delete that message to tidy
the log, and do not describe this app as "working offline" without the
qualifier: a grey rectangle that goes unexplained reads as a broken app, and a
person who thinks the app is broken stops trusting the colours too.

If you upgrade Leaflet, the SRI hashes must be updated in **both**
`docs/vendor/leaflet/PROVENANCE.md` and `tests/test_offline_map.py`, and `sw.js`
bumped. The suite failing until you do that is the intended behaviour.

Note the two path conventions, because they look inconsistent and are not:
`tests/test_offline_map.py` serves `docs/` as its document root, so the
`vendor/leaflet/...` strings inside it are **web-root-relative and correct**.
Prose in this file and in `PROVENANCE.md` describes files on disk, so it carries
the `docs/` prefix. Do not "fix" one to match the other.

### A notice you cannot reach has been removed

Rules 4 and 5 say never soften a land-status warning and always state
uncertainty on screen. **Layout is a way of deleting text**, and until
2026-07-26 nothing in this repo was watching for it. Alan reported from his
phone that the Leaflet controls were painting over the panel; measuring it
found two independent defects, both of which had shipped green through eleven
suites.

- **The z-index tie.** `#panel` was `z-index:1000`. So are Leaflet's
  `.leaflet-top`/`.leaflet-bottom` **containers** (`docs/vendor/leaflet/leaflet.css`
  line 141). The `z-index:800` on `.leaflet-control` only orders controls
  *within* those containers and does not apply here — a static read of the 800
  is how this was got wrong the first time. A tie breaks by DOM order, `#map`
  is declared after `#panel`, so Leaflet won and the zoom and layers controls
  painted **on top of** the land-status warnings. 21 sample points inside
  warning text were covered on a 390x664 phone. `#panel` is now `1200`.
- **The unreachable tail.** `#panel` had no `max-height` and no scroller, and
  `#map` is a full-viewport absolute element so the body never scrolls.
  Everything below the fold was *physically unreachable*: 102 of 256 warning
  sample points on a 390x664 phone, 118 of 250 on a 375x553 one. The panel
  scrolls itself now, and under 600px the expanded panel is a full-screen sheet
  with a sticky title so the collapse control stays reachable at any depth.

Two things to know before you touch this CSS:

- **`max-height` clamps the CONTENT box.** With `box-sizing:content-box`,
  padding + border + `top` push the element past the viewport anyway — measured
  at 624px against a 620px window. `#panel` is `box-sizing:border-box` with
  `max-width:328px` (300 content + 26 padding + 2 border) so the rendered width
  is unchanged from before; that number is a box-model translation, not a
  redesign.
- **`el.scrollTop = n` succeeds on an `overflow-y:hidden` element in Chromium.**
  A reachability walk that only sets `scrollTop` proves the text is
  *programmatically addressable*, not that a finger can get to it — the
  `no-overflow` mutant survived on exactly that. Gate the scroll range on
  computed `overflow-y` before you believe a green.

`tests/test_panel_reachability.py` is the tripwire. It renders each map page at
two phone viewports, a desktop, and a deliberately short 1280x620 window (above
the mobile breakpoint, shorter than the content), expands the panel — the
collapsed panel measures nothing — and hit-tests every point inside warning
text at every reachable scroll offset with `elementFromPoint`, because rect
maths says two boxes intersect and only a hit test says which one **won**.
`#status` is excluded from the scope: it is the run log and has its own 64px
scroller, so scrolling the panel can never reach its lower lines.

**The five stage maps still carry the old `z-index:1000` and no `max-height`.**
They pass because their panels currently *fit* (254–455px in a 664px viewport),
not because they were fixed. Add three sentences to one of them and the suite
goes red. That is the intended behaviour; fix the CSS then, do not raise the
threshold.

### The mutant that applies cleanly and does not matter

The abort discipline — a mutation whose `replace()` matches nothing must exit 2
— was written to catch mutants that go stale when the code moves. It does catch
those, seven times so far. **It does not catch a mutant that applies perfectly
and violates nothing.**

`test_stage_maps.py --mutate stale-cache` was one, found 2026-07-26. It rewrote
the cache version to `fieldgold-v7`. It was written when the assertion pinned a
literal version, so v9 → v7 tripped it. When that assertion was later
generalised to `int(version) > PUBLISHED` with `PUBLISHED = 3` — the right fix,
for the right reason — v7 stopped violating anything, because 7 > 3. The
mutation still applied. The file still changed. Nothing aborted. The suite
reported 109 passed, 0 failed and exited 0, and for that suite exit 0 under
`--mutate` means **survived**.

It is now `fieldgold-v3`: the version actually on the device, which is both what
"stale cache" means and the one value that violates the claim.

Two rules follow.

- **Every mutant must violate the assertion it targets, not merely differ from
  the current value.** When you generalise an assertion, re-read every mutant
  that aimed at it. Generalising is usually right; it silently disarms mutants.
- **Run the mutants and read the exit code against the suite's own convention.**
  Nothing else finds this class. Exit 2 finds stale mutants; only actually
  running them finds dead ones.

## Changing the service worker

`sw.js` caches the app shell. **If you change the CONTENTS of any file in
`SHELL`, the cache version must be bumped** — not just when you add or rename
one. That wording used to read "add or rename", and on 2026-07-26 it very nearly
shipped the panel reachability fix to a phone that would never have seen it:
`map.html` was edited, no file was added, and by the letter of the old sentence
no bump was needed.

Look at the `fetch` handler before you decide otherwise. It is **cache-first
with no revalidation** — `caches.match(e.request).then(hit => { if (hit) return
hit; ... })`. It never asks the network about a file it already holds. `SHELL`
contains `./map.html`. So a device holding `fieldgold-vN` serves its own stored
`map.html` **forever**, and publishing a fix to GitHub Pages changes nothing at
all on that device. The `activate` handler deletes every cache whose key is not
the current `CACHE`, which means **the version string is the entire delivery
mechanism.** Bumping it is not bookkeeping.

Field devices will otherwise keep serving the old copy silently, and exactly
when the user has no signal to notice. Treat a stale service worker as a
correctness bug, not a nuisance.

**Versions are sequential from v4 and withdrawn numbers are not reused.** The
note above `const CACHE` in `sw.js` explains that an early draft numbered change
sets as v5–v9 and withdrew them; the v5 published on 2026-07-26 is a real
release and is unrelated. Nothing pins the number any more — `test_state_claims.py`,
`test_stage_maps.py` and `test_offline_map.py` all read it and assert only that
it is past v3, the last version that reached a device without land status. Pinning
it made correct bumps fail, which teaches the next person to edit the assertion
instead of thinking.

`tests/test_sw_lifecycle.py` covers the takeover itself: it stands up the tree
under one cache version, registers the worker, swaps the server's document root
to the current tree, and asserts the new worker installs, the new cache is
POPULATED, the old one is deleted, and the page ends up controlled. Two things
it learned the hard way, both worth knowing before you touch it:

- **`caches.open(CACHE)` creates the cache before `addAll` fetches anything.**
  So a total install failure leaves a correctly-named EMPTY cache behind, and
  any check of the form `'fieldgold-vN' in caches.keys()` passes on a worker
  that cached nothing at all. Assert on contents.
- **A local reproduction of a version bump can be defeated by `If-Modified-Since`.**
  Chromium sends it on the worker's update fetch. `python3 -m http.server`
  answers it from the file's MTIME, so serving a newer *tree* whose `sw.js` has
  an *older* timestamp gets a 304 and the update never happens — no error, no
  console message, nothing on screen. This is why hand-driven DevTools work on
  2026-07-26 could not get v4 to install. GitHub Pages revalidates on ETag, from
  the bytes, so it is a harness trap and not a production one. If you reproduce
  an update locally, serve with caching off.

## Deploying to GitHub Pages — verify the artifact, not the status

The site is served from **branch `main`, path `/docs`** (flipped from `/` in
Phase 0a, 2026-07-27). `docs/` holds only web assets so that Capacitor's
`webDir` can point at it; `tests/` and `tools/` stay at the repo root and must
never ship in the app bundle.

Two rules, both learned by getting them wrong on 2026-07-27, and both of the
same shape: **a green-looking field is not the artifact.**

- **A Pages build status of `built` can name an earlier commit.** The Pages
  API reports `status` for the repository, not for your push. After the Phase
  0a flip it read `built` with source `/docs` while the live bytes came from
  the build for the commit *before* the move — so every `docs/`-relative path
  404'd and the front page was a Jekyll rendering of `README.md`. Polling
  `status` proved nothing. **Read
  `/repos/OWNER/REPO/pages/builds/latest --jq .commit` and require it to equal
  the SHA you pushed** before you call a deploy done.
- **Pushed does not imply building.** `53edb99` reached `origin/main` and sat
  15 minutes with no `pages build and deployment` run at all. If no run appears,
  force one: `gh api -X POST repos/OWNER/REPO/pages/builds`. It completed in
  about 45 seconds.

Then fetch the assets, cache-busted, and check **content** and not only status
codes — a 200 can be a Jekyll page wearing your title. The Phase 0a check was
14 paths plus greps for `VISION_PROMPT` in `index.html`, the scan-button text
in `map.html`, `Leaflet 1.9.4`, and the `REM_BENCHES` seed.

`docs/.nojekyll` exists so the build is deterministic and Jekyll does not
process the tree. That is its whole justification. It is **not** there to stop
`vendor/` being excluded — see the retraction in the commit that added it.

## What a good pull request looks like here

Small, one concern, and explicit about what was verified versus assumed. If a
change touches bench data, say in the PR body which coordinates were compared
against which source and confirm none moved.

## If you are an agent working in this repo

Two consequences worth holding in mind:

- You can commit. Prefer opening a pull request over pushing to `main`, so a
  human reads the diff before a phone caches it.
- The rules above are the whole brief. Nothing else reviews your change before
  it reaches a device used to decide where a person walks.

## Current state

Read `STATE.md` at the start of any work session. It is the source of truth
for which migration phase is active and what is verified. Do not infer phase
from conversation history.

## Migration phases

0. Capacitor shell — wrap unchanged, sign, install on device
1. Consolidate scattered HTML into one routed app
2. localStorage -> SQLite
3. Offline tiles -> filesystem + SQLite index
4. Background GPS

**Ordering constraint: Phase 2 before Phase 3.** The tile index needs real
tables. Building it on localStorage means rebuilding it.

Do not start a phase before the previous one is marked verified in `STATE.md`.

## Commands

```
npx cap sync          # after any web asset or plugin change
npx cap open ios      # opens Xcode
```

`npx cap sync` is required after every dependency change. Skipping it is the
most common cause of "the plugin isn't there" confusion.

There is no build step for app code, and there is not going to be one. See
ground rule 1.

## Verification tiers

Label every factual claim about external systems with one of:

- `[self-tested]` — ran on the dev machine
- `[fetched]` — retrieved from a live endpoint this session
- `[externally-verified]` — confirmed on the actual iPhone or in the field

Never present `[self-tested]` as `[externally-verified]`. The first two you can
produce yourself; the third you cannot, and saying otherwise is how an
unverified claim gets carried into terrain.

## Network reality

You run locally with normal network access. ARDF, BLM and USGS are reachable —
fetch them directly rather than asking for a paste, and do not report a failed
fetch as evidence an endpoint is down without checking it.

What is **not** verifiable here: whether a layer renders on the phone, whether
tiles survive offline, whether a fix lands in terrain. Those are device checks
and they belong to Alan.

## Geology data notes

- Bedrock layer is the USGS **Geologic map of Alaska**, not SGMC.
  SGMC excludes Alaska. This has been gotten wrong before.
- Working reach: Little Susitna River, near Turner's Corner / Hatcher Pass.

## Conventions

- One phase per branch, one commit per verified step.
- Read-only tooling by default. Anything that writes to the repo or to
  device storage gets called out explicitly before it runs.
- Prefer editing existing files over creating new ones.
- If a step needs a decision from Alan, stop and ask. Do not pick a default
  and proceed.
