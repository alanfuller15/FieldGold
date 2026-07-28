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
2. **No new runtime dependencies from a CDN.** The app must work with no signal.
   Anything fetched at page load is a failure mode at the trailhead.
3. **Never invent coordinates.** Latitude and longitude values in this repo trace
   back to a lidar-derived REM analysis and to DNR land-status queries. If a
   change moves a coordinate, that change is wrong unless the issue explicitly
   says otherwise and gives the source.
4. **Never soften a land-status warning.** Candidates are tiered clean /
   not-checked / avoid. "Not checked" must never be presented as safe, and
   "avoid" must never be quietly dropped from a list to make the UI tidier.
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
7. **The model-facing prompt is not a safety control.** `VISION_PROMPT` in
   `index.html` is sent to a vision model along with a land-status block built
   by `FieldGoldData.landBriefForPrompt`. Instructing a model to withhold pan
   advice on encumbered ground is a request, not a guarantee. The control that
   actually holds is `landBanner()`, drawn by the app from
   `contextForPoint()` before the request is even sent. If you change this
   screen, the banner renders on every path — success, HTTP error, network
   failure, and re-opening an old photo — or the change is wrong.

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
| `ios/` | **generated by `npx cap add ios`.** Tracked, but `ios/.gitignore` (Capacitor's own) excludes build output and `App/App/public` — the web assets there are a *copy* of `docs/` regenerated by `npx cap sync`, and must never be tracked as a second source of truth |
| `tests/` | **twelve suites, 489 assertions** — measured 2026-07-26 by running all twelve and summing each suite's own count (30/50 node; 30, 31, 39, 48, 29, 25, 15, 109, 68, 15 python). The figure here read 488. `test_land_status.js`, `test_photo_land_context.js` (node); `test_app_land_status.py`, `test_photo_app.py`, `test_map_sites.py`, `test_offline_map.py`, `test_seed_drift.py`, `test_stage_maps.py`, `test_state_claims.py`, `test_reactive_refresh.py`, `test_sw_lifecycle.py`, `test_panel_reachability.py` (playwright) — **eleven of the twelve** take `--mutate`, **66 mutants** (64 distinct names — `no-banner` and `stale-cache` each appear in two suites). `test_app_land_status.py` does not, and that gap is open. **The "all caught" run covered 63 of them.** Counted off the tree 2026-07-26: 57 mutants at `35adc6f`, 66 at `72e8815`, 66 now. The 63 was never the tree's count — three mutants have never appeared in a verified-all-caught run, and which three is not recorded. The conclusion that the 63 were caught still stands; only the number was wrong. **The exit convention is split and this file got it wrong twice** — verified empirically 2026-07-26 by running those 63. Inverting (caught → 0, survived → 1): `test_offline_map.py`, `test_sw_lifecycle.py`, `test_reactive_refresh.py`, `test_seed_drift.py`, `test_panel_reachability.py`. Exit 1 on any failure: `test_map_sites.py`, `test_photo_app.py`, `test_stage_maps.py`, `test_state_claims.py`, and both `.js` suites. **Do not read this table — run one known mutant per suite and observe the code.** Whatever a runner assumes, half the suites report the opposite, and the failure mode is a runner that prints green over a survived mutant. A mutation whose `replace()` matches nothing must abort with exit 2 rather than report a pass — but see below: exit 2 does not catch everything |

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
| `CLAUDE.md` | 653 | this file — the whole brief for anyone changing the repo |
| `STATE.md` | 335 | **source of truth for the active migration phase.** Read it first; do not infer phase from conversation history. Points at the phase-0 runbook for procedure |
| `README.md` | 200 | the public-facing README, written for a prospector. What GitHub renders. Re-read 2026-07-28 against the moved tree — it names no file paths, so Phase 0a did not stale it |
| `docs/vendor/leaflet/PROVENANCE.md` | 137 | where the vendored Leaflet bytes came from and how they were verified. Moved into `docs/` with the bytes it documents in Phase 0a. Carries a 2026-07-28 correction: the `.gitattributes` it cited does not exist |
| `.claude/skills/phase-0-shell/SKILL.md` | 146 | Phase 0 runbook — Capacitor init, `cap add ios`, signing, first device install. Defers to `STATE.md` for status |
| `ios/App/CapApp-SPM/README.md` | 5 | **generated by `cap add ios`, not written here.** Five lines saying the SPM package hosts Capacitor's Swift dependencies and not to edit it. Indexed because the control above says every tracked `.md` gets a row, and a generated file is exactly the kind that otherwise accumulates unlisted. Regenerated by Capacitor — do not hand-edit (ground rule 6 applies) |

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
