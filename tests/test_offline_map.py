#!/usr/bin/env python3
"""Adversarial test for the map working with NO NETWORK AT ALL.

The bug being fixed: every map page loaded Leaflet from
`https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js`. On an app
whose entire purpose is to work at a trailhead with no signal, the map library
itself was a network fetch. This was not a theory — it was measured while
writing `tests/test_map_sites.py`: with no network `window.L` is undefined and
the page's own log reads "Leaflet failed". No map, no markers, no land-status
colours.

WHAT MAKES THIS SUITE DIFFERENT FROM test_map_sites.py.

That suite stubs Leaflet, because it is asking what map.html ASKS Leaflet to
draw. This suite does the opposite: it loads the REAL vendored Leaflet and
blocks every request that does not go to the local server. If the vendored copy
is missing, truncated, or quietly swapped, this suite fails. A stub here would
defeat the entire point — it would prove the map works offline by supplying,
from the test harness, the very file whose absence is the bug.

WHAT IT STILL DOES NOT PROVE.

Basemap TILES are not vendored and are not fixed by this change. Offline you
get your benches, your logged sites, their land-status colours and their popups
drawn on a blank background. This suite asserts exactly that — including that
map.html SAYS SO on screen — rather than pretending the picture comes back too.

  python3 tests/test_offline_map.py
  python3 tests/test_offline_map.py --mutate cdnjs-back   (prove it can fail)
"""
import base64
import functools
import hashlib
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

# Published on leafletjs.com's download page — an independent publisher from
# npm, which is the whole point of the cross-check. See
# docs/vendor/leaflet/PROVENANCE.md. If you upgrade Leaflet these must be
# updated from that page BY HAND; a hash copied out of the file you are trying
# to verify is not a verification.
#
# The keys below are WEB-ROOT-relative and are correct as written: ROOT is
# REPO/"docs", so "vendor/leaflet/..." resolves under it. Only prose about
# files on disk carries the docs/ prefix. Do not add it here.
SRI = {
    "vendor/leaflet/leaflet.js":  "sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=",
    "vendor/leaflet/leaflet.css": "sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=",
}

# leaflet.css asks for these by relative path. Missing, the default marker
# renders as a broken image — a marker you cannot see, on ground you cannot dig.
VENDOR_IMAGES = ["marker-icon.png", "marker-icon-2x.png", "marker-shadow.png",
                 "layers.png", "layers-2x.png"]

MAP_PAGES = ["map.html", "stage1_map_test.html", "stage2_map.html",
             "stage3_map.html", "stage4_map.html", "stage5_map.html"]

GREEN = "#6FA760"

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


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(directory):
    handler = functools.partial(Quiet, directory=str(directory))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def mutate(root):
    """Break the tree on a throwaway copy. A mutant that matches nothing must
    ABORT: a green run against unmutated code reads as proof and is worse than
    no mutation testing at all."""
    def edit(relpath, a, b):
        p = root / relpath
        s0 = p.read_text(encoding="utf-8")
        s = s0.replace(a, b)
        if s == s0:
            print("mutant " + MUTATE + " did not match " + relpath
                  + "; refusing to report a pass on an unmutated tree")
            sys.exit(2)
        p.write_text(s, encoding="utf-8")

    if MUTATE == "cdnjs-back":
        # Put the actual shipped bug back: fetch the library over the network.
        edit("map.html", 'src="vendor/leaflet/leaflet.js"',
             'src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"')
    elif MUTATE == "sw-drop-leaflet":
        # Vendored but not cached: works on the desk, gone after an eviction.
        edit("sw.js", "  './vendor/leaflet/leaflet.js',\n", "")
    elif MUTATE == "sw-drop-images":
        edit("sw.js", "  './vendor/leaflet/images/marker-icon.png',\n", "")
    elif MUTATE == "sw-stale-cache":
        # Version read, not named. Pinned to 'fieldgold-v7', this mutant went
        # silently un-runnable the moment 0006 shipped v8: it aborted instead of
        # mutating, so nothing was proving that the v6-detection check below can
        # fail. Found while bumping to v9.
        _cur = re.search(r"const CACHE = 'fieldgold-v(\d+)';",
                         (root / "sw.js").read_text(encoding="utf-8"))
        if not _cur:
            print("mutant %s: no readable cache version in sw.js" % MUTATE)
            sys.exit(2)
        # Now v3 — the version actually on a device that never got land status,
        # which is both what "stale cache" means here and the one value that
        # violates the check below. It was 'fieldgold-v6' until 2026-07-28, when
        # the real sequential bump to v6 made the pinned check fail on a
        # CORRECT change. Same trap as test_stage_maps.py's stale-cache mutant:
        # a mutant must violate the assertion it targets, not merely differ from
        # the current value.
        edit("sw.js", "const CACHE = 'fieldgold-v%s';" % _cur.group(1),
             "const CACHE = 'fieldgold-v3';")
    elif MUTATE == "swap-leaflet":
        # A silently-swapped library. One appended byte is enough; it has to be.
        p = root / "vendor/leaflet/leaflet.js"
        p.write_bytes(p.read_bytes() + b"\n//x\n")
    elif MUTATE == "tick-on-load":
        # Put the shipped defect back: tick off Leaflet's `load` whatever the
        # tiles actually did. This is the exact code that printed five green
        # ticks over 0 of 100 tiles.
        edit("map.html",
             "      if(loaded>0){ said=true; log(name+' ✓','ok'); }",
             "      if(true){ said=true; log(name+' ✓','ok'); }")
    elif MUTATE == "silent-on-fail":
        # The false-RED direction. Stop ticking falsely AND stop reporting the
        # failure, so offline the layers simply say nothing. 7a's "reports the
        # failure instead" half is what catches this; 7a alone without it would
        # be satisfied by silence.
        edit("map.html",
             "      else if(errored>0){ said=true; log(name+' unavailable — 0 tiles loaded','err'); }\n",
             "")
    elif MUTATE == "base-tick-after-warn":
        # Drop `baseSaid` from watchBase's load guard, leaving the tile-count
        # guard in place. Invisible in the all-fail case — which is why 7c
        # exists. In the MIXED case the basemap warns and then ticks itself
        # green, the sequence the phone showed.
        edit("map.html", "if(baseOk||baseSaid||loaded===0) return;",
             "if(baseOk||loaded===0) return;")
    elif MUTATE == "no-tile-honesty":
        # Keep the map, drop the sentence that tells you the blank background
        # is a missing basemap and not a broken app.
        edit("map.html", "log('basemap tiles unavailable — no signal','warn');", "")
    else:
        print("unknown mutant: " + MUTATE)
        sys.exit(2)


def main():
    root = ROOT
    if MUTATE:
        tmp = pathlib.Path(tempfile.mkdtemp()) / "repo"
        shutil.copytree(ROOT, tmp)
        root = tmp
        mutate(root)

    print("offline map suite  " + str(root) + (f"  MUTANT={MUTATE}" if MUTATE else ""))

    # ------------------------------------------------------------------
    # 1. Nothing is fetched from a CDN any more.
    # ------------------------------------------------------------------
    print("[1] no CDN references")
    attr = re.compile(r'(?:src|href)\s*=\s*["\'][^"\']*cdnjs', re.I)
    for f in MAP_PAGES:
        s = (root / f).read_text(encoding="utf-8")
        check(f + " loads no cdnjs asset", not attr.search(s),
              (attr.search(s).group(0) if attr.search(s) else ""))
    sw = (root / "sw.js").read_text(encoding="utf-8")
    shell_src = re.search(r"const SHELL = \[(.*?)\];", sw, re.S)
    shell_entries = re.findall(r"'([^']+)'", shell_src.group(1)) if shell_src else []
    # Deliberately checks the SHELL entries, not the whole file: the comment
    # block above SHELL explains what v6 phones still hold and has to say the
    # word "cdnjs" to do it. Asserting on the comment would be asserting on
    # prose.
    check("no SHELL entry is a cdnjs URL",
          shell_entries and not any("cdnjs" in e for e in shell_entries),
          [e for e in shell_entries if "cdnjs" in e])

    # ------------------------------------------------------------------
    # 2. The vendored bytes are the bytes leafletjs.com published.
    #    Not npm's hash of npm's own file — an independent publisher.
    # ------------------------------------------------------------------
    print("[2] vendored bytes match the independently published SRI")
    for rel, want in SRI.items():
        p = root / rel
        got = ("sha256-" + base64.b64encode(
            hashlib.sha256(p.read_bytes()).digest()).decode()) if p.exists() else "MISSING"
        check(rel + " matches leafletjs.com's published hash", got == want, got)
    for img in VENDOR_IMAGES:
        p = root / "vendor/leaflet/images" / img
        check("vendor/leaflet/images/" + img + " is present",
              p.exists() and p.stat().st_size > 0)

    # ------------------------------------------------------------------
    # 3. The service worker actually caches what the pages now need.
    #    Vendoring without this is a change that works on a desk and fails
    #    after a cache eviction, offline, with nothing on screen to say so.
    # ------------------------------------------------------------------
    print("[3] service-worker shell covers the vendored assets")
    need = ["./vendor/leaflet/leaflet.js", "./vendor/leaflet/leaflet.css"] + \
           ["./vendor/leaflet/images/" + i for i in VENDOR_IMAGES]
    for n in need:
        check("SHELL caches " + n, n in shell_entries, shell_entries)
    # PUBLISHED is the last version that reached a device without land status.
    # Read, not pinned — and it took a real bump to find that out. This check
    # used to read `!= "fieldgold-v6"`, which is a pinned literal wearing a
    # comparison's clothes: it passed for as long as nobody bumped to v6 and
    # then failed on a CORRECT change, which is precisely how a suite teaches
    # the next person to edit the assertion instead of thinking. The other two
    # suites that read this value (test_stage_maps.py, test_state_claims.py)
    # were already `> 3`; CLAUDE.md said all three were, and was wrong about
    # this one.
    PUBLISHED = 3
    ver = re.search(r"const CACHE = 'fieldgold-v(\d+)'", sw)
    check("  the cache version is readable at all", bool(ver), sw[:80])
    check("cache version is past the v%d already on the device (a v%d phone "
          "has no land status at all and looks fine until it evicts)"
          % (PUBLISHED, PUBLISHED),
          bool(ver) and int(ver.group(1)) > PUBLISHED, ver and ver.group(0))

    # ------------------------------------------------------------------
    # 4. The real thing: load the map with every off-origin request blocked.
    # ------------------------------------------------------------------
    print("[4] map.html with the network cut")
    httpd, port = serve(root)
    base = f"http://127.0.0.1:{port}"
    blocked = []
    local_failed = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context()

        def gate(route, request):
            if request.url.startswith(base):
                route.continue_()
            else:
                blocked.append(request.url)
                route.abort()

        # NO leaflet stub. That is the point of this suite.
        ctx.route("**/*", gate)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("requestfailed",
                lambda r: local_failed.append(r.url) if r.url.startswith(base) else None)

        page.goto(base + "/load_rem_benches.html", wait_until="load")
        page.get_by_text("Load all 20 with status").click()
        counts = page.evaluate(
            "() => FieldGoldData.statusCounts(FieldGoldData.get('bench'))")
        check("bench land-status data loaded offline",
              (counts["clean"], counts["unchecked"], counts["avoid"]) == (8, 0, 12),
              counts)

        # A logged site on encumbered ground, placed from the loaded data —
        # never a coordinate typed into this file (repo rule 3 applies to
        # tests; it was broken once already, in test_map_sites.py).
        avoid = page.evaluate(
            "() => FieldGoldData.get('bench').find(b => b.profile === 'REM-14')")
        check("reference position came from the data, not from this file",
              bool(avoid) and "MCO 549" in (avoid.get("status_label") or ""),
              avoid and avoid.get("status_label"))
        page.evaluate(
            "([b]) => localStorage.setItem('fieldgold_sites', JSON.stringify("
            "{updated:1, sites:[{id:'off1', name:'Offline check', lat:b.lat, "
            "lon:b.lon, score:88, verdict:'Strong'}]}))", [avoid])

        page.goto(base + "/map.html", wait_until="load")
        page.wait_for_timeout(1500)

        check("the real Leaflet loaded from the repo, with no network",
              page.evaluate("() => typeof L !== 'undefined' && !!L.version"),
              page.evaluate("() => typeof L"))
        # Guarded: when the cdnjs mutant is applied L does not exist at all,
        # and an unguarded L.version throws out of the harness instead of
        # reporting a failure. A suite that crashes where it should fail hides
        # every assertion after it.
        lver = page.evaluate(
            "() => (typeof L === 'undefined' ? null : (L.version || null))")
        check("  ...and it is 1.9.4, the version PROVENANCE.md documents",
              lver == "1.9.4", lver)
        check("something off-origin really was blocked (otherwise this whole "
              "section proves nothing)", len(blocked) > 0, len(blocked))
        check("no same-origin request failed — every vendored asset resolved",
              not local_failed, local_failed[:4])

        status = page.evaluate("() => document.getElementById('status').innerText")
        check("the page does not report a missing map library",
              "map library missing" not in status, status[:200])
        check("the map came up", "map ready" in status, status[:200])

        # ------------------------------------------------------------------
        # 5. Real Leaflet means real DOM. Assert on what was actually drawn,
        #    not on what map.html asked for.
        # ------------------------------------------------------------------
        print("[5] what is actually on the screen")
        fills = page.evaluate(
            "() => Array.from(document.querySelectorAll('path.leaflet-interactive'))"
            ".map(p => p.getAttribute('fill'))")
        check("markers were rendered into the DOM by real Leaflet",
              len(fills) > 0, len(fills))
        check("something is drawn in the AVOID colour — the encumbered benches "
              "are on screen, not silently dropped",
              "#B2402F" in [f and f.upper() for f in fills],
              sorted(set(f for f in fills if f)))

        # The rendered <path> elements carry no marker identity, so which dot
        # is the logged site cannot be read off the DOM. That question is
        # test_map_sites.py's job and it is answered there against the draw
        # calls. What this suite adds is that the site reached the map AT ALL
        # with the network cut — which is the thing the CDN dependency broke.
        check("a logged site reached the offline map",
              "my sites: 1" in status, status[-300:])
        check("no marker rendered offline is the verified-open green — the "
              "only green layer is ARDF, which needs network and is absent",
              GREEN not in [f and f.upper() for f in fills if f],
              sorted(set(f for f in fills if f)))

        # ------------------------------------------------------------------
        # 6. The honest part: tiles are still gone, and the page says so.
        # ------------------------------------------------------------------
        print("[6] the basemap is still a network dependency, said out loud")
        check("the page states the basemap is unavailable",
              "basemap tiles unavailable" in status, status[-400:])
        check("  ...and states that the POINTS are still correct",
              "land-status colours are still correct" in status, status[-400:])
        check("  ...and does not claim the map works offline outright",
              "works offline" not in status.lower(), status[-400:])
        check("tile requests were among the things blocked",
              any(("tile" in u or "arcgisonline" in u or "openstreetmap" in u)
                  for u in blocked), blocked[:3])

        check("no uncaught page errors with the network cut", not errors, errors[:2])

        # ------------------------------------------------------------------
        # 7. A ✓ is earned by a tile that LOADED. Nothing else earns it.
        #
        #    Leaflet's _tileReady gates `tileload` and the leaflet-tile-loaded
        #    class on !err. It does NOT gate `load`, which fires whenever no
        #    tiles remain PENDING — including when every one of them failed. On
        #    the phone with the radios off (STATE.md, offline Run 2) map.html
        #    logged `basemap (Streets) ✓`, `claims ✓`, `ardf ✓` and `ngdbsed ✓`
        #    over ZERO loaded tiles, the basemap tick arriving three lines after
        #    its own no-signal warning.
        #
        #    Sections 4-6 above have been running these exact conditions since
        #    this suite was written and asserted nothing about them. That is why
        #    the defect reached a device through a green gate.
        #
        #    Two-sided on purpose. "No ✓ offline" is also satisfied by a page
        #    that never reports success at all — a false RED, the same defect
        #    pointing the other way. 7b is the control that forbids it.
        # ------------------------------------------------------------------
        print("[7] a tick is earned by a loaded tile, in both directions")

        # 7a. terrain is OFF by default, so neither device run exercised it, and
        #     it was mechanically the worst case: a ✓ logged off `load` paired
        #     with an EMPTY tileerror handler that swallowed every failure.
        page.check("#t-terrain")
        page.wait_for_timeout(1500)
        status = page.evaluate("() => document.getElementById('status').innerText")
        loaded_cls = page.evaluate(
            "() => document.querySelectorAll('img.leaflet-tile-loaded').length")
        in_dom = page.evaluate(
            "() => document.querySelectorAll('img.leaflet-tile').length")
        check("tiles were requested and NONE loaded — otherwise everything "
              "below this line proves nothing", in_dom > 0 and loaded_cls == 0,
              {"inDom": in_dom, "loadedClass": loaded_cls})
        for name in ["ardf", "ngdbsed", "claims", "terrain"]:
            check("no false ✓ for " + name + " over zero loaded tiles",
                  (name + " ✓") not in status, status)
            check("  ...and " + name + " reports the failure instead",
                  (name + " unavailable") in status, status)
        check("the basemap does not tick at all with nothing loaded",
              "basemap (" not in status, status)
        # The ordering half. The phone showed the warning and the tick in the
        # same log, three lines apart, which is worse than either alone.
        after_warn = status.split("basemap tiles unavailable", 1)
        check("no layer ticks green ANYWHERE after the no-signal warning",
              len(after_warn) == 2 and "✓" not in after_warn[1],
              after_warn[-1][:200])

        # 7b. The control. Every tile request fulfilled with a real PNG, so
        #     every layer must tick. Without this, deleting all ✓ logging would
        #     pass 7a.
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
            "z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")

        def fulfil(route, request):
            if request.url.startswith(base):
                route.continue_()
            else:
                route.fulfill(status=200, content_type="image/png", body=png)

        ok_ctx = browser.new_context()
        ok_ctx.route("**/*", fulfil)
        ok_page = ok_ctx.new_page()
        ok_page.goto(base + "/map.html", wait_until="load")
        ok_page.wait_for_timeout(1500)
        ok_page.check("#t-terrain")
        ok_page.wait_for_timeout(1500)
        ok_status = ok_page.evaluate(
            "() => document.getElementById('status').innerText")
        for name in ["basemap (Streets)", "ardf", "ngdbsed", "claims", "terrain"]:
            check("a layer whose tiles DO load still ticks: " + name,
                  (name + " ✓") in ok_status, ok_status)
        check("nothing reports unavailable when every tile loaded",
              "unavailable" not in ok_status, ok_status)
        ok_ctx.close()

        # 7c. The mixed case — the ONLY scenario in which watchBase's `baseSaid`
        #     guard is load-bearing. The first two basemap tiles fail, the rest
        #     succeed, so the warning fires on the first failure and `load` then
        #     arrives with loaded > 0. Without the guard the same layer warns and
        #     then ticks itself green, which is what the phone showed.
        seen = {"n": 0}

        def partial(route, request):
            if request.url.startswith(base):
                route.continue_()
            elif "openstreetmap" in request.url:
                seen["n"] += 1
                if seen["n"] <= 2:
                    route.abort()
                else:
                    route.fulfill(status=200, content_type="image/png", body=png)
            else:
                route.abort()

        part_ctx = browser.new_context()
        part_ctx.route("**/*", partial)
        part_page = part_ctx.new_page()
        part_page.goto(base + "/map.html", wait_until="load")
        part_page.wait_for_timeout(2000)
        part_status = part_page.evaluate(
            "() => document.getElementById('status').innerText")
        part_loaded = part_page.evaluate(
            "() => document.querySelectorAll('img.leaflet-tile-loaded').length")
        check("the mixed case really is mixed — some basemap tiles loaded and "
              "at least one failed", part_loaded > 0 and seen["n"] > 2,
              {"loadedClass": part_loaded, "streetsRequests": seen["n"]})
        check("a partly-failing basemap still warns",
              "basemap tiles unavailable" in part_status, part_status)
        check("  ...and does NOT then tick the same layer green",
              "basemap (Streets) ✓" not in part_status, part_status)
        part_ctx.close()

        browser.close()
    httpd.shutdown()

    print()
    print(f"{PASS} passed, {len(FAILS)} failed")
    for f in FAILS:
        print("  FAILED: " + f)
    if MUTATE and not FAILS:
        print("MUTANT SURVIVED — this suite would not have caught the bug.")
        sys.exit(1)
    if MUTATE and FAILS:
        print("mutant caught (failures above are the expected outcome)")
        sys.exit(0)
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
