# FieldGold — repository guide

A static progressive web app carried into the field for gold prospecting in the
Hatcher Pass / Little Susitna area, Alaska. Served from GitHub Pages at
`alanfuller15.github.io/FieldGold/`.

## Ground rules for anyone (human or model) changing this repo

**This app is used offline, on a phone, in terrain, to decide where a person
physically walks.** That constrains everything below.

1. **No build step.** No bundler, no npm install, no framework. Plain HTML, CSS
   and JS that a browser loads directly. If a change would require a build step,
   the answer is no — propose it in the issue instead of implementing it.
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

| file | role |
|---|---|
| `index.html` | entry point / launcher |
| `fieldgold-data.js` | shared data layer — `localStorage` key `fieldgold_record` |
| `load_rem_benches.html` | loads the 20 REM bench candidates with land status |
| `bench_hunter.html` | bench working view |
| `creek_manual.html` | reference text |
| `map.html` | **the map.** The only field map screen |
| `stage1_map_test.html` … `stage5_map.html` | **archived build stages** of `map.html`, kept for history. Not field tools — see below |
| `sw.js`, `manifest.json`, `icon-*.png` | PWA shell — offline caching and install |
| `tools/build_loader.py` | **generator.** Holds the STATUS table — the land-status call for all 20 candidates with the reasoning for each — and writes **two** files from that one payload: `load_rem_benches.html` in place, and the `REM_BENCHES` seed array inside `fieldgold-data.js` between its BEGIN/END GENERATED markers. See "one payload, two files" below |
| `vendor/leaflet/` | **vendored Leaflet 1.9.4** — not written here; see `PROVENANCE.md` |
| `tests/` | **ten suites.** `test_land_status.js`, `test_photo_land_context.js` (node); `test_app_land_status.py`, `test_photo_app.py`, `test_map_sites.py`, `test_offline_map.py`, `test_seed_drift.py`, `test_stage_maps.py`, `test_state_claims.py`, `test_reactive_refresh.py` (playwright) — **nine of the ten** take `--mutate` to prove they can fail. `test_app_land_status.py` does not, and that gap is open. Note `test_offline_map.py` inverts its exit code under `--mutate` (caught → 0, survived → 1); the others exit 1 on any failure. Read the convention before wiring a runner. A mutation whose `replace()` matches nothing must abort with exit 2 rather than report a pass — a test that cannot fail is not evidence |

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

**They are deliberately NOT in the `sw.js` SHELL, and that is a decision, not an
omission.** Every pixel they draw comes from the network — USGS WMS/WFS, OSM
tiles, the BLM export. Caching their HTML would produce a page that looks like
FieldGold, carries no land-status layer, and shows nothing at all. A browser
offline error is the more honest outcome. `test_stage_maps.py` asserts their
absence from SHELL so a future "helpful" addition trips a test rather than
shipping.

### Leaflet is vendored, the tiles are not

`vendor/leaflet/` holds Leaflet 1.9.4 — see `vendor/leaflet/PROVENANCE.md` for
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
`vendor/leaflet/PROVENANCE.md` and `tests/test_offline_map.py`, and `sw.js`
bumped. The suite failing until you do that is the intended behaviour.

## Changing the service worker

`sw.js` caches the app shell. If you add or rename a file, the cache version must
be bumped or field devices will keep serving the old copy — silently, and exactly
when the user has no signal to notice. Treat a stale service worker as a
correctness bug, not a nuisance.

## What a good pull request looks like here

Small, one concern, and explicit about what was verified versus assumed. If a
change touches bench data, say in the PR body which coordinates were compared
against which source and confirm none moved.

## The `@claude` workflow

`.github/workflows/claude.yml` runs with `contents: write` and, at present, no
`--allowedTools` allowlist. Two consequences worth holding in mind if you are
that agent:

- You can commit. Prefer opening a pull request over pushing to `main`, so a
  human reads the diff before a phone caches it.
- The rules above are the whole brief. Nothing else reviews your change before
  it reaches a device used to decide where a person walks.
