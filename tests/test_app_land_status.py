"""End-to-end check that land status actually reaches the screen.

The unit suite proves fieldgold-data.js behaves. It cannot prove that the
pages USE it -- a page that imports the schema and then renders the old flat
"bench" tag would pass every unit test and still send someone to closed ground.

So this drives the real files in a real browser engine: loads the loader page,
clicks the real button, then opens the app and the map and reads what is on
the screen.

Requires: playwright + chromium (preinstalled). No network -- Leaflet and the
basemap tiles will fail to load, which is fine; the bench logic is local.
"""
import json
import pathlib
import re
import subprocess
import sys
import threading
import functools
import http.server
import socketserver

# Derived from this file's own location, NOT hardcoded. An earlier version of
# this line named an absolute path on the machine the suite was written on.
# That path existed there and held a DIFFERENT, half-finished copy of the app,
# so the suite ran green while testing bytes that were never shipped -- and on
# any other machine it would have died with "no such file". Green for the wrong
# reason, then red for a reason that has nothing to do with the app. Both are
# worse than a failure that means something.
REPO = pathlib.Path(__file__).resolve().parent.parent
# Web root. The app lives under docs/ so that webDir can point at a directory
# containing only web assets — tests/ and tools/ must never ship in the bundle.
ROOT = REPO / "docs"
PASS, FAILS = 0, []


def check(name, cond, detail=""):
    global PASS
    if cond:
        PASS += 1
        print(f"  ok    {name}")
    else:
        FAILS.append(name)
        print(f"  FAIL  {name}" + (f"  -- {detail}" if detail else ""))


def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(ROOT))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    httpd.allow_reuse_address = True
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, httpd.server_address[1]


def main():
    from playwright.sync_api import sync_playwright

    httpd, port = serve()
    base = f"http://127.0.0.1:{port}"
    print(f"land-status app suite  serving {ROOT} on {base}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context()
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # ---------------------------------------------------------------
        # 1. The loader page, driven the way Alan would drive it.
        # ---------------------------------------------------------------
        page.goto(f"{base}/load_rem_benches.html", wait_until="load")
        page.get_by_text("Load all 20 with status").click()
        status_text = page.locator("#status").inner_text()
        check("loader reports 8 clean / 0 unchecked / 12 avoid",
              "8 verified clean" in status_text
              and "0 unchecked" in status_text
              and "12 flagged avoid" in status_text,
              status_text)

        stored = page.evaluate("JSON.parse(localStorage.getItem('fieldgold_record')).entries")
        benches = [e for e in stored if e.get("kind") == "bench"]
        check("20 bench records written to localStorage", len(benches) == 20, str(len(benches)))
        tiers = {}
        for b in benches:
            tiers[b.get("land_status")] = tiers.get(b.get("land_status"), 0) + 1
        check("stored tiers are 8 clean / 12 avoid / no unchecked",
              tiers == {"clean": 8, "avoid": 12}, json.dumps(tiers))

        # The five newly-cleared benches were checked with the 8-layer Tier-1
        # battery, not the full 16. That difference must survive into the record
        # -- if it only lives in a log file it is not available at a trailhead.
        depths = {}
        for b in benches:
            depths[b.get("status_depth")] = depths.get(b.get("status_depth"), 0) + 1
        check("every bench records HOW deeply it was checked",
              depths == {"full": 8, "tier1": 12}, json.dumps(depths))

        # Two of the eight clean are outside the Public Use Area and so do NOT
        # inherit its panning permission. That is the single easiest thing to
        # lose in a ranking, because they sit in the green tier next to six that
        # do. Assert the distinction is carried per-record, not just in prose.
        clean = [b for b in benches if b["land_status"] == "clean"]
        check("outside-PUA clean benches are flagged in_pua False",
              sorted(b["profile"] for b in clean if b["in_pua"] is False)
              == ["REM-19", "REM-7"], json.dumps([b["profile"] for b in clean]))
        check("every outside-PUA clean bench says so in its visible label",
              all("OUTSIDE the Public Use Area" in b["status_label"]
                  for b in clean if b["in_pua"] is False))
        check("every stored bench has a land_status",
              all("land_status" in b for b in benches))

        # ---------------------------------------------------------------
        # 2. The Bench Hunter's re-sync must not delete them.
        #    Calls the same data-layer API bench_hunter.html now calls.
        # ---------------------------------------------------------------
        page.evaluate("""() => {
            FieldGoldData.replaceKind('bench', [
              {lat:61.71, lon:-149.24, source:'benchhunter', profile:1, count:2,
               strong:true, nearest:6}
            ], { where: e => e.source !== 'REM' });
        }""")
        after = page.evaluate("FieldGoldData.get('bench')")
        rem_after = [b for b in after if b.get("source") == "REM"]
        check("all 20 REM records survive a Bench Hunter re-sync",
              len(rem_after) == 20, str(len(rem_after)))
        check("the new bench-hunter record is present and unchecked",
              any(b.get("source") == "benchhunter" and b.get("land_status") == "unchecked"
                  for b in after))
        # DELIBERATELY LEAVE the bench-hunter record in place from here on.
        #
        # As of 2026-07-25 none of the 20 REM candidates is 'unchecked' any more.
        # The unchecked tier is still the most safety-critical branch in the whole
        # schema -- it is what ANY new bench defaults to -- so the suite must keep
        # exercising it against a real record rather than deleting the assertions
        # along with the last unchecked REM bench. This bench-hunter entry is that
        # record, and it is exactly the case that matters: a bench the user just
        # created, that nobody has run past DNR.

        # ---------------------------------------------------------------
        # 3. The main app: does the status reach the DOM?
        # ---------------------------------------------------------------
        page.goto(f"{base}/index.html", wait_until="load")
        page.wait_for_timeout(400)

        # The planner needs a selected stop before it suggests neighbours, and
        # needs a logged site to anchor distance. Seed one directly.
        page.evaluate("""() => {
            const rem = FieldGoldData.get('bench').filter(b => b.source === 'REM');
            const clean = rem.find(b => b.land_status === 'clean');
            const avoid = rem.find(b => b.land_status === 'avoid');
            window.__ids = { clean: 'rem-' + clean.rank, avoid: 'rem-' + avoid.rank };
            window.__names = { clean: clean.profile, avoid: avoid.profile };
        }""")
        ids = page.evaluate("window.__ids")

        # statusBadge is the single renderer every list goes through.
        badges = page.evaluate("""() => {
            const rem = FieldGoldData.get('bench').filter(b => b.source === 'REM');
            const pick = t => rem.find(b => b.land_status === t);
            return {
              clean: statusBadge({_status:'clean'}),
              unchecked: statusBadge({_status:'unchecked'}),
              avoid: statusBadge({_status:'avoid'}),
              rawClean: statusBadge(pick('clean')),
              rawAvoid: statusBadge(pick('avoid')),
              noField: statusBadge({kind:'bench', lat:1, lon:1}),
            };
        }""")
        check("badge for clean says CLEAN", "CLEAN" in badges["clean"] and "green" in badges["clean"])
        check("badge for avoid says AVOID", "AVOID" in badges["avoid"] and "rust" in badges["avoid"])
        check("badge for unchecked says NOT CHECKED",
              "NOT CHECKED" in badges["unchecked"] and "amber" in badges["unchecked"])
        check("badge reads a raw record's land_status too",
              "CLEAN" in badges["rawClean"] and "AVOID" in badges["rawAvoid"])
        check("badge on a record with no land_status says NOT CHECKED, not CLEAN",
              "NOT CHECKED" in badges["noField"], badges["noField"])

        # allRoutableStops must carry the tier through to routing.
        stops = page.evaluate("allRoutableStops()")
        bench_stops = [s for s in stops if s.get("isBench")]
        check("every routable bench stop carries a _status",
              len(bench_stops) == 21 and all(s.get("_status") for s in bench_stops),
              str(len(bench_stops)))
        st_counts = {}
        for s_ in bench_stops:
            st_counts[s_["_status"]] = st_counts.get(s_["_status"], 0) + 1
        check("routing sees 8 clean, 12 avoid and the 1 unchecked new bench",
              st_counts == {"clean": 8, "avoid": 12, "unchecked": 1},
              json.dumps(st_counts))

        # THE ROUTING QUESTION: select an avoid stop, does the app say so?
        page.evaluate("""(ids) => {
            S.tripSelection = [ids.avoid, ids.clean];
        }""", ids)
        avoid_found = page.evaluate("avoidStopsInTrip().map(s => s.name)")
        check("avoidStopsInTrip finds the encumbered stop in the selection",
              len(avoid_found) == 1, json.dumps(avoid_found))

        # The GPX is the artifact that leaves the app entirely.
        gpx = page.evaluate("""() => {
            const stops = allRoutableStops();
            const sel = S.tripSelection.map(id => stops.find(s => s.id === id)).filter(Boolean);
            return buildGpx(orderTrip(sel));
        }""")
        check("GPX marks the encumbered waypoint AVOID in its NAME",
              re.search(r"<name>AVOID — ", gpx) is not None,
              "no AVOID-prefixed <name> found")
        check("GPX uses a red flag symbol for the encumbered waypoint",
              "Flag, Red" in gpx)
        check("GPX does NOT prefix the clean waypoint with AVOID",
              gpx.count("AVOID — ") == 1, str(gpx.count("AVOID — ")))
        check("GPX description states the closure",
              "LAND STATUS: AVOID" in gpx)

        # The outside-PUA caveat must survive into the GPX. Once that file is in
        # onX there is no FieldGold around it to explain that a green flag on
        # REM-19 does not carry the PUA's panning permission.
        gpx_nopua = page.evaluate("""() => {
            const stops = allRoutableStops();
            const b = FieldGoldData.get('bench').find(x => x.profile === 'REM-19');
            const s = stops.find(x => x.id === benchId(b));
            return buildGpx([s]);
        }""")
        check("GPX carries the OUTSIDE-the-PUA caveat on a clean-but-unpermitted bench",
              "OUTSIDE the Public Use Area" in gpx_nopua,
              "caveat missing from exported waypoint")

        # An unchecked bench must also be labelled in the exported file.
        gpx_unchecked = page.evaluate("""() => {
            const stops = allRoutableStops();
            const u = stops.find(s => s._status === 'unchecked');
            return buildGpx([u]);
        }""")
        check("GPX marks an unchecked waypoint NOT CHECKED in its name",
              "<name>NOT CHECKED — " in gpx_unchecked)

        # Rendered planner HTML: the visible warning.
        #
        # Match on "in this route", which appears ONLY in the route banner. An
        # earlier version of this test matched "encumbered ground" and passed
        # against the hidden-avoid notice further up the page -- a green tick
        # for a string the banner never produced. A test that can pass without
        # the feature is not a test.
        #
        # Select a KNOWN stop rather than whichever avoid record happens to be
        # first: the five avoid candidates carry different instruments (MCO,
        # LLO, pending ADL) and different label wording, so "first avoid" makes
        # the assertion depend on array order.
        planner = page.evaluate("""() => {
            const rem = FieldGoldData.get('bench').filter(b => b.source === 'REM');
            const mco = rem.find(b => (b.status_label || '').includes('MCO 549'));
            const clean = rem.find(b => b.land_status === 'clean');
            // The unchecked stop is no longer a REM record -- it is the
            // bench-hunter bench created above. Resolve its id through the app's
            // own benchId() rather than assuming the 'rem-N' shape.
            const unch = FieldGoldData.get('bench')
                          .find(b => FieldGoldData.statusOf(b) === 'unchecked');
            S.tripSelection = ['rem-' + mco.rank, 'rem-' + clean.rank, benchId(unch)];
            return renderTripPlanner(S.sites.filter(s => s.gps));
        }""")
        check("planner renders the red encumbered-ground route banner",
              "in this route is on encumbered ground" in planner
              or "in this route are on encumbered ground" in planner,
              "banner sentence not found")
        check("planner banner names the actual closing order",
              "MCO 549" in planner, "MCO 549 not rendered")
        check("planner warns that a selected stop was never checked",
              "never been land-status checked" in planner)
        check("planner no longer renders the old flat 'bench' tag",
              'class="badge amber">bench<' not in planner)

        # ---------------------------------------------------------------
        # 4. The map: marker colour must track status.
        # ---------------------------------------------------------------
        page.goto(f"{base}/map.html", wait_until="domcontentloaded")
        page.wait_for_timeout(900)
        colors = page.evaluate("""() => {
            const benches = FieldGoldData.get('bench');
            return benches.map(b => ({
              id: b.id, st: FieldGoldData.statusOf(b),
              color: FieldGoldData.statusMeta(b).color
            }));
        }""")
        by_color = {}
        for c in colors:
            by_color.setdefault(c["color"], set()).add(c["st"])
        check("map resolves exactly three marker colours", len(by_color) == 3,
              json.dumps({k: sorted(v) for k, v in by_color.items()}))
        check("each colour maps to exactly one tier",
              all(len(v) == 1 for v in by_color.values()))

        check("no uncaught page errors anywhere in the run",
              not [e for e in errors if "Leaflet" not in e and "tile" not in e.lower()],
              "; ".join(errors[:3]))

        browser.close()
    httpd.shutdown()

    print()
    print(f"{PASS} passed, {len(FAILS)} failed")
    if FAILS:
        print("FAILED: " + ", ".join(FAILS))
        sys.exit(1)
    print("APP SUITE PASSED")


if __name__ == "__main__":
    main()
