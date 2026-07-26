#!/usr/bin/env python3
"""Adversarial test for the SECOND register: state mining claims.

WHAT 0006 FIXED, AND WHAT IT LEFT.

0006 proved the map was asking the wrong government. `BLM_AK_Federal_Mining_
Claims` holds federal claims on federal land; this reach is state land (GS 1222,
state patent 50-87-0076), so the claims that govern this ground live in DNR's
`ME112` (active) and `ME13` (pending). 0006 stopped the app painting a federal
zero green. It did not tell anyone what the state register actually says.

Measured 2026-07-25 against Mapper/Mineral_Estate_Layers/MapServer/112 and /13:
**22 active state claims** inside the reach envelope, **0 pending**, against
**1** polygon in the federal layer over the same ground — and **3** active state
claims inside the box holding REM-1/11/19/20, where the federal layer returns
none. Every one of the 20 bench points was queried against ME112 and every one
came back empty. So: claims are near, and no bench is inside one.

THE INVARIANT THIS SUITE EXISTS TO DEFEND.

`land_status` and `state_claim` are two registers, asked separately, kept
separate. A bench can be CLEAN on every encumbrance layer and still sit inside
somebody's active claim. The moment those two tiers are folded into one to tidy
the popup, an unchecked claim inherits a clean encumbrance call — which is the
0006 bug wearing different clothes.

And the unknown side of it: unknown -> `unchecked`, NEVER `none`. "We did not
ask" and "we asked and the answer was no" must not render the same way on a
screen someone reads at a trailhead.

WHAT THIS SUITE PROVES, AND WHAT IT DOES NOT.

Sections 1-2 run the real `fieldgold-data.js` in a browser and feed it junk.
Section 3 reads the generated loader off disk. Section 4 re-runs the generator
into a scratch copy and demands byte-identical output — repo rule 6, and the
only check here that would catch the generator drifting away from the file it
is supposed to own. Sections 5-6 load the real `map.html` with real data and
read back what the page CHOSE to draw; Leaflet is a recording stub, so this
says nothing about rendering. Section 7 is static text.

One honest limit, and it is the reason section 6 exists at all: per-bench claim
PROXIMITY was never measured. The fetch proxy closed on the envelope-count form
partway through the session and it was not routed around. Every record carries
`state_claim_proximity: "unknown"`, and section 6 asserts the page never prints
a metre distance to a claim — because until that number is measured, a number
there would be a fabrication.

  python3 tests/test_state_claims.py
  python3 tests/test_state_claims.py --mutate claim-none-default

mutants: claim-none-default, merge-tiers, drop-date, drop-line, drop-line-rem,
         fake-proximity, fake-proximity-gen, gen-drop-field, drop-panel,
         stale-cache
"""
import functools
import http.server
import json
import pathlib
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
MUTATE = sys.argv[sys.argv.index("--mutate") + 1] if "--mutate" in sys.argv else None

PASS = 0
FAILS = []

CLEAN_GREEN = "#4E9A5F"
AMBER = "#D29A3A"
RUST = "#B2402F"

NONE_LABEL = "NO STATE CLAIM ON THIS POINT"
CLAIMED_LABEL = "INSIDE A STATE MINING CLAIM"
UNCHECKED_LABEL = "STATE CLAIMS NOT CHECKED"

# A number followed by a distance unit. Used only inside the state-claim slice
# of a popup, so the legitimate "nearest 12 m above creek" line cannot mask it.
DISTANCE_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:m|meters|metres|km|ft|feet|mi)\b")


def check(name, cond, detail=""):
    global PASS
    if cond:
        PASS += 1
        print("  ok    " + name)
    else:
        FAILS.append(name)
        print("  FAIL  " + name + ("  -- " + str(detail)[:220] if detail else ""))


# Same recording stub the other suites use, and for the same reason: it proves
# what the page ASKED Leaflet to draw. The defect species this project keeps
# hitting is in the choosing, not in the drawing.
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


def edit(root, fname, old, new, count=1):
    """Apply a mutation, or abort.

    A mutant whose replace() matches nothing leaves the tree intact and the
    suite then "passes" against unmutated code, which is worse than no mutation
    testing at all because it reads as evidence.
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
    if MUTATE == "claim-none-default":
        # The whole invariant, inverted: an unrecognised value falls through to
        # 'none' instead of 'unchecked'. "We did not ask" now renders as "we
        # asked and the answer was no".
        edit(root, "fieldgold-data.js",
             "        s === STATE_CLAIM.UNCHECKED) return s;\n"
             "    return STATE_CLAIM.UNCHECKED;",
             "        s === STATE_CLAIM.UNCHECKED) return s;\n"
             "    return STATE_CLAIM.NONE;")
    elif MUTATE == "merge-tiers":
        # The tidy-the-popup change: let a clean encumbrance call stand in for
        # a claim check when the claim field is missing. This is the 0006 bug
        # in new clothes, and it is the single most likely future regression.
        edit(root, "fieldgold-data.js",
             "    return normalizeStateClaim(entry.state_claim);",
             "    if (entry.state_claim === undefined && entry.land_status === 'clean')\n"
             "      return STATE_CLAIM.NONE;\n"
             "    return normalizeStateClaim(entry.state_claim);")
    elif MUTATE == "drop-date":
        # Keep the tier, drop the shelf life. A 'none' with no date on it is
        # not a result, it is a rumour.
        edit(root, "map.html",
             "    const when = on ? ' — checked '+on : ' — no check date on this record';",
             "    const when = '';")
    elif MUTATE == "drop-line":
        # The register is measured, stored, documented — and never printed.
        # TWO occurrences now: map.html draws two diamond layers, the bench
        # hunter's and the lidar set's, and each calls the shared helper. Both
        # are removed here, because a mutant that removes one and is caught by
        # the other proves nothing about the one it removed.
        edit(root, "map.html", "          +stateClaimLine(b)\n", "", count=2)
    elif MUTATE == "drop-line-rem":
        # Only the REM layer loses it. The lidar set is the one carrying all 20
        # seeded records and 12 of the avoid tier, so this is the deletion that
        # would actually reach a phone — and it is invisible to any check that
        # reads the bench layer and calls that "every bench".
        edit(root, "map.html",
             "          +statusWarn(b)\n          +stateClaimLine(b)\n"
             "          +'<br><span style=\"font-size:.72rem;color:#6E6857;\">Lidar",
             "          +statusWarn(b)\n"
             "          +'<br><span style=\"font-size:.72rem;color:#6E6857;\">Lidar")
    elif MUTATE == "fake-proximity":
        # The number nobody measured, printed as though somebody had.
        edit(root, "map.html",
             "+'How near the nearest one is was never measured — confirm in Alaska Mapper.</span>'",
             "+'Nearest active state claim: 250 m.</span>'")
    elif MUTATE == "fake-proximity-gen":
        # Same fabrication, one layer deeper: the generator writes a zero and
        # the assertion that would have caught it is removed with it.
        edit(root, "tools/build_loader.py",
             '    nb["state_claim_proximity"] = "unknown"',
             '    nb["state_claim_proximity"] = 0')
        edit(root, "tools/build_loader.py",
             'assert all(b["state_claim_proximity"] == "unknown" for b in out), \\\n'
             '    "per-bench claim proximity was never measured — do not let it read as zero"\n',
             "")
    elif MUTATE == "gen-drop-field":
        # The generator stops writing the field. The committed HTML still has
        # it, so only a regeneration catches this.
        edit(root, "tools/build_loader.py", '    nb["state_claim"] = "none"\n', "")
    elif MUTATE == "drop-panel":
        edit(root, "map.html", 'id="state-register"', 'id="state-register-hidden" hidden')
    elif MUTATE == "stale-cache":
        # Read the current version rather than naming it. Pinned to
        # 'fieldgold-v4', this mutant began aborting with exit 2 the moment 0009
        # bumped the cache to v5 — a mutant that cannot be applied is not a
        # passing mutant, and the abort is the only reason that was noticed.
        _c = re.search(r"const CACHE = 'fieldgold-v(\d+)';",
                       (root / "sw.js").read_text())
        if not _c:
            print("stale-cache: no cache version to mutate")
            sys.exit(2)
        edit(root, "sw.js", "const CACHE = 'fieldgold-v%s';" % _c.group(1),
             "const CACHE = 'fieldgold-v3';")
    else:
        print("unknown mutant: " + str(MUTATE))
        sys.exit(2)


# Every land-status diamond on map.html, whichever layer drew it. map.html has
# two: the bench-hunter set (loadBenches, scoped to source !== 'REM') and the
# lidar set (loadREM, scoped to source === 'REM'). Both are asked the same
# questions here, because both make the same promises about the claim register.
DIAMONDS = """() => window.__drawn.filter(d => d.popup && (
    d.popup.indexOf('Bench candidate') >= 0 ||
    d.popup.indexOf('REM terrace candidate') >= 0))"""


def claim_slice(popup):
    """The state-claim portion of a bench popup, and nothing else.

    Sliced from the first claim label to the closing 'Walk the shelf' line, so
    the legitimate 'nearest N m above creek' figure cannot launder a fabricated
    claim distance past section 6.
    """
    i = -1
    for lab in (NONE_LABEL, CLAIMED_LABEL, UNCHECKED_LABEL):
        j = popup.find(lab)
        if j >= 0 and (i < 0 or j < i):
            i = j
    if i < 0:
        return ""
    # Two layers, two closing lines. The bench-hunter diamond ends with 'Walk
    # the shelf'; the REM diamond ends with the lidar caveat. Slicing to
    # whichever comes first keeps the same guarantee for both: the figures that
    # follow the claim line cannot be read as claim distances.
    end = -1
    for tail in ("Walk the shelf", "Lidar geomorphic target"):
        j = popup.find(tail, i)
        if j >= 0 and (end < 0 or j < end):
            end = j
    return popup[i:end if end > 0 else len(popup)]


def main():
    root = ROOT
    if MUTATE:
        tmp = pathlib.Path(tempfile.mkdtemp()) / "repo"
        shutil.copytree(ROOT, tmp)
        root = tmp
        apply_mutant(root)

    print("state-claim register suite  " + str(root)
          + ("  MUTANT=" + MUTATE if MUTATE else ""))

    map_txt = (root / "map.html").read_text(encoding="utf-8")
    loader_txt = (root / "load_rem_benches.html").read_text(encoding="utf-8")
    gen_txt = (root / "tools" / "build_loader.py").read_text(encoding="utf-8")
    sw = (root / "sw.js").read_text(encoding="utf-8")

    httpd, port = serve(root)
    base = "http://127.0.0.1:%d" % port

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context()
        ctx.route("**/leaflet*.js", lambda route: route.fulfill(
            status=200, content_type="application/javascript", body=LEAFLET_STUB))
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(base + "/load_rem_benches.html", wait_until="load")

        # --------------------------------------------------------------
        # 1. Unknown -> 'unchecked'. NEVER 'none'.
        # --------------------------------------------------------------
        print("\n1. the unknown-input invariant, run against the real data layer")
        check("  the data layer exposes the claim register at all",
              page.evaluate("() => !!(window.FieldGoldData && FieldGoldData.stateClaimOf)"))

        junk = ["", " ", "no", "nope", "n/a", "unknown", "NULL", "0", "false",
                "clear", "open", "not claimed", "none found", "no claims",
                "clean", "avoid", "checked", "-", "null"]
        got = page.evaluate(
            "vals => vals.map(v => FieldGoldData.stateClaimOf({state_claim: v}))", junk)
        bad = [(v, g) for v, g in zip(junk, got) if g != "unchecked"]
        check("  every near-miss string reads UNCHECKED, not none", not bad, bad[:3])

        nonstr = page.evaluate(
            "() => [undefined, null, 0, 1, true, false, {}, [], NaN]"
            ".map(v => FieldGoldData.stateClaimOf({state_claim: v}))")
        check("  every non-string reads UNCHECKED", set(nonstr) == {"unchecked"}, nonstr)

        check("  a missing field reads UNCHECKED",
              page.evaluate("() => FieldGoldData.stateClaimOf({lat:61.7, lon:-149.2})")
              == "unchecked")
        check("  a missing ENTRY reads UNCHECKED",
              page.evaluate("() => [FieldGoldData.stateClaimOf(null),"
                            "FieldGoldData.stateClaimOf(undefined),"
                            "FieldGoldData.stateClaimOf('bench')]") == ["unchecked"] * 3)

        # The three real answers must survive, case- and whitespace-insensitively,
        # or a future author works around the normaliser instead of using it.
        real = page.evaluate(
            "() => ['none','NONE',' none ','claimed','CLAIMED','unchecked']"
            ".map(v => FieldGoldData.stateClaimOf({state_claim: v}))")
        check("  the three real answers round-trip",
              real == ["none", "none", "none", "claimed", "claimed", "unchecked"], real)

        # --------------------------------------------------------------
        # 2. Two registers. They do not leak into one another.
        # --------------------------------------------------------------
        print("\n2. land_status and state_claim stay separate")
        cross = page.evaluate(
            "() => ({"
            " cleanNoClaim: FieldGoldData.stateClaimOf({kind:'bench',land_status:'clean'}),"
            " avoidNoClaim: FieldGoldData.stateClaimOf({kind:'bench',land_status:'avoid'}),"
            " claimedStaysClean: FieldGoldData.statusOf({kind:'bench',land_status:'clean',state_claim:'claimed'}),"
            " noneStaysAvoid: FieldGoldData.statusOf({kind:'bench',land_status:'avoid',state_claim:'none'}),"
            " claimOnUnchecked: FieldGoldData.stateClaimOf({kind:'bench',land_status:'unchecked',state_claim:'none'})"
            "})")
        check("  a CLEAN encumbrance call does NOT imply 'no claim'",
              cross["cleanNoClaim"] == "unchecked", cross)
        check("  an AVOID encumbrance call does NOT imply a claim either",
              cross["avoidNoClaim"] == "unchecked", cross)
        check("  a claim does not silently downgrade land_status",
              cross["claimedStaysClean"] == "clean", cross)
        check("  'no claim' does not silently upgrade an AVOID bench",
              cross["noneStaysAvoid"] == "avoid", cross)
        check("  a claim answer survives on an unchecked bench",
              cross["claimOnUnchecked"] == "none", cross)

        tiers = page.evaluate("() => [Object.values(FieldGoldData.STATUS),"
                              "Object.values(FieldGoldData.STATE_CLAIM)]")
        check("  the two tier vocabularies share no word",
              not (set(tiers[0]) & set(tiers[1]) - {"unchecked"}), tiers)
        check("  ...except 'unchecked', which means the same thing in both",
              "unchecked" in tiers[0] and "unchecked" in tiers[1], tiers)

        dates = page.evaluate(
            "() => [FieldGoldData.stateClaimCheckedOn({state_claim_checked:'2026-07-25'}),"
            "FieldGoldData.stateClaimCheckedOn({state_claim_checked:'  '}),"
            "FieldGoldData.stateClaimCheckedOn({state_claim_checked:20260725}),"
            "FieldGoldData.stateClaimCheckedOn({}),"
            "FieldGoldData.stateClaimCheckedOn(null)]")
        check("  a check date is returned when present, null when not",
              dates == ["2026-07-25", None, None, None, None], dates)

        # --------------------------------------------------------------
        # 3. Every generated record carries the second register.
        # --------------------------------------------------------------
        print("\n3. the generated loader carries state_claim on every record")
        m = re.search(r"const REM_BENCHES\s*=\s*(\[[\s\S]*?\n\]);", loader_txt)
        check("  the payload was found in the generated file", bool(m))
        recs = json.loads(m.group(1)) if m else []
        check("  all 20 REM records are present", len(recs) == 20, len(recs))
        check("  every record has state_claim == 'none'",
              all(r.get("state_claim") == "none" for r in recs),
              [r.get("profile") for r in recs if r.get("state_claim") != "none"][:3])
        check("  every record's claim date matches its land-status date",
              all(r.get("state_claim_checked") == r.get("status_checked") for r in recs),
              [(r.get("profile"), r.get("state_claim_checked"), r.get("status_checked"))
               for r in recs if r.get("state_claim_checked") != r.get("status_checked")][:3])
        check("  every claim date is non-empty",
              all(r.get("state_claim_checked") for r in recs))
        check("  every record names the register it was asked of",
              all("ME112" in (r.get("state_claim_register") or "") for r in recs))
        check("  proximity is the string 'unknown' on every record, never a number",
              all(r.get("state_claim_proximity") == "unknown" for r in recs),
              [r.get("state_claim_proximity") for r in recs
               if r.get("state_claim_proximity") != "unknown"][:3])
        check("  the loader page tells the reader claims are near",
              "22 active" in loader_txt and "ME112" in loader_txt
              and "Proximity was never measured" in loader_txt)

        # --------------------------------------------------------------
        # 4. The generator owns the file. Repo rule 6.
        # --------------------------------------------------------------
        print("\n4. the generator holds the invariant and owns its output")
        for needle, why in [
            ('assert all(b["state_claim"] == "none" for b in out)',
             "the empty-result assertion"),
            ('assert all(b["state_claim_checked"] == b["status_checked"] for b in out)',
             "the dates-agree assertion"),
            ('assert all(b["state_claim_proximity"] == "unknown" for b in out)',
             "the never-a-zero assertion"),
        ]:
            check("  build_loader.py still holds %s" % why, needle in gen_txt)

        # SRC and DST are the same file. Without this, a derived field whose
        # assignment is deleted keeps appearing on every record — inherited from
        # the previous run's output — with the assertions green and the bytes
        # unchanged. The gen-drop-field mutant could not fail until this landed.
        check("  build_loader.py drops inherited derived fields before writing",
              "DERIVED = (" in gen_txt and "nb.pop(k, None)" in gen_txt,
              "a derived field must disappear when it stops being derived")
        check("  ...and state_claim is in that list",
              re.search(r"DERIVED = \([^)]*\"state_claim\"", gen_txt, re.S) is not None)
        check("  ...and geo_score/geo_rank are NOT (they must be inherited)",
              not re.search(r"DERIVED = \([^)]*geo_", gen_txt, re.S))

        scratch = pathlib.Path(tempfile.mkdtemp()) / "regen"
        shutil.copytree(root, scratch)
        before = (scratch / "load_rem_benches.html").read_bytes()
        proc = subprocess.run([sys.executable, "tools/build_loader.py"],
                              cwd=str(scratch), capture_output=True, text=True)
        check("  the generator runs clean against the committed tree",
              proc.returncode == 0, (proc.stderr or proc.stdout)[-300:])
        after = (scratch / "load_rem_benches.html").read_bytes()
        check("  re-running it is a byte-exact no-op (rule 6: never hand-edit)",
              before == after,
              "the committed loader is not what the generator produces")
        check("  the generator reported the expected tier split",
              "clean=8" in proc.stdout and "avoid=12" in proc.stdout,
              proc.stdout[-200:])
        shutil.rmtree(scratch.parent, ignore_errors=True)

        # --------------------------------------------------------------
        # 5. BEHAVIOUR: what the map actually prints in a bench popup.
        # --------------------------------------------------------------
        print("\n5. behaviour: the claim line on every bench popup")
        page.get_by_text("Load all 20 with status").click()
        page.wait_for_timeout(200)
        loaded = page.evaluate("() => FieldGoldData.get('bench').length")
        check("  20 benches reached localStorage", loaded == 20, loaded)

        # One bench-hunter record alongside the 20 lidar ones, so BOTH diamond
        # layers draw in this section. Without it every assertion below reads
        # only loadREM, and a deletion from loadBenches — the layer a user's own
        # hunter output lands on — passes untouched. It carries no state_claim
        # on purpose: the unknown case is the one that must not read as 'none'.
        page.evaluate("""() => {
          FieldGoldData.put({kind:'bench', profile:'HUNT-1', lat:61.7500, lon:-149.2500,
                             count:3, nearest:9, land_status:'clean',
                             status_checked:'2026-07-25'});
        }""")

        page.goto(base + "/map.html", wait_until="load")
        page.wait_for_timeout(600)
        marks = page.evaluate(DIAMONDS)
        check("  every bench was drawn", len(marks) == 21, len(marks))

        by_layer = {"REM": [d for d in marks if "REM terrace candidate" in d["popup"]],
                    "hunter": [d for d in marks if "Bench candidate" in d["popup"]]}
        check("  the lidar layer drew 20 and the hunter layer drew 1",
              (len(by_layer["REM"]), len(by_layer["hunter"])) == (20, 1),
              {k: len(v) for k, v in by_layer.items()})
        check("  the hunter record reads NOT CHECKED, never 'none'",
              by_layer["hunter"]
              and UNCHECKED_LABEL in by_layer["hunter"][0]["popup"]
              and NONE_LABEL not in by_layer["hunter"][0]["popup"],
              claim_slice(by_layer["hunter"][0]["popup"])[:160] if by_layer["hunter"] else "")

        # The 20 REM benches are drawn by loadREM, not loadBenches. That split
        # is the fix for a real hazard: before it, both functions drew every REM
        # record, so two markers stacked on one coordinate and whichever drew
        # last won — and the REM layer was flat cyan with no land status, so it
        # could land on top of the rust diamond that had it right. If the scope
        # filters are ever removed, the count above still reads 40 and only this
        # check notices.
        coords = [tuple(round(float(v), 6) for v in d["latlng"]) for d in marks]
        dupes = sorted({c for c in coords if coords.count(c) > 1})
        check("  no coordinate carries two diamonds (the layers are disjoint)",
              not dupes, dupes[:3])
        check("  ...and every drawn diamond belongs to exactly one of the two layers",
              len(by_layer["REM"]) + len(by_layer["hunter"]) == len(marks),
              len(marks))
        check("  EVERY bench popup carries a state-claim line",
              all(claim_slice(d["popup"]) for d in marks),
              [d["popup"][:80] for d in marks if not claim_slice(d["popup"])][:1])
        # The next three are about the twenty records that WERE queried against
        # ME112, so they are scoped to the lidar layer. The hunter record was
        # never asked, and it is asserted above to say exactly that instead.
        checked = by_layer["REM"]
        check("  ...and every one reads NO STATE CLAIM (all 20 came back empty)",
              all(NONE_LABEL in d["popup"] for d in checked),
              sum(1 for d in checked if NONE_LABEL not in d["popup"]))
        check("  ...and every one carries the date the check was taken",
              all("— checked 2026-07-" in d["popup"] for d in checked),
              [claim_slice(d["popup"])[:120] for d in checked
               if "— checked 2026-07-" not in d["popup"]][:1])
        check("  ...and every one says claims are near even though none is on the point",
              all("22 active state claims sit in this reach" in d["popup"] for d in checked))
        check("  no uncaught page errors", not errors, errors[:2])

        # The three ways a record can be wrong, injected into real storage.
        print("\n   the same page, with three damaged records")
        page.evaluate("""() => {
          const rec = JSON.parse(localStorage.getItem(FieldGoldData.KEY));
          const by = n => rec.entries.find(e => e.kind==='bench' && e.profile===n);
          delete by('REM-2').state_claim;             // field never written
          delete by('REM-7').state_claim_checked;     // answer with no date
          by('REM-13').state_claim = 'claimed';       // clean bench, inside a claim
          by('REM-14').state_claim = 'probably fine'; // junk that must not read as 'none'
          localStorage.setItem(FieldGoldData.KEY, JSON.stringify(rec));
        }""")
        page.goto(base + "/map.html", wait_until="load")
        page.wait_for_timeout(600)
        marks = page.evaluate(DIAMONDS)
        pop = {}
        for d in marks:
            mm = re.search(r"<b>(?:Profile )?(REM-\d+|\d+)</b>", d["popup"])
            if mm:
                pop[mm.group(1)] = d

        check("  all four damaged records still drew", all(k in pop for k in
              ("REM-2", "REM-7", "REM-13", "REM-14")), sorted(pop))
        check("  a record with NO state_claim reads NOT CHECKED",
              UNCHECKED_LABEL in pop["REM-2"]["popup"]
              and NONE_LABEL not in pop["REM-2"]["popup"],
              claim_slice(pop["REM-2"]["popup"])[:160])
        check("  ...even though its land_status is CLEAN",
              "CLEAN" in pop["REM-2"]["popup"])
        check("  a record with junk in the field reads NOT CHECKED, not 'none'",
              UNCHECKED_LABEL in pop["REM-14"]["popup"]
              and NONE_LABEL not in pop["REM-14"]["popup"],
              claim_slice(pop["REM-14"]["popup"])[:160])
        check("  an undated answer SAYS it is undated rather than omitting it",
              "no check date on this record" in pop["REM-7"]["popup"],
              claim_slice(pop["REM-7"]["popup"])[:160])
        check("  a CLAIMED bench says so in words",
              CLAIMED_LABEL in pop["REM-13"]["popup"],
              claim_slice(pop["REM-13"]["popup"])[:160])
        check("  ...and does NOT also claim the ground is clear",
              NONE_LABEL not in pop["REM-13"]["popup"]
              and "22 active state claims sit in this reach"
              not in claim_slice(pop["REM-13"]["popup"]))
        # The whole point of the second register: the diamond is coloured by
        # land status and stays CLEAN, while the popup says a claim covers it.
        icon = pop["REM-13"]["opts"]["icon"]["html"]
        check("  ...while its land-status diamond stays CLEAN (registers unmerged)",
              CLEAN_GREEN in icon and "CLEAN" in pop["REM-13"]["popup"], icon[:120])

        # --------------------------------------------------------------
        # 6. The number nobody measured is not printed.
        # --------------------------------------------------------------
        print("\n6. no fabricated distance to a claim, anywhere")
        offenders = []
        for d in marks:
            sl = claim_slice(d["popup"])
            hit = DISTANCE_RE.search(sl)
            if hit:
                offenders.append((d["popup"][:40], hit.group(0), sl[:140]))
        check("  no bench popup prints a distance inside its claim line",
              not offenders, offenders[:1])
        check("  the popups say in words that proximity was never measured",
              all("never measured" in claim_slice(d["popup"])
                  for d in marks if NONE_LABEL in d["popup"]))
        check("  map.html says the same thing at page level",
              "does not know how near" in map_txt and "not measured" in map_txt)
        check("  ...and points the reader at Alaska Mapper for it",
              "Alaska Mapper" in map_txt)
        check("  no source file emits state_claim_proximity as a rendered value",
              "state_claim_proximity" not in map_txt,
              "the field exists to be absent from the screen, not to be printed")

        browser.close()

    httpd.shutdown()

    # ------------------------------------------------------------------
    # 7. The page-level panel, and the cache bump that ships it.
    # ------------------------------------------------------------------
    print("\n7. the register is named, counted and dated on the map")
    panel_i = map_txt.find('id="state-register"')
    check("  map.html carries the #state-register panel", panel_i > 0)
    panel = map_txt[panel_i:panel_i + 1400] if panel_i > 0 else ""
    for needle, why in [("2026-07-25", "the date it was counted"),
                        ("22", "the active count"),
                        ("ME112", "the active layer"),
                        ("ME13", "the pending layer"),
                        ("None of the 20", "that no bench is inside one"),
                        ("goes stale", "that the snapshot expires")]:
        check("  the panel states %s" % why, needle in panel, panel[:120])
    check("  the panel sits next to the FEDERAL note it corrects",
          0 < map_txt.find("BLM") < panel_i)

    # Version READ, not named. This check used to pin the literal string
    # 'fieldgold-v4', and 0009 is what proved that wrong: bumping the cache to
    # v5 to actually deliver a map.html fix turned a correct bump into a red
    # test, which trains the next person to edit the assertion instead of
    # thinking. test_offline_map.py and test_stage_maps.py had already learned
    # this and left comments saying so; this was the last pinned one.
    #
    # The claim being made is NOT "the version is 4". It is: the sequence that
    # actually reached a device is v1, v2, v3 — the per-change-set numbering of
    # the withdrawn stack was never published — so anything past v3 means
    # somebody bumped it deliberately, and the reason is written down above the
    # declaration (asserted separately, just below).
    _cv = re.search(r"const CACHE = 'fieldgold-v(\d+)';", sw)
    check("  sw.js declares a cache version",
          bool(_cv), sw[sw.find("const CACHE"):][:48])
    check("  sw.js is past v3 — the last version that reached a device without land status",
          bool(_cv) and int(_cv.group(1)) > 3,
          _cv.group(0) if _cv else None)
    # The whole comment block above the declaration, not a fixed window of it.
    # The note used to be one paragraph per change set and a 700-character
    # window reached all of it; the collapsed note is one release covering seven
    # changes, so a window that size lands in the middle and reads nothing. What
    # matters is that the reason is written down and is specific enough to judge
    # — the register named, the count, and the date it expires against.
    bump_note = sw[:sw.find("const CACHE")]
    for needle, why in [("state claim", "names the state register"),
                        ("22 active", "carries the measured count"),
                        ("2026-07-25", "dates the count")]:
        check("  the bump note %s" % why, needle in bump_note.lower(),
              bump_note[-200:])

    print("")
    print("%d passed, %d failed" % (PASS, len(FAILS)))
    if FAILS:
        print("FAILED: " + ", ".join(FAILS))
        sys.exit(1)
    print("STATE-CLAIM REGISTER SUITE PASSED")


if __name__ == "__main__":
    main()
