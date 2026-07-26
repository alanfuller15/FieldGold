#!/usr/bin/env python3
"""Adversarial test for map.html's site layer.

The bug being fixed: site markers were coloured by TERRAIN SCORE, using the
same green (#6FA760) that this map's own legend defines as "DNR-checked,
nothing found". A site scored 80 on landform grounds therefore rendered in the
colour reserved for verified-open ground, whether or not any land check had
ever been run near it. map.html was the last screen in the app that could show
a green marker sitting inside a mineral closing order.

The second bug: the legacy `fieldgold_sites` localStorage blob is written by an
older Field Brain, has never been through the shared layer's validation, and
was read straight into L.circleMarker and into popup HTML — unchecked
coordinates, unescaped names.

WHAT THIS TEST DOES AND DOES NOT PROVE.

Leaflet is now VENDORED at vendor/leaflet/ (change set 0005), so this suite
could load the real thing — and `tests/test_offline_map.py` does exactly that,
with the network cut, which is where that belongs. Here the real file is still
intercepted and replaced with a recording stub, on purpose. That means
this suite proves WHAT map.html asks Leaflet to draw — fill colours, popup
HTML, which records reach the map at all — and proves nothing about how
Leaflet then renders it. That is the right split: the defect was in the
choosing, not in the drawing.

One consequence to be honest about: the stub records popup HTML but never
attaches it to the document, so the `window.__pwned` assertion cannot fail even
with escaping removed — it passes under the `no-escape` mutant. The assertion
that actually carries weight there is the one checking `&lt;img` is present in
the popup string. `__pwned` is kept as a belt-and-braces check, not as evidence.

  python3 tests/test_map_sites.py
  python3 tests/test_map_sites.py --mutate score-colour   (prove it can fail)
"""
import functools
import http.server
import json
import pathlib
import shutil
import socketserver
import sys
import tempfile
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
MUTATE = sys.argv[sys.argv.index("--mutate") + 1] if "--mutate" in sys.argv else None

PASS = 0
FAILS = []


def check(name, cond, detail=""):
    global PASS
    if cond:
        PASS += 1
        print("  ok    " + name)
    else:
        FAILS.append(name)
        print("  FAIL  " + name + ("  -- " + str(detail)[:220] if detail else ""))


# A recording stub, not an emulation. Every constructor returns a chainable
# object; circleMarker and marker calls are pushed onto window.__drawn with the
# options and popup HTML they were given.
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
        return { getWest: function(){return -150;}, getSouth: function(){return 61;},
                 getEast: function(){return -149;}, getNorth: function(){return 62;},
                 toBBoxString: function(){return '-150,61,-149,62';} };
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
    tileLayer: null,  // assigned below so .wms can hang off it, as in real Leaflet

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

GREEN = "#6FA760"
RUST = "#B2402F"
AMBER = "#D29A3A"


def serve(directory):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(directory))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def main():
    root = ROOT
    if MUTATE:
        tmp = pathlib.Path(tempfile.mkdtemp()) / "repo"
        shutil.copytree(ROOT, tmp)
        root = tmp
        m0 = m = (root / "map.html").read_text(encoding="utf-8")
        if MUTATE == "score-colour":
            # Put the original bug back: colour the dot by terrain score.
            m = m.replace(
                "const col = ctx ? ctx.color : '#D29A3A';",
                "const col = (s.score>=72?'#6FA760':s.score>=50?'#D29A3A':'#C25A3A');")
        elif MUTATE == "no-context":
            # Ignore land status entirely and go back to one flat colour.
            m = m.replace(
                "const col = ctx ? ctx.color : '#D29A3A';",
                "const col = '#6FA760';")
        elif MUTATE == "no-sanitize":
            # Trust the legacy blob again.
            m = m.replace("const clean=sanitizeSites(raw);",
                          "const clean={sites:(raw||[]),bad:[]};")
        elif MUTATE == "no-escape":
            m = m.replace("function esc(v){", "function esc(v){ if(1) return String(v==null?'':v);")
        elif MUTATE == "unscoped-replacekind":
            # Put the site-record version of the bug that ate the REM benches
            # back into index.html: replaceKind with no `where` scope.
            i = (root / "index.html").read_text(encoding="utf-8")
            i2 = i.replace(
                "}), { where: function (e) { return e.source === 'fieldbrain'; } });",
                "}));")
            if i2 == i:
                print("mutant unscoped-replacekind did not match; refusing to "
                      "report a pass on an unmutated tree")
                sys.exit(2)
            (root / "index.html").write_text(i2, encoding="utf-8")
        elif MUTATE == "silent-drop":
            # Drop unusable records without saying so.
            m = m.replace("clean.bad.forEach(function(why){ log('site dropped — '+why,'warn'); });", "")
        else:
            print("unknown mutant: " + MUTATE)
            sys.exit(2)
        # A mutant whose replace() found nothing leaves the tree intact and the
        # suite then "passes" against unmutated code — which is worse than no
        # mutation testing at all, because it reads as evidence.
        if MUTATE != "unscoped-replacekind" and m == m0:
            print("mutant " + MUTATE + " did not match map.html; refusing to "
                  "report a pass on an unmutated tree")
            sys.exit(2)
        (root / "map.html").write_text(m, encoding="utf-8")

    httpd, port = serve(root)
    base = f"http://127.0.0.1:{port}"
    print("map site-layer suite  serving " + str(root) + "  on " + base
          + (f"  MUTANT={MUTATE}" if MUTATE else ""))

    # The two reference positions are read OUT OF THE LOADED DATA below, never
    # typed here. An earlier draft of this file hardcoded a coordinate for
    # REM-14 that was 4 km from the real one, which made the suite assert the
    # wrong thing while looking correct. Repo rule 3 applies to tests too.
    avoid = clean = None

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context()
        ctx.route("**/leaflet*.js", lambda route: route.fulfill(
            status=200, content_type="application/javascript", body=LEAFLET_STUB))
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # ------------------------------------------------------------------
        # Load the real bench land-status data first — contextForPoint has
        # nothing to say without it.
        # ------------------------------------------------------------------
        page.goto(base + "/load_rem_benches.html", wait_until="load")
        page.get_by_text("Load all 20 with status").click()
        counts = page.evaluate(
            "() => FieldGoldData.statusCounts(FieldGoldData.get('bench'))")
        check("bench data loaded: 8 clean / 0 unchecked / 12 avoid",
              (counts["clean"], counts["unchecked"], counts["avoid"]) == (8, 0, 12),
              json.dumps(counts))

        avoid = page.evaluate(
            "() => FieldGoldData.get('bench').find(b => b.profile === 'REM-14')")
        clean = page.evaluate(
            "() => FieldGoldData.get('bench').find(b => b.profile === 'REM-2')")
        check("reference positions came from the data, not from this file",
              bool(avoid) and bool(clean)
              and "MCO 549" in (avoid.get("status_label") or "")
              and clean.get("land_status") == "clean",
              json.dumps([avoid and avoid.get("status_label"),
                          clean and clean.get("land_status")]))

        # ------------------------------------------------------------------
        # 1. A high-scoring site sitting on encumbered ground.
        # ------------------------------------------------------------------
        legacy = {"updated": 1, "sites": [
            {"id": "s1", "name": "Sweet bench", "lat": avoid["lat"], "lon": avoid["lon"],
             "score": 88, "verdict": "Strong", "heightAboveStream": 4},
        ]}
        page.evaluate("([blob]) => localStorage.setItem('fieldgold_sites', JSON.stringify(blob))",
                      [legacy])
        page.goto(base + "/map.html", wait_until="load")
        page.wait_for_timeout(600)

        drawn = page.evaluate("() => window.__drawn.filter(d => d.type === 'circle')")
        site = [d for d in drawn if d["popup"] and "Your logged site" in d["popup"]]
        check("the site was drawn at all", len(site) == 1, len(site))
        fill = site[0]["opts"].get("fillColor") if site else None
        check("a score-88 site on encumbered ground is NOT green",
              fill != GREEN, fill)
        check("  ...it is rust", fill == RUST, fill)
        check("  ...and its popup says AVOID",
              site and "AVOID" in site[0]["popup"], (site[0]["popup"][:160] if site else ""))
        check("  ...and names the encumbrance",
              site and "MCO 549" in site[0]["popup"])
        check("the terrain score is still shown, as text",
              site and "88/100" in site[0]["popup"])
        check("  ...with the caveat that a score is not a legal status",
              site and "still encumbered ground" in site[0]["popup"])

        # The whole point, stated as one blunt assertion: nothing this page
        # draws for a logged site is ever the verified-open colour.
        allfills = [d["opts"].get("fillColor") for d in drawn if d["popup"]
                    and "Your logged site" in d["popup"]]
        check("NO site marker anywhere on the map is green", GREEN not in allfills, allfills)

        status = page.evaluate("() => document.getElementById('status').innerText")
        check("the status log flags sites on encumbered ground",
              "encumbered ground" in status, status[-200:])

        # ------------------------------------------------------------------
        # 2. A site near a CLEAN bench is amber, never green.
        # ------------------------------------------------------------------
        legacy2 = {"updated": 1, "sites": [
            {"id": "s2", "name": "By the clean one", "lat": clean["lat"] + 0.0009,
             "lon": clean["lon"], "score": 95, "verdict": "Strong"},
        ]}
        page.evaluate("([blob]) => localStorage.setItem('fieldgold_sites', JSON.stringify(blob))",
                      [legacy2])
        page.goto(base + "/map.html", wait_until="load")
        page.wait_for_timeout(600)
        s2 = [d for d in page.evaluate("() => window.__drawn.filter(d => d.type==='circle')")
              if d["popup"] and "Your logged site" in d["popup"]]
        check("100 m from a verified-clean bench, a 95-score site is amber",
              s2 and s2[0]["opts"].get("fillColor") == AMBER,
              s2[0]["opts"].get("fillColor") if s2 else None)
        check("  ...and the popup says NOT CHECKED HERE",
              s2 and "NOT CHECKED HERE" in s2[0]["popup"])
        # The word "clean" may appear, but only ever attached to the BENCH that
        # was checked — never to the position the user logged. That is the
        # whole honest-phrasing rule, so assert the exact sentence.
        check("  ...and 'clean' is attributed to the checked bench, not to this spot",
              s2 and "came back clean" in s2[0]["popup"],
              s2[0]["popup"][:200] if s2 else "")

        # ------------------------------------------------------------------
        # 3. Hostile / broken records out of the legacy blob.
        # ------------------------------------------------------------------
        legacy3 = {"updated": 1, "sites": [
            {"id": "g1", "name": "no coords"},
            {"id": "g2", "name": "string coords", "lat": "61.72", "lon": "-149.23"},
            {"id": "g3", "name": "off planet", "lat": 991, "lon": -149.23},
            None,
            "not a record",
            {"id": "g4", "name": "<img src=x onerror=window.__pwned=1>",
             "lat": avoid["lat"], "lon": avoid["lon"], "score": 70},
        ]}
        page.evaluate("([blob]) => localStorage.setItem('fieldgold_sites', JSON.stringify(blob))",
                      [legacy3])
        page.goto(base + "/map.html", wait_until="load")
        page.wait_for_timeout(600)
        s3 = [d for d in page.evaluate("() => window.__drawn.filter(d => d.type==='circle')")
              if d["popup"] and "Your logged site" in d["popup"]]
        check("only the one placeable record is drawn", len(s3) == 1, len(s3))
        status3 = page.evaluate("() => document.getElementById('status').innerText")
        check("every dropped record is REPORTED, not silently skipped",
              status3.count("site dropped") == 5, status3.count("site dropped"))
        check("the report names what was wrong", "no usable coordinates" in status3)
        check("a hostile site name does not execute",
              page.evaluate("() => window.__pwned") is None)
        check("  ...it is escaped into the popup instead",
              s3 and "&lt;img" in s3[0]["popup"], s3[0]["popup"][:160] if s3 else "")
        check("no uncaught page errors from the junk", not errors, errors[:2])

        # ------------------------------------------------------------------
        # 4. The shared record wins over the legacy blob.
        # ------------------------------------------------------------------
        page.goto(base + "/map.html", wait_until="load")
        page.evaluate(
            """([a]) => {
                 FieldGoldData.put({kind:'site', id:'shared1', lat:a.lat, lon:a.lon,
                                    source:'fieldbrain', name:'From the shared layer', score:50});
                 localStorage.setItem('fieldgold_sites', JSON.stringify(
                   {updated:1, sites:[{id:'legacy1', name:'From the legacy blob',
                                       lat:a.lat, lon:a.lon, score:99}]}));
               }""", [clean])
        page.goto(base + "/map.html", wait_until="load")
        page.wait_for_timeout(600)
        pops = [d["popup"] for d in page.evaluate("() => window.__drawn.filter(d=>d.type==='circle')")
                if d["popup"] and "Your logged site" in d["popup"]]
        check("the shared record is used when it has sites",
              any("From the shared layer" in p for p in pops), pops[:1])
        check("  ...and the unvalidated legacy blob is not also drawn",
              not any("From the legacy blob" in p for p in pops))
        status4 = page.evaluate("() => document.getElementById('status').innerText")
        check("the status log says which source it used",
              "from the shared record" in status4, status4[-160:])

        # ------------------------------------------------------------------
        # 5. No bench data on the device at all.
        #
        # localStorage.clear() no longer produces this state: fieldgold-data.js
        # auto-seeds the 20 REM benches on load, so a wiped device comes back
        # WITH land status. That is the seeder working as intended, and it makes
        # the empty case rarer — not impossible. The way to reach it is the way a
        # user reaches it: delete the bench records after the seed has already
        # run once. The seeder deliberately will not resurrect them, because a
        # record you deleted coming back on the next page load is worse than an
        # empty layer. So the branch is still live, and it still has to say in
        # words that amber means "nothing to check against" rather than
        # "checked and unclear".
        # ------------------------------------------------------------------
        page.evaluate("() => localStorage.clear()")
        page.goto(base + "/map.html", wait_until="load")
        page.wait_for_timeout(300)
        seeded = page.evaluate("() => FieldGoldData.get('bench').length")
        check("a wiped device auto-seeds bench records (so section 5 must "
              "delete them, not just clear)", seeded == 20, seeded)
        page.evaluate("""() => {
          const rec = JSON.parse(localStorage.getItem(FieldGoldData.KEY));
          rec.entries = rec.entries.filter(e => e.kind !== 'bench');
          localStorage.setItem(FieldGoldData.KEY, JSON.stringify(rec));
        }""")
        page.evaluate("([a]) => localStorage.setItem('fieldgold_sites', JSON.stringify("
                      "{updated:1, sites:[{id:'x', name:'Alone', lat:a.lat, lon:a.lon, score:90}]}))",
                      [avoid])
        page.goto(base + "/map.html", wait_until="load")
        page.wait_for_timeout(300)
        check("  ...and the seeder does not resurrect deleted benches",
              page.evaluate("() => FieldGoldData.get('bench').length") == 0,
              page.evaluate("() => FieldGoldData.get('bench').length"))
        page.wait_for_timeout(600)
        s5 = [d for d in page.evaluate("() => window.__drawn.filter(d=>d.type==='circle')")
              if d["popup"] and "Your logged site" in d["popup"]]
        check("with no bench data the site is still not green",
              s5 and s5[0]["opts"].get("fillColor") != GREEN,
              s5[0]["opts"].get("fillColor") if s5 else None)
        status5 = page.evaluate("() => document.getElementById('status').innerText")
        check("with no bench data the map says the colours mean unknown",
              "no land-status data on this device" in status5, status5[-200:])

        # ------------------------------------------------------------------
        # 6. syncSitesToMap must not clear site records it does not own.
        # ------------------------------------------------------------------
        page.goto(base + "/index.html", wait_until="load")
        page.wait_for_timeout(400)
        survived = page.evaluate(
            """() => {
                 FieldGoldData.put({kind:'site', id:'other-tool-1', lat:61.72, lon:-149.23,
                                    source:'some-other-tool', name:'Not Field Brain\\'s'});
                 S.sites = [{id:'fb1', name:'Mine', score:0.8,
                             gps:{lat:61.73, lon:-149.24, heightAboveStream:3}}];
                 syncSitesToMap();
                 return FieldGoldData.get('site').map(e => e.id);
               }""")
        check("syncSitesToMap keeps another tool's site records",
              "other-tool-1" in survived, survived)
        check("  ...and still writes its own", "fb1" in survived, survived)
        twice = page.evaluate("() => { syncSitesToMap(); syncSitesToMap();"
                              " return FieldGoldData.get('site').map(e => e.id); }")
        check("  ...and running it repeatedly does not duplicate or accumulate",
              sorted(twice) == sorted(survived), twice)

        check("no uncaught page errors anywhere in the run", not errors, errors[:2])
        browser.close()

    httpd.shutdown()
    print("")
    print(f"{PASS} passed, {len(FAILS)} failed")
    if FAILS:
        print("FAILED: " + ", ".join(FAILS))
        sys.exit(1)
    print("MAP SITE-LAYER SUITE PASSED")


if __name__ == "__main__":
    main()
