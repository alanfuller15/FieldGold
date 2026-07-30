# Prior art — the Phase 1 design, checked before it is built

**Run 2026-07-29 under `.claude/skills/prior-art/SKILL.md`. Findings only.
Nothing in `PHASE1-DESIGN.md` was changed by this pass, and nothing found here
has been adopted.** Amending the design is a separate decision and is Alan's.

**Why it was run.** `PHASE1-DESIGN.md` is approved and unbuilt, and it invents
vocabulary — "working set", "view registry", "problem row". Invented vocabulary
is exactly what prevents finding prior art, because the field that studied the
thing does not call it that. Six items were checked, ordered by how much a found
standard would change the build.

## Source tiers used below

Per the protocol, and stricter than a bibliography:

- **[fetched]** — the page was retrieved this session and the quoted words are
  its own. Seven sources.
- **[search-derived]** — taken from search-result summaries; the page was not
  retrieved. Treat as a pointer, not as a quotation.
- **[unverified]** — a source that could not be reached, recorded so the claim
  stands or falls on other grounds.

---

## Summary

| # | item | status |
|---|---|---|
| 1 | the working set | **PARTIALLY EXISTS** — two names, one documented failure mode, no unified pattern found |
| 2 | the D6 lifecycle problem | **EXISTS** — and it is a named platform primitive on Android |
| 3 | view swapping without a framework | **EXISTS** — and the field has already corrected it once |
| 4 | reporting failed / empty / out-of-coverage map layers | **EXISTS**, in two disciplines, which disagree |
| 5 | bounded scroller and pinned footer | **EXISTS** — a normative AA criterion names this exact construct |
| 6 | layer-of-origin at the feature level | **EXISTS** — a UI convention and a W3C Recommendation |

**Items returning NO PRIOR ART FOUND: none.** All six returned something. The
closest to a miss is item 1, where the *composite* mechanism was not found under
any single name — see its DELTA, which is where the genuinely novel part of this
design now sits.

---

## Item 1 — The working set

An ambient, multi-point, session-scoped selection, distinct from the persistent
record, readable by every view, orderable after the fact, surviving backgrounding
but cleared deliberately.

**STEP 1 — the rename.**
*What we call it:* the working set.
*What the field would call it:* a **selection set**, a **scratch layer** or
**temporary layer** (GIS), a **basket** / **cart** / **shortlist** (general UI),
or **uncommitted** / **staged** state (software).

**Query 1, verbatim:**
`"selection set" pattern interaction design uncommitted selection versus saved record terminology`

**Query 2, verbatim:**
`QGIS temporary scratch layer memory layer not saved warning documentation`
*Dimensions varied: **DISCIPLINE** (interaction-design vocabulary → GIS
application documentation) and **ABSTRACTION** (pattern name → a concrete
shipped implementation and its bug reports).*

**Query 3, verbatim** (extra, because this is the largest invented mechanism):
`interaction design pattern library collection basket shortlist "compare later" pattern name Tidwell Designing Interfaces`
*Dimension varied: **REGISTER** (pattern-library vocabulary).* **Returned
nothing usable** — the book exists, its contents were not reachable. Recorded as
searched-and-did-not-find, bounded by non-access rather than by absence.

**NAME** — Two established names, from different directions:
- **"selection set"**, and specifically the distinction between a live selection
  and a **"saved selection set"** that can be named, added to, and re-saved
  [search-derived].
- **"temporary scratch layer"** / **"memory layer"** — QGIS's term for a layer
  held in memory, not written to disk, discarded when the application closes
  [search-derived].

**STATUS — PARTIALLY EXISTS.** Each half of the mechanism has a name. The
*composite* — multi-point, cross-view, orderable-after-the-fact, session-scoped,
survives-background-but-not-exit — was not found under any single name.

**THE STANDARD** — No specification governs this. QGIS's user manual
(`docs.qgis.org`, Creating Layers) documents scratch layers as behaviour, and
QGIS issues #30958 and #8387 and the "Improve scratch layer Save UI" thread are
the field arguing about the boundary [search-derived].

**WHAT THEY LEARNED** — this is the valuable part, and it is a warning:

- **Users lost work by closing a project and ignoring the warning that scratch
  layers were unsaved** [search-derived, QGIS issue tracker]. The temporary
  category is where data goes to die.
- **"Experienced users not knowing what scratch layers were."** The *naming* of
  the intermediate state is itself a failure mode. This is direct evidence
  against relying on a well-chosen word to carry the transient/committed
  distinction, and it bears on the design's open "Selection" vs "Trip" naming
  question and on `STATE.md`'s recorded worry that the app had to be *taught* to
  a second person.
- QGIS's own remedy is **a warning at the moment of loss**, plus a one-action
  path from temporary to permanent ("save these to a real layer"). Both are in
  the approved design already — the Clear-all confirm and the per-point "save as
  site".
- The saved-selection-set literature adds the expectation that a set can be
  **named** and **re-saved under a new name** [search-derived] — a capability the
  design does not have and does not obviously need.

**FIT**
- The names fit and should be used in conversation about this work, because they
  are what makes the next search possible. "Scratch" is the closer analogue:
  session-scoped and explicitly not the record.
- The GIS analogue **breaks in one important place**: a QGIS scratch layer is
  *edited* data awaiting persistence, whereas a FieldGold working point is
  mostly a *reference* to something already persistent (a bench record that
  exists and is not being changed). The loss profile is therefore milder here —
  losing the set loses the *selection*, not the data — which weakens the
  data-loss argument for durability and strengthens the D6 argument, which is
  about the user's twenty minutes rather than about the bytes.
- Nothing found contradicts the design's one-way rule (the set never writes to
  the record implicitly). Nothing found endorses it either; it appears to be
  ours.

**DELTA** — what remains genuinely ours: the **ordering-after-selection** step
with `seq: null` for later additions (D3/D4), the **tier-or-context invariant**
(a working point has one or the other, never both, and a pick can never render
as clean), and the **cross-view read** by Evaluate / Sites / Plan. No source
found addresses a selection whose members carry a *legal status* that must not be
aggregated across provenances.

---

## Item 2 — The D6 lifecycle problem

"Survives backgrounding, cleared on deliberate exit", where the design
established that deliberate exit is not detectable on either distribution.

**STEP 1 — the rename.**
*What we call it:* survives backgrounding, cleared on deliberate exit.
*What the field would call it:* **state preservation and restoration**;
**saved instance state**; the distinction between **system-initiated process
death** and **user-initiated termination**.

**Query 1, verbatim:**
`Android onSaveInstanceState survives process death but not user swipe from recents guidance`

**Query 2, verbatim:**
`Page Lifecycle API terminated state not reliably observable persist state on hidden visibilitychange`
*Dimensions varied: **DISCIPLINE/platform** (Android native → the web platform)
and **ABSTRACTION** (one API's behaviour → the lifecycle model and its
spec-level guidance).*

**Query 3, verbatim** (extra, third platform):
`Apple UIKit state preservation restoration archive deleted when user force quits app documentation`

**NAME** — **"saved instance state"** (Android), **"state preservation and
restoration"** (UIKit), **"page lifecycle"** (web).

**STATUS — EXISTS.** The distinction D6 asks for is not only expressible, it is
**a documented platform primitive on Android**, and it is **documented as
unobservable on the web**. Those two facts together are the answer to the
brief's question.

**THE STANDARD**

Android's official comparison table, from
`developer.android.com/topic/libraries/architecture/saving-states` [fetched]:

| mechanism | config change | **system-initiated process death** | **user complete dismissal / `finish()`** |
|---|---|---|---|
| ViewModel | Yes | No | No |
| **Saved state** (`SavedStateHandle`, `rememberSaveable`) | Yes | **Yes** | **No** |
| Persistent storage | Yes | Yes | Yes |

**The middle row is D6, exactly.** "Saved state bundles persist through both
configuration changes and process death" and do not survive user dismissal.

The web platform's position, from `developer.chrome.com/docs/web-platform/page-lifecycle-api`
[fetched], quoted:

- *"The discarded state is not observable by developers at the time a page is
  being discarded."*
- *"The transition to hidden is also often the last state change that's reliably
  observable by developers (this is especially true on mobile…)"* — and
  developers should therefore *"persist any unsaved application state."*
- *"The `unload` event does not fire in many typical unload situations,
  including closing a tab from the tab switcher on mobile or **closing the
  browser app from the app switcher**."*
- *"the transition to the terminated state cannot be reliably detected in many
  cases (especially on mobile)."*

Apple: the archived *View Controller Programming Guide*, "Preserving and
Restoring State" [fetched], says what preservation is *for* — you save
*"References to any data being displayed **(not the data itself)**"* and
*"Information about the current selection"*. **It does not contain the
force-quit-deletes-the-archive statement**, which practitioner sources assert
[search-derived]; the modern replacement page
(`developer.apple.com/documentation/uikit/preserving-your-app-s-ui-across-launches`)
is a JavaScript-only site and returned only its title **[unverified]**. So: the
iOS claim is *not* established here, and the report does not rest on it.

**WHAT THEY LEARNED**

- **The distinction is real, and platforms that expose it separate it from data
  storage.** Apple's preservation model is explicitly for *UI state* and
  explicitly excludes the data itself; Android's table puts anything that must
  survive user dismissal in *persistent storage*. **The field's test is not "is
  this session state" but "would the user mourn it".** A twenty-minute traverse
  is mourned, so by the field's own division it is data, not UI state — which is
  the design's conclusion, reached from a different direction.
- **`unload` and by extension `beforeunload` do not fire when an app is closed
  from the app switcher.** The design recorded this as untested for the shell;
  the web platform documents it as *not firing* for browsers. WKWebView is the
  same engine, so the inference is strong — but Capacitor is not a browser tab
  and **the shell case is still not device-verified.** Do not upgrade the tier.
- The prescription is uniform across all three: **write state at `hidden`,
  never at exit.**

**FIT**
- The design's choice — one `localStorage` key, an explicit Clear control, a
  visible age — **is what the web platform's own guidance prescribes**, and the
  Clear control is the substitute for the event Android has and the web does not.
- The Android table is worth keeping as the vocabulary for D8's feature
  divergence: the native build *could* have true D6 semantics through a native
  plugin; the web build cannot, by construction. **That is a feature divergence
  D8 says must be visible to the user rather than silent.**
- Nothing found contradicts D6. Nothing found makes it implementable on the web.

**DELTA** — ours: the wording that states the set's age honestly on a
distribution that cannot clear it at exit, and the decision about whether the
native build should later acquire real saved-state semantics and thereby diverge
from the web build in behaviour.

---

## Item 3 — View swapping without a framework

The registry, `init`/`enter`, and the hidden-container measurement trap.

**STEP 1 — the rename.**
*What we call it:* a view registry with `init` and `enter`.
*What the field would call it:* **view-controller lifecycle**; **lifecycle
hooks**; **card layout** / **tabbed document interface**; and for the trap, **an
element with `display:none` generates no box**.

**Query 1, verbatim:**
`viewDidLoad versus viewWillAppear one-time setup versus every appearance view controller lifecycle convention`

**Query 2, verbatim:**
`CSS display none generates no box element not rendered getBoundingClientRect returns zeros specification`
*Dimensions varied: **REGISTER** (platform practitioner convention →
specification language) and **ABSTRACTION** (a lifecycle convention → the
standard that governs layout boxes).*

**NAME** — **`viewDidLoad` / `viewWillAppear`** (UIKit);
**`onCreateView` / `onResume`** (Android fragments). The design's `init`/`enter`
is a re-invention of a thirty-year-old convention, and the invented names are why
it did not look like one.

**STATUS — EXISTS**, and the field has already **corrected** it once.

**THE STANDARD** — no specification; a platform convention. UIKit: *"viewDidLoad
is called only once in the lifetime of a view controller, so you use it for
things that need to happen only once"*, while *"you override viewWillAppear for
tasks that you need to repeat every time a view controller comes on screen"*
[search-derived, multiple practitioner sources; Apple's own reference is on the
same JS-only site and was not fetched].

For the trap, the DOM side is unambiguous: with `display:none` the element *"does
not participate in layout, so every DOMRect dimension is zero"*, and
`getClientRects()` returns an empty list for elements that are not rendered
[search-derived, MDN]. `visibility:hidden` differs — it *"still reserves layout
space"*.

**WHAT THEY LEARNED** — the most useful finding in this pass:

**Two hooks were not enough, and iOS 17 added a third.** From
`useyourloaf.com/blog/uikit-view-lifecycle-viewisappearing/` [fetched]:

> *"The important point to remember about these methods is that the views frame
> (size and position) and traits, like the horizontal/vertical size class, are
> not updated until after the view has been added to the view hierarchy."*
>
> *"This leads to a problem if you want to update the view based on its size or
> traits. It's too early in viewDidLoad or viewWillAppear as the view is not yet
> added to the view hierarchy."*

`viewIsAppearing` exists because a hook that runs *before* geometry is final
cannot measure. **This is the same trap the design identified from
`#status`'s `scrollTop = scrollHeight` writing 0 to 0** — arrived at
independently, on two platforms, and the platform's answer was a new lifecycle
phase.

**FIT**
- The `init`/`enter` split is correct and has thirty years of precedent. Use the
  field's names in discussion so the precedent stays visible.
- **The design has a gap this exposes.** It says `enter` runs "after `.active` is
  applied", which in the DOM makes layout *available* but not necessarily
  *computed* at the moment the handler runs. The safe formulation, and the one
  the field's history argues for, is: **anything that measures must run after
  layout has been computed for the newly shown view, and must verify a non-zero
  size rather than assume one.** Whether that is a third phase, a forced reflow,
  or a `requestAnimationFrame` is an implementation choice; that it must be
  *stated* is the finding. Reported as a gap, not amended.
- Leaflet's `invalidateSize()` requirement in the design is the same fact in
  library form and is consistent with all of this.

**DELTA** — ours: the tab-bar↔registry completeness assertion (the field has no
equivalent, because a framework's router owns that relationship), and the rule 7
path enumeration, which is specific to this app's banner obligation.

---

## Item 4 — Reporting failed, empty and out-of-coverage map layers

The design establishes that the app cannot distinguish "layer failed", "layer
returned empty" and "outside coverage", and must not guess.

**STEP 1 — the rename.**
*What we call it:* tile honesty.
*What the field would call it:* **service exception reporting** (OGC), and
**uncertainty / missing-data representation** (cartography). Framed generally:
**absence of evidence versus evidence of absence.**

**Query 1, verbatim:**
`OGC WMS EXCEPTIONS parameter INIMAGE BLANK service exception blank image standard`

**Query 2, verbatim:**
`cartography convention distinguishing "no data" from zero missing data uncertainty visualization map legend`
*Dimensions varied: **DISCIPLINE** (service/protocol engineering → cartography)
and **ABSTRACTION** (a protocol parameter → representational theory and
convention).*

**STATUS — EXISTS in two disciplines, and they answer differently.** This is the
item where prior art most changes the picture.

### 4a. The protocol already anticipated this, and named both behaviours

**NAME** — the WMS **`EXCEPTIONS`** request parameter.

**THE STANDARD** — OGC WMS 1.3.0. Valid `EXCEPTIONS` values for `GetMap` are
**`XML`**, **`INIMAGE`** and **`BLANK`**:
`application/vnd.ogc.se_xml`, `application/vnd.ogc.se_inimage` (*"error text
embedding in image"*), `application/vnd.ogc.se_blank` (*"blank image"*). A
conformant server **shall** support `INIMAGE` and **shall** support `BLANK`
[search-derived: GeoServer WMS reference, MapServer WMS server docs, DGIWG 112
profile, Oracle Map Visualization docs]. The OGC specification itself was not
fetched — **[unverified]** as a primary source, though four independent
implementation documents agree.

**WHAT THEY LEARNED** — the standard contains both the disease and a cure:

- **`BLANK` is the standard's name for the exact ambiguity the design
  identified.** A server told to return a blank image on error produces a
  failure that is pixel-identical to empty coverage. The design discovered by
  measurement what the specification defined in 2004.
- **`INIMAGE` is the standard's answer**: the failure describes itself, in the
  tile, where the user is already looking.

**FIT** — and **this is a conflict to rule on, not to resolve here.**

- Measured in this tree [self-tested] 2026-07-29: `docs/map.html` sets **no
  `EXCEPTIONS` parameter** on either WMS layer (`:168` ardf/geochem, `:197`
  terrain). Per the spec the default is `XML`, so a failure returns non-image
  bytes, Leaflet raises `tileerror`, and PR #6's item D counts it. **Today's
  failures are detectable for the WMS layers**, which is why the design's
  counting approach works at all.
- The BLM layer is **not** WMS — it is an ArcGIS `export?` with `f:image`
  (`:185`), so its error behaviour is ArcGIS's, not the standard's, and
  **whether it returns a blank image on failure is untested.** That is the layer
  whose entire on-screen treatment exists to stop a blank being over-read.
- **`EXCEPTIONS=INIMAGE` would put a third party's error text onto the map
  surface.** The design's Design 3 deliberately reports in the problem row and
  never guesses a cause. Adopting `INIMAGE` means uncontrolled remote text
  rendered over the map a person reads in terrain. That touches rules 4 and 5 in
  opposite directions — more honest about failure, less controlled about
  wording — and **it is a decision, not a design detail.** Reported, not
  resolved.

### 4b. Cartography's answer: give absence its own visual class

**NAME** — **uncertainty visualization**, and specifically **intrinsic** vs
**extrinsic** techniques; plus the treatment of **"no data"** as a class.

**THE STANDARD** — no normative spec found for the *interface* case. Penn State's
GEOG 486 course text [fetched] defines the division:

> *"Intrinsic uncertainty visualization techniques cannot be visually separated
> from the visualization of one or more other variables, while extrinsic
> visualization techniques are easier to interpret separately."*

and notes that with an intrinsic technique such as transparency, *"The two
variables are combined together to create the legend as well."*

The practitioner and textbook convention: **"no data" values should be excluded
from the classification but should still be visualized, and visualized
differently from the other classes** — commonly grey, or a hatched overlay
[search-derived: cartography course texts and practitioner pages]. There is also
a paper titled *"Representing the Presence of Absence in Cartography"*, which is
this problem by name; **[unverified]**, ResearchGate, title only.

**WHAT THEY LEARNED** — **absence gets a symbol.** The field's settled answer to
"how do you show that silence is not an answer" is not to leave the space blank
and explain in text — it is to **give the absence its own visual class, outside
the data classes, and put it in the legend.** Hatching (extrinsic) keeps the
uncertainty separable from the data underneath; transparency (intrinsic) does
not.

**FIT** — a genuine tension with the approved design, reported as such:

- Design 3 leaves the map blank and reports counts in the problem row. **The
  cartographic convention would symbolize the failure on the map itself.** Both
  are defensible; they are different answers to the same question, and the
  field's is the older one.
- **It is only partly applicable, for a reason the design already established:**
  you can only symbolize what you can detect. A *failed* layer is detectable, so
  it could carry a hatch. **"Outside coverage" is not detectable** — a blank
  200-response is indistinguishable from covered-and-empty — so no symbol can be
  drawn for it honestly. Cartography's convention assumes the data source *tells
  you* which cells are no-data; a tiled web service does not.
- Consequence worth stating: adopting hatching for the detectable case would
  make the *undetectable* case conspicuous by its plainness, which is arguably an
  improvement and arguably a new false signal. Alan's call.

**DELTA** — ours: the specific wording that a blank layer *"is not 'no claims
here'"*, which is this project's own federal-register discipline and has no
cartographic equivalent; and the decision on `EXCEPTIONS` and on hatching.

---

## Item 5 — The bounded scroller and the pinned footer

**STEP 1 — the rename.**
*What we call it:* a bounded scroller with a pinned footer in a popup.
*What the field would call it:* a **sheet** or **bottom sheet** with a **peek
height**; and for the pinned control, **sticky footer** — which a WCAG criterion
names directly.

**Query 1, verbatim:**
`WCAG 2.2 success criterion 2.4.11 focus not obscured minimum sticky footer 2.5.8 target size`

**Query 2, verbatim:**
`Material Design bottom sheet peek height show partial content indicate more scrollable guidance`
*Dimensions varied: **REGISTER** (normative standard → platform design
guideline) and **ABSTRACTION** (conformance criterion → concrete component
guidance).*

*(Note: WCAG appears here on **different criteria** from the already-grounded
1.4.1. This is new ground, not a re-check of recorded work.)*

**NAME** — **peek height** (Material), **sticky footer** (WCAG), **target size**
(WCAG).

**STATUS — EXISTS**, and one of the standards names this exact construct as a
hazard.

**THE STANDARD**

**WCAG 2.2 SC 2.4.11 Focus Not Obscured (Minimum), Level AA**, from
`w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum` [fetched]:

> *"When a user interface component receives keyboard focus, the component is
> not entirely hidden due to author-created content."* (Level AA)
>
> *"Typical types of content that can overlap focused items are sticky footers,
> sticky headers, and non-modal dialogs."*
>
> *"This AA criterion allows for the component receiving focus to be_partially_
> obscured by other author-created content."*

Remedies the page names include making the overlay modal, **scroll padding**, or
auto-closing on focus loss.

**WCAG 2.2 SC 2.5.8 Target Size (Minimum), Level AA** — interactive targets at
least **24×24 CSS pixels** [search-derived from the same result set; the
Understanding page for 2.5.8 was not fetched].

**Material Design, bottom sheets** — the collapsed resting state shows only its
**peek height**, and that height *"should have enough height to indicate there is
extra content for the user to interact with"* [search-derived: m2.material.io
and material-components-android docs].

**WHAT THEY LEARNED**

- **The sticky footer is the canonical thing that obscures what the user needs
  to see.** WCAG names it in the first breath. The design's pinned footer is
  precisely this construct.
- **Partial obscuring is permitted; total obscuring fails.** The criterion draws
  the line the design needs.
- **A resting height must advertise that more exists.** Material's peek-height
  guidance is the field's articulation of the design's "state what is visible at
  rest", and the antidote to a container that looks like it ends where it does
  not — the same class as the run log showing four of twelve lines.

**FIT**
- The design's 44px control size exceeds 2.5.8's 24×24 floor. Consistent; the
  standard's number is worth recording so a future change knows the floor is 24
  and the target is 44.
- The design's "state what is visible at rest" requirement is **already the
  field's**, which raises confidence rather than changing anything.
- **A gap this exposes.** The design now stacks **two** pieces of sticky
  content: the popup's own pinned footer and `.fg-chrome` at `z-index:1500`.
  2.4.11 is about *keyboard focus*, and a focused control inside the popup's
  scroller could be entirely covered by either. The design does not mention
  scroll padding or any focus-visibility obligation. **Reported as a gap.** Note
  the criterion is checkable in the existing Playwright harness, which makes it
  cheap.
- Ground rule 1 is untouched: these are patterns and criteria, not libraries.
  Nothing here suggests adopting Material as a dependency.

**DELTA** — ours: the specific numbers (`calc(100vh - sa-top - fg-chrome-h -
24px)`), the decision to pin the *selection* control rather than a close button,
and the requirement that assertions be gated on computed `overflow-y`, which
comes from this project's own surviving `no-overflow` mutant and is not in any
guideline.

---

## Item 6 — The feature popup's layer-of-origin line

**STEP 1 — the rename.**
*What we call it:* the layer-of-origin line.
*What the field would call it:* **identify results grouped by layer** (GIS
practice); **provenance**, **attribution** or **lineage** (information science
and geospatial metadata).

**Query 1, verbatim:**
`GIS identify tool results grouped by layer name convention multiple layers same location popup`

**Query 2, verbatim:**
`W3C PROV provenance ontology standard attribution wasDerivedFrom data source lineage ISO 19115`
*Dimensions varied: **DISCIPLINE** (GIS UI practice → information science /
semantic web) and **ABSTRACTION** (a UI convention → a formal ontology and
metadata standard).*

**NAME** — **"identify"**, whose results are **grouped by layer**; and
**provenance** / **lineage** for the underlying concept.

**STATUS — EXISTS.** This is settled practice, not an invention.

**THE STANDARD**
- **GIS convention:** in ArcMap's Identify tool, *"When features are listed in
  the Results List, they are grouped by layer"*, and stacked layers at one
  location all appear, grouped [search-derived: `desktop.arcgis.com`, Identifying
  features]. Layer names are also used as the disambiguator in menus where
  several similar layers exist.
- **W3C PROV-O** — a **W3C Recommendation** for provenance: entities,
  activities, agents, with relations including `wasAttributedTo`,
  `wasDerivedFrom` and `wasGeneratedBy`, used to *"form assessments about
  quality, reliability or trustworthiness"* [search-derived].
- **ISO 19115 / 19115-2 lineage** is the geospatial counterpart, and
  peer-reviewed work exists on combining the two to express provenance **at the
  dataset, feature and attribute levels** — i.e. exactly the granularity this
  item asks about [search-derived: Closa et al., *Computers, Environment and
  Urban Systems*; not fetched, **[unverified]** as a primary source].

**WHAT THEY LEARNED**
- **Grouping by layer is the convention precisely because a location can be in
  several layers at once**, which is the ambiguity the design identified from a
  different direction (layers off by default, so a lone marker is unattributable).
- Provenance is treated as **a property that travels with the datum**, not as a
  UI decoration — the standards model it at the feature and attribute level.
  That supports the design's decision to carry `featureKind` and `recordId` on
  the working point rather than reconstructing origin at render time.
- The purpose the provenance literature states — supporting an assessment of
  *trustworthiness* — is the same purpose this app's land-status registers serve,
  and it is a stronger argument for the layer line than "the marker would
  otherwise be ambiguous".

**FIT**
- The design's requirement is the field's convention, at feature granularity.
  Adopt the vocabulary; no mechanism changes.
- **PROV-O is not proportionate here** — it is an OWL ontology for distributed
  data exchange, and this is one line in a popup on a phone. Ground rule 1 is not
  at issue (nothing would be imported), but neither is the ontology useful. Its
  value is the *concept* and the search term.
- One thing the field does that the design does not: **group by layer when
  several features coincide.** The design specifies one popup per marker tap.
  Stacked markers at one coordinate — which this app has had before, when both
  bench functions drew every REM bench — would give one popup per tap with no
  indication that another feature sits underneath. **Reported as a gap, not
  amended.**

**DELTA** — ours: nothing substantial. This item is the field's convention and
the design should simply say so.

---

## Conflicts and gaps, collected

**Conflicts — reported, not resolved. Each needs Alan's ruling.**

1. **`EXCEPTIONS=INIMAGE` versus controlled wording.** The WMS standard offers
   self-describing failure tiles; adopting it renders a third party's error text
   on the map a person reads in terrain. Rules 4 and 5 pull in opposite
   directions.
2. **Cartography symbolizes absence; Design 3 explains it in text.** The field's
   convention is to give absence its own visual class in the legend. It is only
   partly applicable, because "outside coverage" is undetectable here, so
   adopting it for the detectable case may make the undetectable case read as
   fine.

**Gaps — things the design does not currently state, surfaced by the search.**

3. **`enter` must be defined as post-layout.** iOS added a third lifecycle hook
   because the second fires before geometry is final. The design says "after
   `.active` is applied", which is not the same claim.
4. **Focus visibility under two layers of sticky content.** WCAG 2.4.11 (AA)
   names sticky footers as the canonical obscurer, and the design stacks a pinned
   popup footer under `.fg-chrome`. No scroll-padding or focus obligation is
   stated. Checkable in the existing harness.
5. **Coincident features.** GIS identify groups results by layer when several
   features share a location; the design gives one popup per marker with no
   indication of what is underneath.
6. **Naming the intermediate state is itself a failure mode.** QGIS's users lost
   work because they did not know what a scratch layer was. The design's open
   "Selection" vs "Trip" naming question is more load-bearing than it looked, and
   the answer needs a person, not an assertion.

---

## What this pass did not check

- Anything already grounded and recorded: **WCAG 1.4.1**, the **OSM tile usage
  policy**, the safe-area work, and Leaflet's `_tileReady` behaviour. Item 5
  touched WCAG on *different* criteria, which is new ground.
- The OGC WMS specification as a primary document. Four implementation
  documents agree on the `EXCEPTIONS` values; the spec itself was not fetched.
- Apple's current documentation on state preservation. Its site is
  JavaScript-only and returned no body.
- The interaction-design pattern-library literature (Tidwell, van Welie) as
  primary sources. Searched, not reachable.
- Any of the six items against **safety engineering** or **human factors**,
  which the protocol names as candidate disciplines and which were not tried.
  Items 4 and 6 are the two most likely to have something there — absence of a
  signal versus a negative signal is a studied problem in alarm design.
