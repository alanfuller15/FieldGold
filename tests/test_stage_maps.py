#!/usr/bin/env python3
"""Adversarial test for the false-green claims bug, on map.html and on the five
archived stage maps.

THE BUG.

`map.html`'s legend says, in these words: green = DNR-checked, nothing found.
The `⛏ Find PROVEN + OPEN ground` button drew a green #6FA760 circle on every
ARDF gold occurrence that BLM's **BLM_AK_Federal_Mining_Claims** service came
back empty on, captioned "PROVEN + OPEN candidate". A federal mining claim can
only exist on federal land. This reach is state land — GS 1222, state patent
50-87-0076 — and every encumbrance the project has found here (MCO 549, LLO 5,
ADL 229824) is a state instrument recorded in DNR's ME112/ME13, which that
service does not hold and never has.

Measured, not assumed: the federal layer returns ONE polygon across the whole
reach envelope and none over the four upper benches, against 143 in a same-size
box near Fairbanks. The query works. The zeros are real. They are the wrong
government's zeros. An empty answer from the wrong authority renders on a phone
exactly like a clean answer from the right one.

The same block, byte-identical, lived in stage4_map.html and stage5_map.html,
and the layer labelled "Mining claims — DON'T dig here" in stage3/4/5 was that
same federal service — blank across the reach, with nothing on screen naming
which register was asked.

WHAT THIS SUITE PROVES, AND WHAT IT DOES NOT.

Sections 1-4 are static: they read the files off disk and assert on their text.
That is weak evidence in general, but it is the right instrument for the two
things that are genuinely textual — the archive banners and the sw.js SHELL
decision — because neither has any runtime behaviour to observe.

Section 5 is the one that carries the weight. It loads the real map.html with
real bench land-status data in localStorage, serves a canned ARDF response and
a canned BLM identify response returning **zero results** — the exact input
that used to produce green — clicks the scan button, and reads back what the
map asked Leaflet to draw. Leaflet itself is a recording stub, so this proves
what the page CHOOSES to draw and nothing about how it renders. The defect was
in the choosing.

One honest limit: nothing here checks the live BLM service. The 1-vs-143
measurement is recorded in the research log, not re-run at test time; the app
must not depend on a network to be tested.

  python3 tests/test_stage_maps.py
  python3 tests/test_stage_maps.py --mutate green-open   (prove it can fail)

mutants: green-open, drop-warning, no-banner, stage-green, claims-label,
         shell-stages, stale-cache
"""
import functools
import http.server
import pathlib
import re
import shutil
import socketserver
import sys
import tempfile
import threading

from playwright.sync_api import sync_playwright

REPO = pathlib.Path(__file__).resolve().parent.parent
# Web root. The app lives under docs/ so that webDir can point at a directory
# containing only web assets — tests/ and tools/ must never ship in the bundle.
ROOT = REPO / "docs"
MUTATE = sys.argv[sys.argv.index("--mutate") + 1] if "--mutate" in sys.argv else None

PASS = 0
FAILS = []

GREEN = "#6FA760"
GREEN_RGB = "rgb(111, 167, 96)"
RUST = "#B2402F"
AMBER = "#D29A3A"

# Read off disk, never typed twice. A hardcoded list of stage maps is the
# defect species this project has now hit four times: the list drifts, the
# check keeps passing, and the file nobody listed keeps its bug.
STAGES = sorted(p.name for p in ROOT.glob("stage*_map*.html"))
ALL_MAPS = STAGES + ["map.html"]


def check(name, cond, detail=""):
    global PASS
    if cond:
        PASS += 1
        print("  ok    " + name)
    else:
        FAILS.append(name)
        print("  FAIL  " + name + ("  -- " + str(detail)[:220] if detail else ""))


# A recording stub, not an emulation — same one test_map_sites.py uses, and for
# the same reason. Every constructor returns a chainable object; circleMarker
# and marker calls are pushed onto window.__drawn with the options and popup
# HTML they were given.
LEAFLET_STUB = r"""
window.__drawn = [];
(function () {
  function chain(rec) {
    var o = {
      addTo: function () { return o; },
      bindPopup: function (h) { if (rec) rec.popup = h; return o; },
      openPopup: function () { return o; },
      setLatLng: function () { return o; },
      setContent: function (h) { if (rec) rec.popup = h; return o; },
      openOn: function () { return o; },
      clearLayers: function () {
        window.__drawn = window.__drawn.filter(function (d) { return d.group !== o.__gid; });
        return o;
      },
      addLayer: function () { return o; },
      removeLayer: function () { return o; },
      bringToFront: function () { return o; },
      on: function () { return o; },
      off: function () { return o; },
      remove: function () { return o; },
      getBounds: function () {
        return { getWest: function(){return -149.30;}, getSouth: function(){return 61.68;},
                 getEast: function(){return -149.15;}, getNorth: function(){return 61.79;},
                 toBBoxString: function(){return '-149.30,61.68,-149.15,61.79';} };
      },
      getSize: function () { return { x: 800, y: 600 }; },
      getContainer: function () { return document.createElement('div'); },
      getPane: function () { return document.createElement('div'); },
      getZoom: function () { return 12; },
      latLngToContainerPoint: function () { return { x: 400, y: 300 }; },
      setView: function () { return o; },
      invalidateSize: function () { return o; },
      extend: function () { return function () { return chain(null); }; }
    };
    return o;
  }
  var gid = 0;
  var L = {
    map: function () { return chain(null); },
    tileLayer: null,
    layerGroup: function () { var g = chain(null); g.__gid = ++gid; g.__isGroup = true; return g; },
    popup: function () { return chain(null); },
    divIcon: function (o) { return o; },
    circleMarker: function (ll, opts) {
      var rec = { type: 'circle', latlng: ll, opts: opts || {}, popup: null };
      window.__drawn.push(rec);
      var c = chain(rec);
      c.addTo = function (g) { rec.group = g && g.__gid; return c; };
      return c;
    },
    marker: function (ll, opts) {
      var rec = { type: 'marker', latlng: ll, opts: opts || {}, popup: null };
      window.__drawn.push(rec);
      var c = chain(rec);
      c.addTo = function (g) { rec.group = g && g.__gid; return c; };
      return c;
    },
    control: { zoom: function () { return chain(null); }, layers: function () { return chain(null); } },
    CRS: { EPSG3857: { project: function () { return { x: 0, y: 0 }; } } },
    Util: { setOptions: function () {} }
  };
  L.tileLayer = function () { return chain(null); };
  L.tileLayer.wms = function () { return chain(null); };
  L.TileLayer = function () { return chain(null); };
  L.TileLayer.extend = function (proto) {
    var F = function () { return chain(null); };
    F.prototype = proto || {};
    return F;
  };
  L.Class = { extend: L.TileLayer.extend };
  window.L = L;
})();
"""


def ardf_gml(points):
    """Canned USGS ARDF WFS 1.1.0 response, in the shape map.html parses.

    The parser is a regex over <ms:ardf> blocks and filters on /Au/ in
    ms:comm_main. Anything that does not match that filter is not the input
    the bug needed, so the fixture mirrors it exactly.
    """
    recs = "".join(
        "<ms:ardf><ms:site>%s</ms:site><ms:comm_main>%s</ms:comm_main>"
        "<ms:latitude>%.6f</ms:latitude><ms:longitude>%.6f</ms:longitude></ms:ardf>"
        % (name, comm, lat, lon) for name, comm, lat, lon in points)
    return ('<?xml version="1.0" encoding="ISO-8859-1"?>'
            '<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs" '
            'xmlns:ms="http://mapserver.gis.umn.edu/mapserver">'
            + recs + "</wfs:FeatureCollection>")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(directory):
    handler = functools.partial(Quiet, directory=str(directory))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def edit(root, fname, old, new, count=1):
    """Apply a mutation, or abort.

    A mutant whose replace() matches nothing leaves the tree intact and the
    suite then "passes" against unmutated code — which is worse than no
    mutation testing at all, because it reads as evidence. Every mutation
    below asserts its occurrence count and exits 2 on a mismatch.
    """
    p = root / fname
    s = p.read_text(encoding="utf-8")
    n = s.count(old)
    if n != count:
        print("mutant %s: expected %d occurrence(s) of %r in %s, found %d — "
              "refusing to report a pass on an unmutated tree"
              % (MUTATE, count, old[:60], fname, n))
        sys.exit(2)
    p.write_text(s.replace(old, new), encoding="utf-8")


def apply_mutant(root):
    if MUTATE == "green-open":
        # Put the original bug back on map.html: colour the occurrence by the
        # FEDERAL claim answer, green when it comes back empty.
        edit(root, "map.html",
             "const col=ctx?ctx.color:'#D29A3A', ink=ctx?(ctx.ink||'#14110C'):'#14110C';\n"
             "      if(ctx&&ctx.advice===false) rust++;\n"
             "      const fed=await federalClaimAt(lng,lat);",
             "const ink='#14110C';\n"
             "      if(ctx&&ctx.advice===false) rust++;\n"
             "      const fed=await federalClaimAt(lng,lat);\n"
             "      const col=(fed===false?'#6FA760':'#D29A3A');")
    elif MUTATE == "drop-warning":
        # Keep the colour fix but drop the sentence that says what a federal
        # zero does not mean. The colour is the control; the sentence is the
        # explanation. Losing either should fail.
        edit(root, "map.html",
             "    log('\"none returned\" is NOT open ground: this reach is state land "
             "and state claims are not in that register','warn');\n", "")
    elif MUTATE == "no-banner":
        # Strip the archive banner from one stage map. One is enough: the
        # assertion is over every file the glob finds, not over a list.
        edit(root, STAGES[0], "ARCHIVED BUILD STAGE", "Field map")
    elif MUTATE == "stage-green":
        edit(root, "stage4_map.html",
             "L.circleMarker([lat,lng],{radius:9,color:'#D29A3A',weight:3,"
             "fillColor:'#D29A3A',fillOpacity:.35})",
             "L.circleMarker([lat,lng],{radius:9,color:'#6FA760',weight:3,"
             "fillColor:'#6FA760',fillOpacity:.35})")
    elif MUTATE == "claims-label":
        edit(root, "stage3_map.html",
             '</span>BLM <b style="color:#E8C04A;">FEDERAL</b> claims only</label>',
             "</span>Mining claims — DON'T dig here</label>")
    elif MUTATE == "claims-sr":
        # A transposition, which is what a typo actually looks like. The
        # service ACCEPTS this request: HTTP 200, image/png, 886 bytes,
        # md5 7be830c6…, byte-identical to a correct empty answer. Nothing at
        # runtime can catch it, which is why the static check exists.
        edit(root, "map.html", "bboxSR:'3857'", "bboxSR:'3758'")
    elif MUTATE == "claims-layer":
        # Capital O for a zero. Same response as above: a valid, transparent,
        # permanently blank PNG.
        edit(root, "map.html", "layers:'show:0'", "layers:'show:O'")
    elif MUTATE == "shell-stages":
        # The "helpful" future change: cache the stage maps for offline use.
        # They draw nothing without a network, so this produces a page that
        # looks like FieldGold and shows blank ground.
        edit(root, "sw.js", "  './map.html',",
             "  './map.html',\n  './stage1_map_test.html',\n  './stage5_map.html',")
    elif MUTATE == "stale-cache":
        # Read the CURRENT version out of the file rather than naming it. This
        # mutant named 'fieldgold-v8' literally and began aborting the moment
        # 0007 bumped the cache to v9 — a mutation test that cannot run is a
        # mutation test that cannot fail, which is the thing this project keeps
        # promising itself it will stop shipping. Seventh sighting of the
        # hardcoded-value species; the abort discipline is what surfaced it.
        cur = re.search(r"const CACHE = 'fieldgold-v(\d+)';",
                        (root / "sw.js").read_text(encoding="utf-8"))
        if not cur:
            print("mutant %s: no readable cache version in sw.js" % MUTATE)
            sys.exit(2)
        # v3, not v7. EIGHTH SIGHTING, and this one is subtler than the seven
        # before it: the mutant applied cleanly, exited 0, and was DEAD.
        #
        # It was written when the assertion below pinned a literal version, so
        # rewriting v9 to v7 tripped it. When that assertion was generalised to
        # `int(version) > PUBLISHED` with PUBLISHED = 3 — the right fix, for the
        # right reason — v7 quietly stopped violating anything, because 7 > 3.
        # The mutation still ran, still reported, still exited 0, and proved
        # nothing. No abort fired, because nothing failed to match. The abort
        # discipline catches a mutant that cannot be APPLIED; it cannot catch a
        # mutant that applies and does not MATTER. Only running the mutants and
        # reading rc=0 as "survived" rather than "passed" catches this one.
        #
        # v3 is the version actually sitting in the phone's cache, so it is both
        # what "stale cache" means and the one value that violates the claim.
        edit(root, "sw.js", "const CACHE = 'fieldgold-v%s';" % cur.group(1),
             "const CACHE = 'fieldgold-v3';")
    else:
        print("unknown mutant: " + str(MUTATE))
        sys.exit(2)


def main():
    root = ROOT
    if MUTATE:
        tmp = pathlib.Path(tempfile.mkdtemp()) / "repo"
        shutil.copytree(ROOT, tmp)
        root = tmp
        apply_mutant(root)

    print("stage-map / false-green suite  " + str(root)
          + ("  MUTANT=" + MUTATE if MUTATE else ""))
    check("the stage-map list was discovered, not hardcoded",
          len(STAGES) == 5, STAGES)

    txt = {f: (root / f).read_text(encoding="utf-8") for f in ALL_MAPS}
    sw = (root / "sw.js").read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # 1. No page draws a green marker, anywhere, for any reason.
    # ------------------------------------------------------------------
    print("\n1. green is reserved for DNR-checked ground")
    for f in ALL_MAPS:
        bad = [ln for ln in txt[f].splitlines()
               if GREEN in ln and "circleMarker" in ln]
        check("  %s has no green circleMarker" % f, not bad, bad[:1])
    for f in ALL_MAPS:
        # The remaining occurrences of the colour are the .ok status-log ink and
        # explanatory comments. Assert that, rather than banning the string and
        # forcing a future author to work around the test.
        live = [ln.strip() for ln in txt[f].splitlines()
                if GREEN in ln and not ln.strip().startswith("//")
                and ".ok" not in ln and "color:#6FA760" not in ln]
        check("  %s: surviving %s is log ink or comment only" % (f, GREEN),
              not live, live[:1])

    print("\n2. no page still promises OPEN ground")
    for f in ALL_MAPS:
        # The phrase may still appear on screen, but only in the past tense,
        # describing what this button used to do. That disclosure is worth
        # keeping — a person who remembers the green dots deserves to be told
        # where they went. What must not survive is the phrase used as a
        # PROMISE: a button label, a caption, a popup heading.
        vis = [ln.strip() for ln in txt[f].splitlines()
               if "PROVEN + OPEN" in ln and not ln.strip().startswith("//")
               and "used to" not in ln]
        check("  %s: 'PROVEN + OPEN' survives only as history or comment" % f,
              not vis, vis[:1])
        check("  %s: no button offers to find it" % f,
              "Find PROVEN + OPEN ground</button>" not in txt[f])
        vis2 = [ln.strip() for ln in txt[f].splitlines()
                if "isClaimed" in ln and not ln.strip().startswith("//")]
        check("  %s: isClaimed() is gone (renamed federalClaimAt)" % f, not vis2, vis2[:1])

    # ------------------------------------------------------------------
    # 3. The stage maps say what they are, on screen, above the fold.
    # ------------------------------------------------------------------
    print("\n3. the stage maps are labelled as archived")
    for f in STAGES:
        check("  %s carries the ARCHIVED BUILD STAGE banner" % f,
              "ARCHIVED BUILD STAGE" in txt[f])
        check("  %s says it has no land-status layer" % f,
              "no land-status layer" in txt[f])
        check("  %s points at map.html" % f,
              'href="map.html"' in txt[f])
        # The banner must be inside the panel and before the heading, or it is
        # a footnote on a page that already looks like the app.
        i_ban = txt[f].find("ARCHIVED BUILD STAGE")
        i_head = txt[f].find("FieldGold")
        i_body = txt[f].find("<body")
        check("  %s: the banner is in the body, not the <head>" % f,
              i_ban > i_body > 0, (i_body, i_ban))
        check("  %s does not reference the shared data layer" % f,
              "fieldgold-data.js" not in txt[f],
              "a stage map loading the shared layer would be a field tool again")

    titles = {}
    for f in ALL_MAPS:
        a = txt[f].find("<title>")
        titles[f] = txt[f][a + 7:txt[f].find("</title>", a)]
    check("  every map page has a distinct title",
          len(set(titles.values())) == len(titles), titles)
    check("  map.html is not still titled 'Stage 3'",
          "Stage 3" not in titles["map.html"], titles["map.html"])
    for f in STAGES:
        check("  %s title says archived" % f,
              "archived" in titles[f].lower(), titles[f])

    # ------------------------------------------------------------------
    # 4. The claims layer names its register.
    # ------------------------------------------------------------------
    print("\n4. the claims layer names which government it asked")
    for f in ALL_MAPS:
        if "BLM_AK_Federal_Mining_Claims" not in txt[f]:
            continue
        check("  %s: the label no longer reads 'Mining claims — DON'T dig here'" % f,
              "Mining claims — DON'T dig here" not in txt[f])
        check("  %s: the label says FEDERAL" % f,
              "FEDERAL</b> claims only" in txt[f])
        check("  %s: the note says blank is not 'no claims'" % f,
              ('not the same as "no claims."' in txt[f]
               or 'does not mean\n' in txt[f] or '"no claims."' in txt[f]))
        check("  %s: the note says the reach is state land" % f,
              "state</b>" in txt[f] and "Alaska DNR" in txt[f])
        check("  %s: the note carries the measurement" % f,
              "143" in txt[f] and "1 federal polygon" in txt[f])

        # THE REQUEST PARAMETERS ARE ASSERTED LITERALLY, AND THIS IS NOT
        # OVER-SPECIFICATION. Do not delete it as pedantry.
        #
        # Measured against the live BLM service 2026-07-29, seven requests,
        # recorded in STATE.md: a typo in these values DOES NOT FAIL. The
        # ArcGIS `export?` endpoint answers HTTP 200, content-type image/png,
        # 886 bytes, md5 7be830c61ed940eb68430ae9628af377 — which is
        # BYTE-IDENTICAL to a correct empty answer over Hatcher Pass. Both
        # bboxSR=99999 and layers=show:99 return exactly that. Not similar to
        # the right answer: the same object.
        #
        # So a wrong value here produces a claims layer that is blank forever,
        # that Leaflet reports as a successful tile load, and that no other
        # assertion in this repo can see. It would be silent and permanent, on
        # the ONE layer whose entire on-screen treatment exists to stop a blank
        # being over-read — the FEDERAL label, the "not the same as no claims"
        # note, the 1-vs-143 measurement, and the isClaimed() ->
        # federalClaimAt() rename that section 2 above defends.
        #
        # Unlike the WMS layers, this one has no honest failure channel: they
        # send no EXCEPTIONS parameter, so the WMS default of XML makes a
        # server-side rejection non-image and the tile load fails visibly. The
        # export endpoint returns a valid PNG either way. This static check is
        # the only tripwire available, and it needs no network.
        flat = re.sub(r"\s+", " ", txt[f])
        check("  %s: the claims URL carries the exact parameter tuple" % f,
              ("bboxSR:'3857', imageSR:'3857', size:'256,256', "
               "format:'png32', transparent:'true', f:'image', "
               "layers:'show:0'") in flat,
              flat[flat.find("bboxSR"):][:140] if "bboxSR" in flat else "no bboxSR at all")
        # Every occurrence, not merely one, so a second divergent copy of the
        # URL cannot hide behind a correct first one.
        check("  %s: every bboxSR is 3857" % f,
              len(re.findall(r"bboxSR:'", txt[f]))
              == len(re.findall(r"bboxSR:'3857'", txt[f])),
              re.findall(r"bboxSR:'[^']*'", txt[f]))
        check("  %s: every imageSR is 3857" % f,
              len(re.findall(r"imageSR:'", txt[f]))
              == len(re.findall(r"imageSR:'3857'", txt[f])),
              re.findall(r"imageSR:'[^']*'", txt[f]))

    # ------------------------------------------------------------------
    # 5. sw.js — the version bump, and the SHELL exclusion as a DECISION.
    # ------------------------------------------------------------------
    print("\n5. the service worker")
    # The requirement is that the shipped cache is PAST the one on the device —
    # not that it is any particular number. This check has now been wrong twice
    # in the same way: pinned at 'v8' it went red when a later change legitimately
    # shipped v9, and pinned at '>= 8' it went red again when seven change sets
    # were collapsed into a single publication numbered v4. Both times it failed
    # for the one reason a regression test must never fail: the app moved on.
    # PUBLISHED is the version actually sitting in the phone's cache, and the
    # only thing that has to be true is that the new one is greater — that is
    # literally the condition the activate handler tests.
    PUBLISHED = 3
    cache_v = re.search(r"const CACHE = 'fieldgold-v(\d+)';", sw)
    check("  the cache version is readable at all",
          bool(cache_v), sw[sw.find("const CACHE"):][:48])
    check("  cache version is past the v%d already on the device" % PUBLISHED,
          bool(cache_v) and int(cache_v.group(1)) > PUBLISHED,
          cache_v and cache_v.group(0))
    shell = sw[sw.find("const SHELL"):sw.find("];", sw.find("const SHELL"))]
    for f in STAGES:
        check("  %s is NOT in SHELL" % f, f not in shell,
              "caching a page that draws only network data yields a FieldGold-"
              "looking page showing nothing")
    check("  the exclusion is written down as a decision, not left as an omission",
          "decision rather" in sw and "network" in sw)
    check("  map.html IS in SHELL", "./map.html" in shell)

    # ------------------------------------------------------------------
    # 6. THE BEHAVIOURAL TEST. Federal query returns zero — the exact input
    #    that used to render green — with real bench data loaded.
    # ------------------------------------------------------------------
    print("\n6. behaviour: a federal claims query returning ZERO results")
    httpd, port = serve(root)
    base = "http://127.0.0.1:%d" % port
    fed_calls = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context()
        ctx.route("**/leaflet*.js", lambda route: route.fulfill(
            status=200, content_type="application/javascript", body=LEAFLET_STUB))
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        page.goto(base + "/load_rem_benches.html", wait_until="load")
        page.get_by_text("Load all 20 with status").click()
        avoid = page.evaluate(
            "() => FieldGoldData.get('bench').find(b => b.profile === 'REM-14')")
        clean = page.evaluate(
            "() => FieldGoldData.get('bench').find(b => b.profile === 'REM-2')")
        # Coordinates come out of the loaded data. Repo rule 3 applies to tests.
        check("  reference positions came from the data, not from this file",
              bool(avoid) and bool(clean)
              and "MCO 549" in (avoid.get("status_label") or "")
              and clean.get("land_status") == "clean")

        fixture = ardf_gml([
            ("On the closed one", "Au, Ag", avoid["lat"], avoid["lon"]),
            ("Near the clean one", "Au", clean["lat"] + 0.0009, clean["lon"]),
        ])

        def ardf(route):
            route.fulfill(status=200, content_type="text/xml", body=fixture)

        def blm(route):
            # ZERO results. On state ground this is what the federal register
            # actually returns, and it is what used to be painted green.
            fed_calls.append(route.request.url)
            route.fulfill(status=200, content_type="application/json",
                          body='{"results":[]}')

        ctx.route("**/wfs/ardf*", ardf)
        ctx.route("**/BLM_AK_Federal_Mining_Claims/**", blm)

        page.goto(base + "/map.html", wait_until="load")
        page.wait_for_timeout(500)
        page.click("#findopen")
        page.wait_for_timeout(1500)

        occ = [d for d in page.evaluate("() => window.__drawn.filter(d=>d.type==='circle')")
               if d["popup"] and "Documented gold occurrence" in d["popup"]]
        check("  both gold occurrences were drawn", len(occ) == 2, len(occ))
        check("  the federal service was actually queried",
              len(fed_calls) == 2, len(fed_calls))

        fills = [d["opts"].get("fillColor") for d in occ]
        check("  NO occurrence is green, on a zero federal answer",
              GREEN not in fills and GREEN_RGB not in fills, fills)
        check("  the one on MCO 549 ground is rust", RUST in fills, fills)
        check("  the other is amber, never clean", AMBER in fills, fills)

        pops = " ".join(d["popup"] for d in occ)
        check("  no popup uses the word OPEN", "OPEN" not in pops)
        check("  the popup names the register as FEDERAL",
              pops.count("<b>federal</b> claim returned here") == 2)
        check("  ...and says an empty federal answer means nothing here",
              pops.count("this reach is state land") == 2)
        # Per-popup, not a total count: the avoid tier's own detail string also
        # names Alaska Mapper, so a total would pass with one popup carrying
        # two mentions and the other carrying none.
        check("  ...and EVERY popup sends the reader to Alaska Mapper",
              all("Alaska Mapper, not on this map" in d["popup"] for d in occ),
              [d["popup"][-160:] for d in occ][:1])
        check("  the encumbrance is named on the rust one", "MCO 549" in pops)

        status = page.evaluate("() => document.getElementById('status').innerText")
        check("  the log says a federal zero is not open ground",
              "NOT open ground" in status, status[-240:])
        check("  the log reports the federal counts separately",
              "federal register only" in status, status[-240:])
        check("  no uncaught page errors", not errors, errors[:2])

        # --------------------------------------------------------------
        # 7. The shared data layer fails to load. The fallback must be
        #    amber-and-say-so, not a silent default.
        # --------------------------------------------------------------
        print("\n7. behaviour: fieldgold-data.js does not load")
        ctx.route("**/fieldgold-data.js", lambda r: r.fulfill(
            status=200, content_type="application/javascript", body="/* gone */"))
        page.goto(base + "/map.html", wait_until="load")
        page.wait_for_timeout(400)
        page.click("#findopen")
        page.wait_for_timeout(1500)
        occ2 = [d for d in page.evaluate("() => window.__drawn.filter(d=>d.type==='circle')")
                if d["popup"] and "Documented gold occurrence" in d["popup"]]
        check("  occurrences still draw with no shared layer", len(occ2) == 2, len(occ2))
        check("  ...all amber, none green",
              all(d["opts"].get("fillColor") == AMBER for d in occ2),
              [d["opts"].get("fillColor") for d in occ2])
        check("  ...and each popup SAYS the status is unknown and why",
              all("Land status unknown" in d["popup"] for d in occ2))

        browser.close()

    httpd.shutdown()
    print("")
    print("%d passed, %d failed" % (PASS, len(FAILS)))
    if FAILS:
        print("FAILED: " + ", ".join(FAILS))
        sys.exit(1)
    print("STAGE-MAP / FALSE-GREEN SUITE PASSED")


if __name__ == "__main__":
    main()
