# FieldGold

A field kit for placer-gold prospecting the Mat-Su, built as one app you carry
on your phone. It doesn't find gold for you. It does the desk research, terrain
reading, and record-keeping that used to take a laptop and five browser tabs —
so you spend your field time walking the right ground instead of guessing.

Everything runs in your browser at **alanfuller15.github.io/FieldGold**. Add it
to your home screen and it installs like an app. The field-side tools work with
no signal — with one qualifier worth knowing before you rely on it: basemap
tiles come from the network, so offline you get your benches, your logged
sites, their land-status colours and their popups drawn on a blank background.
The map says so on screen rather than leaving you with an unexplained grey
rectangle.

---

## What it actually is

Four connected tools with one front door (Field Brain), sharing one record of
your prospects:

**Field Brain** — the hub. Evaluate a spot against eight weighted
placer-favorability indicators (documented source, mining history, traps,
bedrock, colors, black sand, gradient, access), log it with GPS, research it
against real government sources, analyze a photo of the ground with a vision
model, and read nine Alaska-tuned geology articles. Export everything to GPX for
onX, Gaia, or Garmin.

**The gold map** — every documented gold occurrence (USGS ARDF), stream-sediment
sample (USGS geochem), and **federal** mining claim (BLM) in the area, on one map
with satellite, streets, and topo views. Tap any spot to check it for documented
gold and for federal claims — which on this state ground is a near-empty
register, where blank does not mean "no claims". Your logged sites and your
bench candidates show here too.

**The bench hunter** — reads the river's terrain and flags old stranded channels
(benches) worth walking. More on this below, since it's the least obvious piece.

**The creek manual** — how to read a creek on the ground: where gold concentrates,
what to look for, how to work it.

They're connected. Log a site in Field Brain and it appears on the map. Run the
bench hunter and its candidates appear on the map. Tap a documented gold spot on
the map and send it to Field Brain to evaluate. One shared record, one kit.

---

## The one principle behind all of it

The tool never pretends to know more than it does. Every claim is tagged by how
well it's grounded. A geochem sample that couldn't detect gold at useful levels
is called a null, not a hit. A bench the terrain flags is called a candidate to
walk, not a verdict. A claim check names which government it asked: the map
queries BLM's *federal* register, while the *state* register that actually
governs this ground — DNR's ME112 active and ME13 pending layers — is a separate
answer carried on each bench record with the date it was checked, because a
claim can be staked any day and an undated check is a rumour. Both say "verify
before acting — data lags reality," because they do. The honesty is the point:
it's a research and reasoning aid that respects that the ground makes the final
call, not the software.

---

## How the bench hunter actually helps (the part worth studying)

The idea it's built on: gold-bearing creeks move over time. Where the creek used
to run, it left gravel — and gold — stranded on flat shelves (benches) above the
current water. Old-timers made fortunes on bench deposits. They're easy to walk
past because they're up out of the creek, hidden in the trees, and look like
ordinary flat ground.

The bench hunter reads the valley's shape from elevation data and finds the flat
shelves that sit in the height band where old benches strand — **3 to 20 meters
above the current channel**, flat ground (under ~12% grade) set back from the
water. When a flat also has a distinct step dropping below it (a real terrace
edge, over ~20% grade), it flags that as a **strong** candidate.

So what it gives you is not "gold is here." It's: *of the whole reach, these
specific stretches have flat shelves at bench-height worth walking — go check
these instead of wandering the creek randomly.* Each flag tells you how far off
the creek to walk and how high to climb. That's the whole job: it turns miles of
river into a short list of walkable spots, and hands you off to your eyes and pan
to judge whether each one is a real bench (rounded creek gravel = old channel;
angular rock = just slope wash).

Think of it as a metal-detector for *terrain shape* — it beeps at the places
worth digging into, and you confirm on the ground.

One honest limit built in: Alaska's best public elevation data is 5m radar, which
is coarser than Lower-48 lidar. So a low bench can hide below what the data
resolves. "Clean valley" on the tool is not proof there's no bench — it means
nothing stood out at 5m. Trust the flags; don't trust the absence of flags.

---

## Non-obvious things worth knowing

**The tools launcher.** In Field Brain, the pin icon (top of the header, next to
the data icon) opens the map, bench hunter, and creek manual. That's how you move
between the four tools.

**Your data flows automatically — in one direction, on one device.** Logging a
site in Field Brain pushes it to the map. Running the bench hunter pushes its
candidates to the map. But this only works within one browser on one phone —
your data doesn't sync between your phone and laptop. Whatever browser you first
used holds your data. Different browser or device = separate, empty record.

**Export often — it's your only backup.** Your logged sites live in the browser,
not in the repo and not in the cloud. A browser "clear data," or iOS Safari
auto-clearing storage for sites you haven't opened in a week, will wipe them. Use
Field Brain's export to save a file somewhere you control. Treat the app's memory
as a working store, not a backup.

**Tap-to-place beats typing coordinates.** On the map, tap any spot → "Use this
spot in Field Brain" → it starts an evaluation there, no coordinates to type. A
tapped spot starts blank (no false score) because nothing's documented there yet;
a tapped *documented occurrence* pre-fills the "documented source" indicator,
because that one's earned.

**The map needs signal; the field tools don't.** The gold map's live layers
(ARDF, claims, geochem) fetch from USGS/BLM in real time, so do that research at
home with a connection. Evaluate, Sites, Knowledge, the bench hunter, and the
creek manual all work offline once the app is installed. The map itself still
opens offline and still draws your points and their land-status colours
correctly — Leaflet is vendored, not fetched — but the basemap tiles are a
network fetch, so they come up blank. Plan online, prospect offline.

**"Scan documented gold occurrences"** — the button that used to say "Find
PROVEN + OPEN ground". It plots ARDF gold occurrences in view and colours each
one by land status, the same as everything else on the map. **It does not find
open ground.**

It used to, and that was the bug. It drew green dots labelled "PROVEN + OPEN"
wherever a BLM claims query came back empty — but BLM's service holds *federal*
claims, and a federal claim can only exist on federal land. Hatcher Pass is
state land: GS 1222, state patent 50-87-0076. That register is nearly empty here
by construction — one polygon across the whole reach envelope, against 143 in a
same-size box near Fairbanks. The query worked. The zeros were real. They were
the wrong government's zeros, and an empty answer from the wrong authority
renders on a phone exactly like a clean answer from the right one. The green is
gone because it was never earned.

**The bench hunter needs its data file.** It runs on a `bench_data.json` from an
elevation pull of your reach. Load that file and it reads the whole reach; the
walk plan and candidates appear. No file, nothing to read.

**Satellite view for judging, streets for reading.** Flip to satellite to eyeball
whether a flagged bench looks like real flat terrace ground before you drive out.
Flip to streets/topo for clean reading of the river and your markers.

---

## Where to point it next (iterating the design)

The design is deliberately additive — each piece was built without breaking the
others, so it's safe to extend. Honest directions worth exploring:

**Better terrain than 5m radar.** The real ceiling on bench detection is the
elevation data. Drone photogrammetry over a specific reach would produce a far
finer terrain model than the public 5m IfSAR — enough to resolve low benches the
current data misses. That's the highest-value upgrade for the bench hunter, and
it's a hobby of its own.

**More data flows.** Photo analysis results could flow onto the map. Bench
candidates could auto-create evaluable sites. The shared-record foundation is
already there; these are small additions.

**Cross-device sync.** The biggest current limitation is that data lives on one
device. A real fix means a lightweight backend, which trades away the
simple-offline nature — worth it only if you start using it across phone and
laptop seriously.

**Field feedback loop.** The most valuable iteration is the cheapest: log what
you actually find (and don't find) at each spot. Over a season, your own logged
results become better ground-truth than any public dataset — and they'd let you
tune the favorability model to what actually pans out on your creeks.

**Sharper geochem reading.** The public geochem is 1980s data, often too
insensitive to detect gold. Sending your own panned concentrates to a modern lab
would give real pathfinder values for your specific spots — better signal than
the historical samples the map shows.

---

## The honest state of it

It works. It's deployed, installable, offline-capable with the basemap caveat
above, and it's been audited —
no secrets leaked, clean code, honest about its limits. It reads real government
data, reasons transparently, and gets you to specific walkable ground with honest
guidance about what only your boots and pan can confirm.

It won't find gold for you. But it'll make sure that when you go looking, you're
walking documented, land-status-checked, terrain-informed ground instead of
guessing — and that you learn the landscape a little better every time you use
it. Checked is not the same as open: the app tells you what was asked, of which
government, and when.

Go read a bench in person. That's what it's for.
