#!/usr/bin/env python3
"""The reactive layer and the seed migration, exercised in a real browser.

WHY THIS FILE EXISTS.

`fieldgold-data.js` carries a comment saying its event listeners "are exercised
for real in the browser by tests/test_reactive_refresh.py". For a while that
sentence named a file that did not exist. A comment citing a test that was never
written is worse than no comment: it is an assurance the reader cannot check and
has no reason to doubt. This file makes the sentence true.

WHAT IS ACTUALLY AT RISK.

Two things, and neither is cosmetic.

1. THE REFRESH. Bench records get their land status from a tool on another
   screen — load_rem_benches.html, bench_hunter.html, an import. Before the
   reactive layer, a bench that moved from NOT CHECKED to AVOID in one tab kept
   drawing amber in the other until somebody happened to reload. Amber reads as
   "nobody has looked yet". Rust reads as "do not work this ground". The gap
   between them is the whole point of the land-status work, and a stale screen
   sits on the wrong side of it.

2. THE DOUBLE DRAW. `pageshow` fires on ordinary page loads as well as on
   back/forward-cache restores. Firing on both means every page redraws
   immediately after its first draw. Markers survive that — they are cleared and
   rebuilt — but the status log APPENDS, so "site dropped — no usable
   coordinates" printed once per bad record becomes twice per bad record, and a
   reader counting lines cannot tell five malformed sites from ten. The listener
   is guarded on `e.persisted`; section 2 is what keeps it guarded.

3. THE SEED MIGRATION. v1 of the seeder already wrote 20 statusless benches onto
   a device. Bumping to v2 with an upgrade path is what gets land status onto
   records that are already there — and NOT resurrecting records the user
   deleted is what keeps the upgrade from being an unwanted restore. Section 4
   drives all four paths.

WHAT THIS SUITE DOES NOT PROVE. Leaflet is stubbed on map.html, so nothing here
says a marker was rendered — only that the page chose to draw it, and chose
again when the record changed. Cross-tab firing is driven by dispatching a
`storage` event, because two real tabs cannot be synchronised reliably enough to
assert on; that tests the handler, not the browser's delivery of the event.

    python3 tests/test_reactive_refresh.py
    python3 tests/test_reactive_refresh.py --mutate no-notify

mutants: no-notify, pageshow-unguarded, seed-flag-v1, seed-no-upgrade,
         seed-resurrects, listener-throws-kills-rest
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

REPO = pathlib.Path(__file__).resolve().parent.parent
# Web root. The app lives under docs/ so that webDir can point at a directory
# containing only web assets — tests/ and tools/ must never ship in the bundle.
ROOT = REPO / "docs"
MUTATE = sys.argv[sys.argv.index("--mutate") + 1] if "--mutate" in sys.argv else None

PASS = 0
FAILS = []

RUST = "#B2402F"
AMBER = "#D29A3A"


def check(name, cond, detail=""):
    global PASS
    if cond:
        PASS += 1
        print("  ok    " + name)
    else:
        FAILS.append(name)
        print("  FAIL  " + name + ("  -- " + str(detail)[:220] if detail else ""))


def edit(root, fname, old, new, count=1):
    p = root / fname
    s = p.read_text(encoding="utf-8")
    n = s.count(old)
    if n != count:
        print("mutant %s: expected %d occurrence(s) of %r in %s, found %d — "
              "refusing to report a pass on an unmutated tree"
              % (MUTATE, count, old[:70], fname, n))
        sys.exit(2)
    p.write_text(s.replace(old, new), encoding="utf-8")


def apply_mutant(root):
    if MUTATE == "no-notify":
        # A same-tab write stops notifying anybody. Every screen goes stale and
        # nothing on it says so.
        edit(root, "fieldgold-data.js",
             "  fireAfterWrite = fire; // same-tab writes now notify",
             "  // fireAfterWrite = fire;")
    elif MUTATE == "pageshow-unguarded":
        # The guard comes off and every page draws twice on arrival.
        edit(root, "fieldgold-data.js",
             "    global.addEventListener('pageshow', function (e) { if (e && e.persisted) fire(); });",
             "    global.addEventListener('pageshow', function (e) { fire(); });")
    elif MUTATE == "seed-flag-v1":
        # The version is never bumped, so a device that ran v1 never re-seeds
        # and the land status reaches the repo but not the phone.
        edit(root, "fieldgold-data.js",
             "  var SEED_FLAG    = 'fieldgold_rem_seeded_v2';",
             "  var SEED_FLAG    = 'fieldgold_rem_seeded_v1';")
    elif MUTATE == "seed-no-upgrade":
        # New records still seed; EXISTING statusless ones are left alone. This
        # is the failure that looks like success: a fresh install is correct and
        # the device that has been carrying the app all along is not.
        edit(root, "fieldgold-data.js",
             "          Object.keys(b).forEach(function (k) { cur[k] = b[k]; });\n"
             "          stampStatus(cur);\n",
             "")
    elif MUTATE == "seed-resurrects":
        # Deleted records come back on the next page load.
        edit(root, "fieldgold-data.js",
             "        } else if (!seededBefore) {",
             "        } else if (true) {")
    elif MUTATE == "listener-throws-kills-rest":
        # One screen's callback throws and takes every other subscriber with it.
        edit(root, "fieldgold-data.js",
             "  function fire() { listeners.forEach(function (fn) { try { fn(); } catch (e) {} }); }",
             "  function fire() { listeners.forEach(function (fn) { fn(); }); }")
    else:
        print("unknown mutant: " + str(MUTATE))
        sys.exit(2)


# Same recording stub the map suites use: it proves what the page ASKED Leaflet
# to draw, which is where this project's defects live.
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


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(directory):
    handler = functools.partial(Quiet, directory=str(directory))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


# The REM diamonds map.html draws, whichever tier they came out at.
REM_DIAMONDS = """() => window.__drawn.filter(
    d => d.popup && d.popup.indexOf('REM terrace candidate') >= 0)"""


def icon_colour(d):
    html = ((d.get("opts") or {}).get("icon") or {}).get("html") or ""
    return html


def main():
    root = ROOT
    if MUTATE:
        tmp = pathlib.Path(tempfile.mkdtemp()) / "repo"
        shutil.copytree(ROOT, tmp)
        root = tmp
        apply_mutant(root)

    print("reactive-refresh suite  " + str(root)
          + ("  MUTANT=" + MUTATE if MUTATE else ""))

    httpd, port = serve(root)
    base = "http://127.0.0.1:%d" % port

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context()
        # Serve the stub IN PLACE OF vendor/leaflet/leaflet.js. An init script
        # cannot do this job any more: Leaflet is vendored now, so the real
        # library loads after the init script and overwrites window.L, and every
        # recorded draw silently becomes zero.
        ctx.route("**/leaflet*.js", lambda route: route.fulfill(
            status=200, content_type="application/javascript", body=LEAFLET_STUB))
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # ------------------------------------------------------------------
        # 1. onChange fires on a same-tab write, and the map redraws.
        # ------------------------------------------------------------------
        print("\n1. a write in this tab reaches the screen")
        page.goto(base + "/map.html", wait_until="load")
        page.wait_for_timeout(600)

        seeded = page.evaluate("() => FieldGoldData.get('bench').length")
        check("  the 20 seeded benches are on the device", seeded == 20, seeded)

        drawn = page.evaluate(REM_DIAMONDS)
        check("  the map drew all 20", len(drawn) == 20, len(drawn))

        fired = page.evaluate("""() => {
          window.__fired = 0;
          FieldGoldData.onChange(() => { window.__fired++; });
          FieldGoldData.put({kind:'note', id:'n1', text:'hello'});
          return window.__fired;
        }""")
        check("  a put() notified the listener", fired >= 1, fired)

        # The case that matters: a bench that was CLEAN becomes AVOID because
        # another screen checked it. Nothing is reloaded.
        before = page.evaluate("""() => {
          const b = FieldGoldData.get('bench').find(x => x.land_status === 'clean');
          return b ? b.id : null;
        }""")
        check("  a clean bench exists to change", before is not None)
        was_rust = page.evaluate(
            "([id]) => window.__drawn.filter(d => d.popup && "
            "d.popup.indexOf('REM terrace candidate')>=0 && "
            "JSON.stringify(d.opts).indexOf('%s')>=0).length" % RUST, [before])

        page.evaluate("""([id]) => {
          const rec = JSON.parse(localStorage.getItem(FieldGoldData.KEY));
          const e = rec.entries.find(x => x.id === id);
          e.land_status = 'avoid';
          e.status_label = 'Inside Mineral Closing Order 549';
          localStorage.setItem(FieldGoldData.KEY, JSON.stringify(rec));
          // A write from another tab arrives as a storage event, not a put().
          window.dispatchEvent(new StorageEvent('storage', {key: FieldGoldData.KEY}));
        }""", [before])
        page.wait_for_timeout(200)

        now_rust = page.evaluate(
            "() => window.__drawn.filter(d => d.popup && "
            "d.popup.indexOf('REM terrace candidate')>=0 && "
            "JSON.stringify(d.opts).indexOf('%s')>=0).length" % RUST)
        check("  a cross-tab status change REDRAWS the diamond rust, no reload",
              now_rust == was_rust + 1, "%s -> %s" % (was_rust, now_rust))

        still = page.evaluate(REM_DIAMONDS)
        check("  ...and the redraw did not duplicate the layer", len(still) == 20,
              len(still))
        check("  ...and the new popup says why it is rust",
              any("Mineral Closing Order 549" in d["popup"] for d in still),
              [d["popup"][:70] for d in still][:1])

        # ------------------------------------------------------------------
        # 2. pageshow is guarded, so an ordinary load draws exactly once.
        # ------------------------------------------------------------------
        print("\n2. an ordinary page load draws once, not twice")
        page.goto(base + "/map.html", wait_until="load")
        page.wait_for_timeout(600)
        status = page.evaluate("() => document.getElementById('status').innerText")
        check("  the REM tally is logged exactly once per load",
              status.count("REM candidates:") == 1,
              status.count("REM candidates:"))
        check("  the bench tally is not doubled either",
              status.count("no bench-hunter candidates yet") <= 1,
              status.count("no bench-hunter candidates yet"))
        check("  the source still guards pageshow on e.persisted",
              "if (e && e.persisted) fire();"
              in (root / "fieldgold-data.js").read_text(encoding="utf-8"))
        # And it must still fire when the restore is real.
        refired = page.evaluate("""() => {
          window.__n = 0;
          FieldGoldData.onChange(() => { window.__n++; });
          window.dispatchEvent(new PageTransitionEvent('pageshow', {persisted: false}));
          const after_plain = window.__n;
          window.dispatchEvent(new PageTransitionEvent('pageshow', {persisted: true}));
          return [after_plain, window.__n];
        }""")
        check("  a plain pageshow does NOT fire", refired[0] == 0, refired)
        check("  a bfcache restore DOES fire", refired[1] > refired[0], refired)

        # ------------------------------------------------------------------
        # 3. One bad subscriber must not silence the others.
        # ------------------------------------------------------------------
        print("\n3. a throwing listener does not take the others down")
        survived = page.evaluate("""() => {
          window.__a = 0; window.__b = 0;
          FieldGoldData.onChange(() => { window.__a++; throw new Error('boom'); });
          FieldGoldData.onChange(() => { window.__b++; });
          try { FieldGoldData.put({kind:'note', id:'n2', text:'x'}); } catch (e) {}
          return [window.__a, window.__b];
        }""")
        check("  the throwing listener ran", survived[0] >= 1, survived)
        check("  ...and the one registered after it ran too", survived[1] >= 1,
              survived)

        # ------------------------------------------------------------------
        # 4. The seed migration, all four paths.
        # ------------------------------------------------------------------
        print("\n4. the v1 -> v2 seed migration")

        def reload_fresh(setup_js, arg=None):
            page.evaluate("() => localStorage.clear()")
            if setup_js:
                page.evaluate(setup_js, arg)
            page.goto(base + "/map.html", wait_until="load")
            page.wait_for_timeout(300)
            return page.evaluate("""() => FieldGoldData.get('bench')
                                     .filter(b => b.source === 'REM')""")

        # (a) A device that has never seen the app.
        fresh = reload_fresh(None)
        check("  a virgin device seeds all 20", len(fresh) == 20, len(fresh))
        check("  ...every one carrying a land_status",
              all(b.get("land_status") in ("clean", "unchecked", "avoid")
                  for b in fresh),
              [b.get("profile") for b in fresh if not b.get("land_status")][:3])
        check("  ...and the split is 8 clean / 12 avoid",
              (sum(1 for b in fresh if b.get("land_status") == "clean"),
               sum(1 for b in fresh if b.get("land_status") == "avoid")) == (8, 12),
              [b.get("land_status") for b in fresh])

        # (b) THE CASE THIS MIGRATION EXISTS FOR: a device that already ran v1
        # and is carrying 20 statusless records.
        v1 = json.dumps([
            {k: v for k, v in b.items()
             if k not in ("land_status", "status_label", "status_checked",
                          "state_claim", "state_claim_checked",
                          "state_claim_register", "state_claim_proximity")}
            for b in fresh
        ])
        upgraded = reload_fresh(
            """([payload]) => {
                 const recs = JSON.parse(payload);
                 localStorage.setItem(FieldGoldData.KEY, JSON.stringify(
                   {version: 1, entries: recs}));
                 localStorage.setItem('fieldgold_rem_seeded_v1', '123');
               }""", [v1])
        check("  a v1 device still has exactly 20 (no duplicates)",
              len(upgraded) == 20, len(upgraded))
        check("  ...and every statusless record was UPGRADED in place",
              all(b.get("land_status") in ("clean", "unchecked", "avoid")
                  for b in upgraded),
              [b.get("profile") for b in upgraded if not b.get("land_status")][:3])
        check("  ...including the 12 that are on encumbered ground",
              sum(1 for b in upgraded if b.get("land_status") == "avoid") == 12,
              sum(1 for b in upgraded if b.get("land_status") == "avoid"))
        check("  ...and both registers are stamped, not left to the reader",
              all(b.get("state_claim") for b in upgraded),
              [b.get("profile") for b in upgraded if not b.get("state_claim")][:3])

        # (c) A v1 device the user pruned. The upgrade must not undo that.
        pruned = json.dumps(json.loads(v1)[:5])
        kept = reload_fresh(
            """([payload]) => {
                 localStorage.setItem(FieldGoldData.KEY, JSON.stringify(
                   {version: 1, entries: JSON.parse(payload)}));
                 localStorage.setItem('fieldgold_rem_seeded_v1', '123');
               }""", [pruned])
        check("  a pruned v1 device keeps its 5 and gets NO resurrections",
              len(kept) == 5, len(kept))
        check("  ...and those 5 were still upgraded",
              kept and all(b.get("land_status") for b in kept),
              [b.get("profile") for b in kept if not b.get("land_status")][:3])

        # (d) Running twice changes nothing.
        again = page.evaluate("""() => {
          const n1 = FieldGoldData.get('bench').filter(b => b.source==='REM').length;
          FieldGoldData.seedREM();
          FieldGoldData.seedREM();
          return [n1, FieldGoldData.get('bench').filter(b => b.source==='REM').length];
        }""")
        check("  re-running the seeder does not accumulate", again[0] == again[1],
              again)

        check("  no uncaught page errors anywhere in the run", not errors,
              errors[:2])

        browser.close()

    httpd.shutdown()

    print("")
    print("%d passed, %d failed" % (PASS, len(FAILS)))

    if MUTATE:
        if FAILS:
            print("MUTANT %r CAUGHT by: %s" % (MUTATE, FAILS[0]))
            sys.exit(0)
        print("MUTANT %r SURVIVED — this suite does not catch it." % MUTATE)
        sys.exit(1)

    if FAILS:
        print("FAILED: " + ", ".join(FAILS))
        sys.exit(1)
    print("REACTIVE-REFRESH SUITE PASSED")


main()
