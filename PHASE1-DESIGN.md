# Phase 1 — consolidation, the working set, layer defaults, the feature popup

**Status: APPROVED AS DESIGNED, 2026-07-29. Not built.** Alan approved Designs
1–4 below on that date, with the rulings and three notes recorded in each place
they apply. Nothing here has been implemented; no application code was written
to produce this document.

**Amended once since approval, 2026-07-29: the view lifecycle is three phases,
not two.** `init` / `enter` / `measure`, with `measure` defined as post-layout —
see Design 1. The reason is in `PRIOR-ART-PHASE1.md` item 3: the field needed a
third hook for exactly this, and this project has already paid for the two-phase
mistake once. **That is the only change made to this document after approval.**
Two other findings from that pass were ruled on and changed nothing here —
`EXCEPTIONS=INIMAGE` declined, symbolizing absence declined in both directions.

**What this file is.** The design for Phase 1's rescope. `STATE.md` remains the
source of truth for *how far* the work has got and points here for *what the
work is*; `CLAUDE.md` remains the brief that constrains it. Where this file and
a ground rule disagree, the ground rule wins and this file is wrong.

**Read first, because this design is downstream of both:** `CLAUDE.md` ground
rules 1, 3, 4, 5, 6 and 7, and `STATE.md`'s Phase 1 items A–E plus the two
offline-run sections. Every measured number quoted here is from those and is
re-attributed at the point of use.

**Why Phase 1 was rescoped.** It was scoped from three shell divergences found
on a device — service worker, `target="_blank"`, safe-area insets — and PR #6
fixes those. They are real and they are not why the app is hard to use. Using it
with a second person surfaced what is:

- **The app plots exactly the things worth going to, and those are the only
  things you cannot select.** Tapping blank map yields usable coordinates;
  tapping a bench diamond, a geochem sample or a documented occurrence yields a
  popup that describes the feature and offers no way to carry it anywhere. The
  habit that developed is tapping *next to* the feature you want, to get
  coordinates the app already has.
- **The only two states a location can be in are "nothing" and "a saved
  Site."** Committing to the permanent record is the price of merely considering
  a place. There is no noun for the thing you are currently looking at.
- **Demonstrating the app to another person required teaching it** — logging in
  one page and seeing it in another needs a tab switch and a reload, in the right
  order, and that sequence existed only in the author's head.
- **Layers are on by default**, so panning issues concurrent requests to USGS,
  BLM and OSM for every layer, and past some threshold tiles come back blank.
  That threshold was found by experiment and is written down nowhere.

---

## Decisions this design is built on

Settled by Alan before the design was written (D1–D8) or as rulings on it
(D7-scope, N1–N3). Design to them; do not re-litigate them here.

| # | decision |
|---|---|
| **D1** | The map is not a separate screen. It is a view alongside Evaluate, Sites, Knowledge, Photo, Research and Kit. One document, screens swap without a page load |
| **D2** | The working set holds **multiple** points. Prospecting means planning a traverse across several outcrops, not visiting one |
| **D3** | Order is not inherent and is user-assignable. Points are a set by default; ordering is an explicit step **after** selection, not a consequence of tap order |
| **D4** | Add-more-later is required. Returning to the map and adding points must not discard ordering already done. Export is the terminal act, not the ordering |
| **D5** | Tapping empty map still yields coordinates, exactly as today. That habit is load-bearing. A point from blank ground and a point from a feature both enter the set; they differ in **provenance**, not in usability |
| **D6** | The working set survives backgrounding and is cleared on deliberate exit. On a phone, "the user closed the app" and "iOS reclaimed memory while the user checked the weather" are indistinguishable to the user, so session-only state can lose a twenty-minute traverse through no action of theirs |
| **D7** | Layers default OFF — **scoped, see the ruling below** |
| **D8** | **Web is the primary distribution; native is the field build.** A stranger receives a URL. Native exists for what a browser cannot do — background GPS, offline tiles at volume, storage that survives eviction. So this consolidation is FIRST a fix to the web app and second a shell improvement, and feature divergence between the two must be visible to the user rather than silent. Filed against the dual-distribution decision in `STATE.md`, which it settles |

### The D7 ruling — and why a literal reading collided with ground rule 4

**Confirmed 2026-07-29: D7 scopes to the QUERY layers. The record layers stay
ON. The basemap is not a toggle.**

`map.html` has seven toggles and they are not the same kind of thing
[self-tested] 2026-07-29:

| toggle | source | network cost per pan |
|---|---|---|
| `t-ardf` | USGS `mrdata.usgs.gov` WMS | 12 tiles |
| `t-geo` | USGS WMS + a WFS feature fetch | 12 tiles + 1 fetch |
| `t-claim` | BLM `gis.blm.gov` export | 12 tiles |
| `t-terrain` | `elevation.nationalmap.gov` — **already off today** | 12 tiles |
| `t-sites` | `localStorage` | **zero** |
| `t-bench` | `localStorage` | **zero** |
| `t-rem` | `localStorage` | **zero** |

**The reasoning, recorded because it is the part that would otherwise be lost:**

- **A zero-network layer gets no politeness argument.** The whole justification
  for defaulting a layer off is the burst of concurrent requests to services
  this project has no agreement with. The bench, REM and site layers read
  `localStorage` and issue nothing. The argument does not reach them.
- **The land-status layers are the ones rule 4 exists for.** Defaulting
  `t-bench` and `t-rem` off means the map opens with the twelve encumbered
  benches **not drawn**, behind an opt-in. That is "`avoid` must never be
  quietly dropped from a list to make the UI tidier" — rule 4's exact
  prohibition — arriving through a default rather than through an edit.
- The basemap is a one-of-three choice, not a toggle. Defaulting it off means a
  blank background always, which is the failure `map.html` already has an
  explanation line for.

Under this ruling a pan costs roughly **12** tile requests rather than the
measured **48**.

### Three notes attached to the approval

- **N1 — the pending-occurrence compat obligation takes option (a):** convert
  once and remove, with the seed v1→v2 care — **convert in place, add nothing
  that is not there, never resurrect a deleted one.** See Design 2.
- **N2 — `creek_manual.html` and `load_rem_benches.html` stay standalone.** The
  no-JS property is real, and keeping rule 6's blast radius at zero is worth
  more than uniformity. See Design 1.
- **N3 — the iframe fallback stays on the table.** If opening `map.html`'s
  closure proves worse than expected, **say so and stop rather than pushing
  through.** That file carries the land-status colours and the federal-register
  caveat.

---

## Corrections to the premises, established against the tree

The rescope brief was written from conversation. Five things in it read
differently against the files. All [self-tested] 2026-07-29.

**1. There IS a noun for the current thing, and it is worse than none.**
`map.html:526` and `:538` write `FieldGoldData.put({kind:'occurrence',
pending:true})`; `index.html:2849 checkPendingOccurrence()` reads it and `:2889`
removes it. The app has a working set of **exactly one**, implemented as a
**persisted record inside `fieldgold_record`**, and it takes `pending[0]` — the
first of any it finds, silently, with no picker. Three consequences: this design
replaces a mechanism rather than adding one; **tapping ＋ today writes to the
permanent record**, so the working set is a net *reduction* in accidental
permanent writes; and devices already hold `pending` occurrences, which is N1.

**2. The mechanism behind the tap-next-to-it habit.** `saveOccurrence` and
`setSpot` are called from **exactly two places**, both inside the
`map.on('click')` identify popup (`map.html:580`, `:589`). Every marker popup —
bench, REM, geochem, scanned ARDF, logged site — has no action at all. And **a
Leaflet marker click does not propagate to `map.on('click')`**, so tapping the
feature can never reach the affordance. The habit is not a workaround for an
oversight; it is the only path that exists. One wrinkle: `＋ Use this spot` is
suppressed when the identify *did* find an ARDF hit (`:586`), so tapping beside
an occurrence yields a different button and a different provenance
(`source:'map'`, `name:'ARDF occurrence'`) than tapping blank ground
(`source:'map-pick'`, `plain:true`).

**3. "The pages do not share live state" is narrower than it reads.**
`FieldGoldData.onChange` already fires on same-tab writes, cross-tab `storage`
events and `pageshow`; both pages subscribe. What `index.html`'s subscriber does
is re-render **Sites and Research only, and only if already active**
(`:2908-2913`), and `checkPendingOccurrence()` runs **once at boot** and is
never re-invoked. The tab-switch-and-reload habit is real; its cause is one
un-subscribed consumer, not absent machinery. **Filed separately as a ten-line
fix available today, independent of consolidation** — see `STATE.md`, "Filed, not
acted on".

**4. "All map layers are on by default" — six of seven.** `t-terrain` is off.
The measured burst is **48 tile requests per pan** (4 network layers × 12
viewport tiles), from offline Run 2's `tilesInDom`.

**5. The blank-tile threshold is recorded nowhere.** Searched; confirmed absent.
The design therefore cannot reference it and must not guess a cause. See
Design 3.

---

## Design 1 — Consolidation

### The machinery already exists; this extends it

`index.html` has a plain-JS view swapper today: `.view{display:none}` /
`.view.active{display:block}` (`:77`), six `<section class="view" id="view-*">`
(`:294-309`), a fixed `.tabbar` of `data-view` buttons (`:313`), and
`switchView(name)` (`:2832`) which clears `.active`, sets one, and calls that
view's render function from an `if` chain.

Two changes, no new concepts, no framework, no router library, no bundler
(ground rule 1 is binding and "consolidate into one routed app" is the sentence
that invites breaking it):

1. **A seventh view, `view-map`.** `map.html`'s body moves into it.
2. **The `if` chain becomes a declared registry** — a plain object:
   `VIEWS = { evaluate:{init,enter,measure}, sites:{…}, knowledge:{…}, photo:{…},
   research:{…}, checklist:{…}, map:{…} }`.

The registry buys one thing the chain cannot: **a test can assert that every
`data-view` in the tab bar has an entry and every entry has a tab.** That is
rule 4's routing extension made checkable — a view reachable by a route with no
control, or a control pointing at nothing, fails a suite instead of shipping.

### `init`, `enter` and `measure` — why three phases, not two

> **AMENDED 2026-07-29, and this is the only amendment made after approval.**
> This section originally specified **two** phases, `init` and `enter`, with
> `enter` running "after `.active` is applied". The prior-art pass
> (`PRIOR-ART-PHASE1.md`, item 3) found that the field needed **three**: iOS 17
> added `viewIsAppearing` because `viewWillAppear` fires before the view's
> geometry is final — *"It's too early in viewDidLoad or viewWillAppear as the
> view is not yet added to the view hierarchy"* [fetched]. **This project has
> already paid for that exact mistake once**, when `log()`'s
> `S.scrollTop = S.scrollHeight` wrote 0 to 0 against a `display:none` subtree.
> Specifying two phases was repeating it in a new place. Alan's ruling,
> 2026-07-29: amend.

Three phases. The names are ours; the shape is UIKit's.

| phase | runs | for |
|---|---|---|
| `init` | **once**, idempotent | building DOM, constructing the Leaflet map, binding listeners. **Never measures anything** |
| `enter` | every time the view becomes visible, immediately after `.active` is applied | state changes that do not depend on geometry: subscribing, reading the record, clearing a stale results pane, setting the hash |
| `measure` | every time the view becomes visible, **after the browser has computed layout for it** | anything that reads or writes geometry: `map.invalidateSize()`, scroll positions, bounded-scroller heights, reachability-dependent decisions |

**Why `enter` cannot be the measuring phase.** Applying `.active` makes layout
*obtainable*; it does not mean layout has been *computed* at the moment the
handler runs. The DOM is more forgiving than UIKit here — a forced reflow inside
the same task will produce correct numbers — but "more forgiving" is not
"guaranteed", and the distinction is invisible in a diff and on a desktop. Making
it a named phase is what stops the next person putting a measurement in the wrong
one.

**Two rules that go with `measure`, both from this project's own history:**

- **It runs after layout, by construction, not by hope.** Either read a layout
  property to force a synchronous reflow before measuring, or defer to the next
  frame. Which one is an implementation choice; that the phase is *defined* as
  post-layout is not.
- **It verifies a non-zero size rather than assuming one.** A zero size means the
  view is not laid out and the measurement is void — that is the
  `scrollHeight === 0` failure, and the correct response is to report it, not to
  proceed with zeros. This is the same discipline as gating scroll assertions on
  computed `overflow-y` rather than on `scrollTop` accepting a value.

`init` remains once-only because re-running `L.map()` on the same container
throws ("container is already initialized").

The reason is measured, not stylistic. **A `display:none` container has no
layout box**, and this repo has already been bitten by exactly that: `log()`'s
`S.scrollTop = S.scrollHeight` wrote 0 to 0 because `#panelbody` was
`display:none` and `scrollHeight` was 0 — *"the collapse that hides the log also
disables the scroll that would reveal it."* Consolidation multiplies that trap
by the number of hidden views.

- **Leaflet cannot initialise usefully in a hidden container.** `map.getSize()`
  reads 0×0, no tiles are requested, markers place wrong.
  `map.invalidateSize()` must run on every `measure`. Re-running `L.map()` throws
  ("container is already initialized"), which is why `init` must be once-only.
- **General rule for the whole design:** no measurement, scroll assignment or
  geometry read inside an inactive view is valid. Anything that measures runs in
  `measure`, and any assertion about it reads **computed style** rather than
  trusting an assignment to succeed.

### The map's closure has to be opened, and that is the real cost

`STATE.md` records that `map` and all four tile layers are `const`s inside
`map.html`'s `window.addEventListener('load', …)` closure and *"are never
exposed on `window`. Nothing in the page can be driven from the inspector."*
That property is why the offline test had to delete the app rather than bust the
cache from the console.

Consolidation **requires** driving the map from outside — the working set must
add and remove markers — so the closure must be opened into something like
`MapView = { init, enter, measure, syncWorkingSet, … }`, with the same `const`s inside
and only what is needed exposed.

**Cost, stated plainly: this refactor touches the most safety-critical file in
the app** — the one carrying the land-status colours, the federal-register
caveat and the tier popups. It is mechanical, but it is not small, and it is the
part of Phase 1 most likely to break something quietly.

**N3, the approved fallback:** keep `map.html` in an `<iframe>` inside
`view-map`. It preserves the file, the test estate and the closure untouched, at
the cost of a separate `window` — so live state would need `postMessage` or
storage, which is the thing being fixed. **If opening the closure proves worse
than expected, say so and stop rather than pushing through.**

### The URL: a hash route

**`#/map`, `#/photo`, …** One `hashchange` listener; `switchView` reads the hash
on load; an unknown hash resolves to `evaluate` rather than a blank screen.

What it buys: shareable and reload-surviving, which is the primary
distribution's currency under D8 — and **an in-app back for free on both
distributions.** That is not incidental: `docs/fieldgold-chrome.css` records
that WKWebView's `allowsBackForwardNavigationGestures` is off, Capacitor never
sets it, and enabling it needs native Swift. A hash history is the only back
either build gets without native code.

What it costs: **the route becomes a public surface.** Every hash target is a
route the user *has*, so rule 4's routing extension applies to each, and a
bookmark to `#/photo` must render its banner (see the rule 7 enumeration below).
Offline it costs nothing — hashes never hit the network, and `sw.js`'s
navigation fallback already ends `.catch(() => caches.match('./index.html'))`.

**Why not a path router (`/map`):** it needs server rewrites on Pages and has no
meaning under `capacitor://localhost`. Foreclosed deliberately.

### The five files

**Keep every filename as a real file.** Measured coupling [self-tested]
2026-07-29: **seven suites contain 76 references to `map.html`**
(`test_stage_maps` 20, `test_panel_reachability` 14, `test_state_claims` 14,
`test_map_sites` 13, `test_offline_map` 9, `test_reactive_refresh` 5,
`test_app_land_status` 1), and **eight suites reference
`load_rem_benches.html`**. Filenames are load-bearing infrastructure here.

| file | disposition | why |
|---|---|---|
| `map.html` | **thin stub** → `index.html#/map`; content moves into `view-map` | bookmarks and external links keep working; suite fetches keep resolving. Their *content* assertions must migrate — **that is the bulk of the work, not the view swapping** |
| `bench_hunter.html` | same treatment | no special property to protect |
| `creek_manual.html` | **standalone — N2** | it loads **no JavaScript at all**, deliberately, and `CLAUDE.md` records that as the point. As a view in a JS-driven document, the reference text stops surviving a total JS failure. That loss is rule-5-adjacent and is not worth uniformity |
| `load_rem_benches.html` | **standalone — N2** | it is **generated** by `tools/build_loader.py` (rule 6), which also writes the seed array into `fieldgold-data.js` between BEGIN/END markers. Consolidating it means the generator emits a view fragment and its read-back assertion plus `test_seed_drift.py` follow. It is a one-time, with-signal utility linked from one line of prose (`index.html:1920`). Leaving it out keeps rule 6's blast radius at **zero** |
| the five stage maps | **untouched** | zero inbound links, ARCHIVED banner, ship by decision, three suites cover them. Caution: they still carry `z-index:1000` and no `max-height` and pass only because their panels currently *fit* — the consolidated CSS must not be "helpfully" shared into them |

### What crosses `localStorage` today, and what changes

| channel | today | after |
|---|---|---|
| `fieldgold_record` | the durable record (bench/site/occurrence/photo) | **unchanged.** It is a record, not a hand-off |
| `fieldgold_sites` (legacy blob) | `index.html:2736` writes it; `map.html` reads it as untrusted input with counted drops | **stop writing, keep reading.** Old devices hold it, and dropped records are reported rather than skipped |
| `kind:'occurrence', pending:true` | the single-slot hand-off | **replaced by the working set**, per N1 |
| `fieldgold_rem_seeded_v1/v2` | seed flags | untouched |
| the seven `t-*` toggles | not persisted; markup defaults | in one document, checkbox state survives a view switch for free. **Hazard to verify, not assume:** a hidden map view still holds its Leaflet layers; it should not request tiles while hidden (no `moveend`, no size) but will resume on `measure` |

**`sw.js` SHELL** keeps the same entries — the stubs are real URLs — and adds
nothing. It **requires a cache version bump**, because `index.html`'s contents
change and the fetch handler is cache-first with no revalidation, so the version
string is the entire delivery mechanism. Per that file's own v10 note: the bump
delivers to browsers and to **nobody's phone**; the shell needs `npx cap sync` +
rebuild + install.

### Ground rule 7: the new paths, and how the banner is guaranteed

Rule 7 names four paths — success, HTTP error, network failure, re-opening an
old photo. A view swapper adds **seven it does not name**:

1. First load straight into `#/photo` — `init` has never run.
2. Re-entering the photo view from another view — `enter` without `init`.
3. **Returning to the photo view with a previous result still in the DOM.** The
   sharpest new one: the page always started fresh before, and a persistent DOM
   does not. A stale banner beside a stale result, or a surviving result whose
   banner was never recomposed.
4. Reload while on `#/photo` — route restoration.
5. `pageshow` with `persisted` — back/forward cache;
   `fieldgold-data.js` already fires `onChange` here and the DOM returns intact.
6. Back/forward through hash history into the photo view.
7. `onChange` firing while the photo view is active and re-rendering — must not
   touch the results pane and drop the banner.

**The guarantee must be structural, not vigilance.** Today `landBanner(land)` is
prepended at **five** call sites (`index.html:2120, 2165, 2172, 2216, 2241`) —
five chances to forget.

- **One writer.** `renderPhotoResult(bodyHtml, ctx)` composes
  `landBanner(ctx) + bodyHtml` and is the *only* thing that writes that
  container. A direct `innerHTML` assignment to it becomes a defect a grep can
  find.
- **`enter` clears the result pane** unless the context it was composed with is
  re-resolved. Default to clearing: a stale banner is worse than an empty pane.
- **Assertion:** for each of the seven paths, the results container is either
  empty or contains a `.land-banner`. Stronger than the current per-call-site
  arrangement can support.

Rule 4's routing side: the registry/tab-bar completeness assertion; unknown hash
→ `evaluate`; and no view renders a bench list before `statusOf` resolves — free
today because storage is synchronous, and **not free in Phase 2**, which rule 7's
async note already covers.

### What Design 1 forecloses

A path-based router; server-side rendering; any future where the map is a
separate document (the closure, once opened, will not want to close); and the
option of consolidating `creek_manual.html` later without re-arguing the no-JS
property.

---

## Design 2 — The working set

### Naming

Internal noun: **working set**. User-facing it must not contain "site" or
"saved". Proposed: **"Selection"** for the ambient set and **"Trip"** for the
ordered artefact, because D3 makes ordering a distinct act and giving the ordered
thing its own noun keeps "selection" honest. Final words are Alan's.

### What a working point carries

Session shape, **not** a schema:

| field | meaning |
|---|---|
| `id` | ephemeral (`ws-1`…), **not** a record id |
| `lat`, `lon` | the only required pair |
| `origin` | `feature` \| `pick` — the load-bearing field |
| `featureKind` | when `feature`: `bench` \| `rem` \| `site` \| `occurrence` \| `geochem` |
| `recordId` | present only when the feature came from `fieldgold_record` (bench/rem/site). Absent for occurrence/geochem, which come from a live query and have no record |
| `label` | profile number, ARDF site name, sample id, or "picked spot" |
| `tier` | **only when the point IS a record carrying `land_status`.** Never derived, never defaulted |
| `context` | the `contextForPoint()` result — what a pick has *instead of* a tier |
| `pickedAt` | timestamp; needed for D6's staleness statement |
| `seq` | `null` until ordered (D3/D4) |

**The rule 4 invariant: a working point has EITHER `tier` OR `context`, never
both, and the UI renders from whichever it has.** A pick shows the context
headline and detail — amber or rust, never green, because `contextForPoint()`
never reports a position as clean — plus a sentence saying there is no bench
check at this position. A feature point shows its own tier word.

**The set's summary never aggregates the two.** Not "3 selected, 1 clean" but
*"3 selected · 1 clean bench · 1 avoid bench · 1 picked spot (no bench check)"*.
A pick is never folded into a tier bucket. No new tier value; no widening of
`contextForPoint()`.

### Entry, exit, display

**Entry.** From a feature: tapping the marker adds it *and* opens the popup
(Design 4). From blank ground: the existing identify popup's ＋ button changes
destination — same tap, same coordinates, same habit (D5), into the set instead
of into `fieldgold_record`.

**No cap yet.** An unbounded set will eventually be a legibility and render
problem, but the number must come from measuring marker and list render cost,
not from feel. Until measured: no cap, risk stated.

**Exit.** Per-point remove, from the list and from the popup. Plus one **Clear
all** with a confirm — the only destructive act on the set, and the answer to D6
that events cannot provide.

**Display on the map.** Working points draw in their own `L.layerGroup` above
the others, marked by **geometry, not colour** — a concentric halo/outline whose
presence is binary and readable in monochrome, plus a numeral once ordered.
Because Phase 1 item E establishes that colour is already carrying more than it
can, selection must not be a hue.

**The underlying marker's fill is never repainted.** Selection is additive.
Selecting a bench does not change what its colour says, and that is assertable:
the fill attribute is byte-identical selected and unselected.

Three things stay distinguishable: plotted feature (as today), working point
(feature + halo), saved Site (as today, `weight:3` if avoid). A saved Site can
also be selected; the halo composes.

### How the views read it

| set state | Evaluate | Sites | Plan |
|---|---|---|---|
| empty | unchanged — manual entry | saved sites only | "nothing selected — tap features on the map" |
| one | offers that point, exactly today's modal minus the storage round-trip | "Selection (1)" affordance | ordering is a no-op; export offered |
| several | **a picker listing every point with its tier or context.** Today's code takes `pending[0]` silently; the set fixes that rather than inheriting it | "save these as sites" — per-point, deliberate, confirm lists what will be written | the ordering step |

**Plan is a section, not a new tab.** The bar has six and D1 adds Map = seven,
which is already the practical limit at phone width.

### Ordering and export (D3, D4)

- The set is **unordered until the user orders it**. Ordering assigns `seq`.
- **Adding after ordering appends as unsequenced.** A new point gets
  `seq: null` and appears in an "unplaced (2)" group. **Nothing renumbers
  automatically** — that is D4 stated mechanically.
- Removing an ordered point **compacts** the sequence, because a gap reads as a
  lost stop.
- **Export leaves the set intact** and stamps `exportedAt`, so the UI can say
  "exported 12 minutes ago; 2 points added since". Export is terminal as an
  *act*, not as a destruction. Format: GPX plus the coordinate list; the two
  existing Apple Maps links stay as they are.

### The relationship to saved Sites, explicitly

- A working point is **not** a draft Site. It has no `kind`, is not in
  `fieldgold_record`, and never appears in the Sites list until saved.
- Saving stays deliberate and per point, or per selection with a confirm listing
  exactly what will be written.
- **After saving, the point stays in the set**, now carrying `recordId` and
  rendering as saved-and-selected. Removing it from the set never deletes the
  Site.
- **The one-way rule: nothing in the working set ever writes to
  `fieldgold_record` implicitly.** Today's ＋ button violates that, so this
  design is a net reduction in accidental permanent writes. That is its
  strongest justification.

### What the working set needs from storage

**One `localStorage` key. No schema. No Phase 2 dependency for the mechanism —
two Phase 2 obligations to name.**

`fieldgold_workingset` = `{updated, points[]}`. Three reasons it is not
something else:

- **Not `fieldgold_record`.** The set is not a record. Mixing them means every
  existing reader (`get('site')`, `readAll()`) can mistake a working point for a
  site, and `stampStatus` would begin stamping tiers onto points that must not
  have one. That is the rule 4 argument for a separate key, and it is decisive.
- **Not `sessionStorage`, and this is where D6 cannot be satisfied by an
  event.** There is **no `@capacitor/app` plugin installed** — `package.json`
  holds only `@capacitor/cli|core|ios` — so the shell has no native lifecycle
  callback; only web events exist. `visibilitychange` fires identically for
  "switched apps" and "about to close"; iOS Safari does not fire `beforeunload`
  reliably; and an app-switcher kill in the shell terminates the process **with
  no JS event at all**, the same silent-failure shape as the service worker. So
  **"deliberate exit" is not detectable on either distribution.**
  `sessionStorage` behaves correctly on web (tab close clears it) and **wrongly
  in the shell**, where an iOS reclaim destroys the twenty-minute traverse —
  exactly D6's stated worry. `localStorage` behaves the reverse.
- **Therefore `localStorage`, plus an explicit Clear control, plus a visible
  age** ("selection from 14:22 — 4 points"). "Deliberate exit" becomes a control
  the user presses rather than an event the app infers. **Untested and must stay
  marked so: whether `pagehide` fires at all in the shell on an app-switcher
  kill.**

**Two named Phase 2 obligations, not designed around:** the `tier`/`context`
fields must survive whatever the record migration does to `land_status`; and
**iOS can evict WKWebView `localStorage` under pressure** — which is one of the
three things D8 says native exists for. Until then the working set is
durable-ish and the UI must not promise more.

### N1 — the compat obligation

Devices already hold `kind:'occurrence', pending:true` records. **Ruled 2026-07-29:
option (a).** On first boot of the consolidated app, convert them into working
points and remove them, once, with the seed v1→v2 care: **convert in place, add
nothing that is not there, never resurrect a deleted one.** This is a data
migration, so ground rule 3 applies with the same weight it applies to the
seeder.

---

## Design 3 — Layer defaults and tile honesty

Built to the D7 ruling above: query layers off, record layers on, basemap not a
toggle.

### AMENDED 2026-07-29 — the two layer classes do not report through the same sentence

> **This section originally treated all query layers alike.** After the BLM
> measurement (`STATE.md`, "the BLM layer is SETTLED"), that was **the failure
> this phase exists to fix, one level up, in our own instrumentation**: a
> per-layer count that means "the layer is working" for one class and "the server
> answered with an image" for another, **reported in the same words**, is absence
> rendering as presence in the reporting channel. Alan's ruling: amend.

**The two classes, stated explicitly, because the difference is invisible in the
code and decides what the app may claim:**

- **The WMS layers — `ardf`, `geo`, `terrain`.** `docs/map.html` sets **no
  `EXCEPTIONS` parameter** (`:168`, `:197`), so the WMS 1.3.0 default of `XML`
  applies and a server-side rejection comes back as **non-image bytes**. The
  `<img>` load fails, `tileerror` fires, item D counts it. **A count therefore
  distinguishes "answered" from "rejected"**, and the existing sentence is
  honest for these three.
- **The claims layer — the ArcGIS `export?` endpoint (`:185`).** It does not.
  The app can establish that **a response arrived** and that **it was an
  image**. It cannot establish that **the request was well-formed.** Measured
  2026-07-29: `bboxSR=99999` and `layers=show:99` both return HTTP 200,
  `image/png`, **886 bytes, md5 `7be830c6…` — byte-identical to a correct empty
  answer over Hatcher Pass.** Not similar to the right answer: the same object.
  A malformed `bbox` returns a different 200 PNG with 276 faint pixels, which is
  also a successful load. Only a non-image response (`size=abc` → `text/plain`
  JSON) or an unreachable server produces `tileerror`.
- **Therefore the two classes must not report through the same sentence.** There
  is no wording that is true of both.

### What the app says for the claims layer — proposed

Held to rule 5 (the page says what is unverified) and to the existing discipline
(report what was counted, never guess a cause). **The acceptance test this had to
pass: a reader who sees only the claims-layer message, and who does not know the
ArcGIS/WMS distinction, must not come away believing the layer was verified as
working.**

**The structural rule, which is the part that matters more than the words: the
two classes use different verbs, and the claims layer never gets a tick.**

| | WMS layers (`ardf`, `geo`, `terrain`) | the claims layer |
|---|---|---|
| tiles arrive | `ardf: 12 of 12 tiles loaded` | `claims: 12 images received — NOT verified` |
| second line | — | `this layer answers 200 with a blank image whether the request was right or wrong; blank here is not "no claims"` |
| nothing arrives | `ardf: 0 of 12 tiles loaded — the layer did not answer` | `claims: 0 of 12 images received — the layer did not answer` |
| ever prints ✓ | may | **never** |
| verb | **loaded** — which the app can establish | **received** — which is all the app can establish |

Same sentence shape, different verb, so the difference is visible without a
footnote and without a lecture. "Received" is the whole claim: bytes arrived and
were an image. "NOT verified" is what stops the sentence being read as a tick.
Neither line guesses a cause, and neither says "no coverage".

Two things this deliberately does **not** do: it does not repeat the
federal-register explanation that the panel already carries in full — the second
line is the short form, at the moment of the event — and it does not attempt to
distinguish a rejected request from an empty answer, because that has been
measured to be impossible for this layer.

### The kind question — RULED 2026-07-29: no third kind. Two kinds stay.

The question was whether the claims line needs a kind of its own. Item C
classifies each line at the call site as either a land-status line or a failure,
with **failure as the default**, so a warning added later without a kind is
over-reported rather than silently omitted. The claims line is **neither**: it is
not a land-status warning and it is not a failure — it is the app stating what it
cannot verify, which is rule 5's category.

**Alan's ruling: no. The claims line gets no kind**, which makes it a failure by
default and lets it headline the problem row. Over-reporting is what item C's
ruling already prefers to silent omission, and this is exactly that case.

**The reasoning, recorded because a later session will find the classification
uncomfortable and want to fix it.** A third kind would be *correct* and would
cost more than it is worth. **Every kind added is a kind every future call site
has to choose between**, and the failure mode of a three-way choice is a line
classified into the quiet bucket by somebody in a hurry. **Two kinds with a known
over-reporting case is safer than three kinds with a new way to under-report.**

**What the ruling costs, stated so it is not discovered later as a bug.** The
problem row will headline

> `claims: 12 images received — NOT verified`

**as though it were a failure, on a run where nothing failed.** That is noise. It
is deliberate. **It is the direction this project fails in** — the same direction
as `unchecked` never becoming `clean`, and as failure being the default kind.

**If it proves noisy enough in the field to matter, the fix is a third kind, and
this ruling is the thing to revisit.** It is **not** a quiet reclassification of
the claims line into the land-status kind, which would hide it in the bucket that
does not headline — the exact under-reporting the ruling exists to prevent. Reopen
the ruling; do not route around it.

**Assertable in the harness, no network needed:** the claims layer's line never
contains "loaded" and never contains "✓". Plus the static tripwire that now
exists — `tests/test_stage_maps.py` asserts the literal `bboxSR`, `imageSR` and
`layers` values in every page that builds that URL, with two mutants
(`claims-sr`, `claims-layer`) verified caught.

### What the app says when tiles fail

PR #6's item D gives per-layer tile outcomes. The honest message is built from
counts, and **the app must not guess a cause** — because it cannot.

**Can overload be distinguished from no coverage? No, and the asymmetry is worth
stating exactly:**

- A **failing** tile errors or times out. That *is* detectable, and item D
  already counts it.
- A tile **outside coverage** typically returns HTTP 200 with a blank or
  transparent image, which Leaflet counts as **loaded**. Without reading pixels,
  "covered and empty" and "not covered" are the same observation.
- **Overload versus the server being down is also not distinguishable.**
  `tileerror` hands you the tile and an error event, not a status code. A 429
  would settle it if the provider sends one — unknown, untested. A single
  diagnostic `fetch` of one failed tile URL could read a status; that is one
  request on failure, not a load-time dependency, so rule 2 permits it. Optional
  and unverified.

**The rule: report what was counted, and say what a blank does not mean.** For a
toggled-on query layer with zero loads:

> `claims: 0 of 12 tiles loaded — the layer did not answer.`
> `A blank claims layer is not "no claims here".`

The second line is the federal-register discipline reused in shape, and it is the
point: **a user will read overload as absence**, which is that bug arriving
through the basemap. Both lines are `failure` kind and headline in item C's
problem row.

**The app never says "no coverage" and never says "too many layers".**

Also proposed: **enabling a query layer states what it will do** — one line
naming the external service it fetches from. Rule 5, at the moment the user
chose the cost.

### The politeness reason, which is also the scaling reason

Recorded as a reason for the default, not only as performance. Six layers on by
default is **48 measured tile requests per pan**, to USGS, BLM, Esri and a
volunteer tile server this project has no agreement with. One user is fine. Many
are a burst, the block arrives without notice, and **the symptom is reports of
blank maps** — which the section above establishes the app cannot correctly
diagnose.

The OSM Foundation tile usage policy is quoted and dated in `STATE.md` under the
Phase 3 filing and the compliance flags; it reserves the right to block access
without prior notice, and it defines bulk downloading as *"any pre-emptive
fetching of tiles other than those a user is actively viewing."*

---

## Design 4 — The feature popup

**Tap a feature → add to selection AND open the popup.** One gesture, two
effects, both visible.

**Second tap on an already-selected feature toggles selection off, and the popup
stays open showing the change.** A toggle whose result you cannot see is how a
point is lost silently, so the popup is the receipt. Accidental double-taps are
already discriminated from pans by the measured 15px `TAP_TOL` (`map.html:552`).
**The rule that makes this safe: a selection change never closes the popup.**

**Contents, in order:**

1. **Which layer it came from** — required, not optional. With query layers off
   by default and toggled deliberately, a lone marker is ambiguous between a
   bench candidate, a geochem sample and an ARDF occurrence.
2. Label, and the tier badge (`CLEAN` / `NOT CHECKED` / `AVOID` as words,
   exactly as `statusBadge` does today) **or** the context block for a pick.
3. The description, in a bounded scroller.
4. A footer: `In selection ✓ · tap again to remove`, or `＋ Add to selection`.

**The bounded scroller, and what is visible at rest.**
`max-height: calc(100vh - var(--sa-top) - var(--fg-chrome-h) - 24px)`, its own
`overflow-y:auto`, `overscroll-behavior:contain`. At 390×844 with real insets:
**the layer line, the label, the tier row and the footer are always visible
without scrolling; the description scrolls.** The footer is pinned, because a
selection control that requires scrolling to find is the untappable-toggle
failure in a smaller box.

**The `#status` lesson applies literally.** A Leaflet popup is created and
inserted before it has a layout box, so any scroll-position or height maths must
run after `popupopen`, never at construction — otherwise it is
`scrollTop = scrollHeight` writing 0 to 0 again. **Any assertion about this
scroller is gated on computed `overflow-y`**, per the surviving `no-overflow`
mutant, not on `scrollTop` accepting a value.

**Z-order:** Leaflet popups live in the map pane, below `#panel` (1200) and below
`.fg-chrome` (1500). The problem row therefore stays on top of the popup, which
is correct and should be asserted.

**ARDF occurrences.** Ground rule 4's physical-hazard boundary applies. Today's
occurrence popup carries the Alaska Mapper caveat but **no physical-hazard line
at all**, while the bench popups already carry *"Shown so you can recognise and
avoid it, not so you can visit it."* The requirement: the ARDF popup states that
these are documented mine workings and that the app makes no claim about
approaching them, and it must not read as a recommendation to visit. **The exact
wording is Alan's** — land-status and hazard wording is not a thing this design
gets to draft.

**Phase 1 item E is not absorbed here.** The popup's tier is already text, so the
popup was never the colour-only defect; **the defect is the marker**, and it
stays filed. A builder must not read the popup work as having fixed E.

---

## What survives from PR #6

| item | verdict |
|---|---|
| **B** safe-area | **Survives intact, and is a prerequisite.** Everything at a screen edge — chrome bar, popup bounds, pinned footer, problem row — depends on `--sa-*` being real, which depends on `viewport-fit=cover` having landed first |
| **D** tile outcomes | **Survives; Design 3 consumes it directly.** Per-layer counts are what the honest message is built from |
| **C** problem row | **Survives, and consolidation improves it.** One bar for one document instead of one per page. `log(msg, cls, kind)`, call-site classification and the failure-headlines ruling carry over unchanged — and it now covers **all seven views**, closing a gap the record names as un-pulled: *"`index.html` has no equivalent of `#status`. Its offline failures have nowhere to be reported at all."* That comes free |
| **A** dead links | **Partly redundant. Nothing should be un-picked.** The three `href` fixes stop being *navigation* — there is no page to reach — but must not revert to `target="_blank"`, and the nine `https://` links stay exactly as they are. The back control's *purpose* is superseded by the tab bar, but WKWebView still gives no back gesture and D1's hash history creates a real need for a back affordance for child views, which that slot can carry. Most importantly the bar **survives in shape and becomes the navigation**: its own stylesheet says so — *"THIS IS THE ROUTER'S SEAM… same position, same shape and the same safe-area handling as index.html's existing `.tabbar`… The three back links collapse into it rather than being unpicked."* A is the foundation of Design 1, not a casualty of it |

---

## Verification: three categories

**Automatable (Playwright/node, no device):** registry ↔ tab-bar completeness
both ways; each of the seven rule-7 paths leaves the results pane
empty-or-bannered; the map container has non-zero size after `measure`; popup
scroller assertions gated on computed `overflow-y`; layer defaults (count of
`checked` = the record layers only); the "0 of N tiles" message and its "not the
same as no claims" line with the network blocked; every feature popup carries a
layer-of-origin line; the selection halo is present/absent as geometry and the
underlying fill is byte-identical either way; the working set survives a reload;
and **`readAll()` length unchanged after selecting five points** — the one-way
rule, made a test.

**Needs the device:** whether `pagehide` fires in the shell on an app-switcher
kill (D6's entire premise); whether the popup footer and chrome bar are tappable
with real insets; whether a hash route survives reloads under
`capacitor://localhost`; whether a hidden map view resumes correctly after
backgrounding; whether iOS evicts the working-set key; landscape, still never
measured on any target.

**Needs a person using the app — the category that found all of this:** whether
select → order → export is discoverable without being taught; whether
"Selection" reads as distinct from "Sites"; whether the halo is visible at arm's
length in sunlight; whether tapping a diamond *feels* like it did something; and
whether query layers off by default makes the map read as broken on first open.
That last one is a real risk with no automatable answer, and its mitigation is a
one-line prompt rather than an assertion.

---

## What this design does NOT address

- **Phase 1 item E's fix**, deliberately. The popup work touches adjacent code
  and must not silently absorb it.
- The Phase 2 schema.
- Phase 3 offline tiles — beyond the OSM policy finding filed in `STATE.md`.
- Phase 4 background GPS.
- The bundle/Pages divergence item. It is still open, and consolidation changes
  what "the tree" means for it, so it should be re-read after this lands.
- The stage maps' CSS debt (`z-index:1000`, no `max-height`).
- `tests/test_panel_reachability.py`'s `#status` exclusion gap. Item C addresses
  the symptom; the suite gap remains.
- Landscape.
- Removal of the `fieldgold_sites` legacy writer — named, not designed.
- Cross-device sync, which still does not exist. `README.md`'s "export often"
  stands.
- Any visual redesign. Every change above is structural or behavioural.
- The ARDF physical-hazard wording, which is Alan's.
- A cap on selection size, which needs measurement.
- The three OSM compliance items, filed in `STATE.md`.
