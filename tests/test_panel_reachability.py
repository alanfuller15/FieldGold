#!/usr/bin/env python3
"""Adversarial test that the land-status notices can actually be READ, on the
device this app is carried on.

THE BUG THIS EXISTS BECAUSE OF.

Reported from the field-relevant device on 2026-07-26: "many features overlay
each other on the map... the leaflet banner at the bottom overlays it as well as
the zoom options and the toggle feature for the satellite streets topo."

Two separate defects, both measured before anything was changed:

  1. `#panel` was `z-index: 1000`. So are Leaflet's `.leaflet-top` and
     `.leaflet-bottom` CONTAINERS (vendor/leaflet/leaflet.css line 141) — the
     `800` on `.leaflet-control` only orders controls WITHIN those containers.
     A tie breaks by DOM order and `#map` comes after `#panel`, so the zoom and
     layers controls painted ON TOP of the claims warning.

  2. `#panel` had no `max-height` and no `overflow`, and `#map` is a
     full-viewport absolute element, so the body never scrolled. Every notice
     below the fold was PHYSICALLY UNREACHABLE. Measured by grid-sampling the
     warning-coloured text: 102 of 256 sample points on a 390x664 phone,
     118 of 250 on a 375x553 one. Zero on a 1440x900 desktop — which is why it
     shipped.

WHY THE OTHER ELEVEN SUITES DID NOT CATCH IT.

All of them read markup and data. Not one of them rendered a page at a phone
viewport and asked whether a human could reach a given sentence. Repo rules 4
and 5 say the land-status notices must not be removed or softened — "Do not
remove those notices as 'clutter'; they are the point." A notice you cannot
scroll to has been removed. Layout is a way of deleting text, and nothing was
watching for it.

WHAT THIS SUITE ASSERTS.

Reachability, measured, not a mandated CSS shape. For every page that has a
`#panel`, at phone viewports, it walks the panel's whole scroll range and asks
of every point inside warning-coloured text: at SOME scroll offset, is the
topmost element at that point panel content rather than a Leaflet control or
off-screen? It also asserts you can get back OUT of a full-screen panel, that
the primary action is reachable, and that the OSM attribution is visible when
the panel is collapsed.

WHAT IT DOES NOT PROVE.

Only two phone viewports and one desktop one are exercised, and only in
Chromium. It does not test a real iOS Safari, where the URL bar changes the
usable height mid-scroll — `100vh` there is the LARGEST height, so a panel sized
to it can sit slightly under the toolbar. It does not read the text, only
whether the pixels are reachable; a notice that is reachable and wrong still
passes.

Note on the stage maps: they pass today because their panels FIT (254-455px in a
664px viewport), not because they were fixed. They are still `z-index: 1000`
with no max-height. This suite will fail them the day one of those panels grows
past the fold, which is the point — but do not read a green run as "the stage
maps are safe."

  python3 tests/test_panel_reachability.py
  python3 tests/test_panel_reachability.py --repo /path/to/FieldGold
  python3 tests/test_panel_reachability.py --mutate z-1000   (prove it can fail)
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
if "--repo" in sys.argv:
    REPO = pathlib.Path(sys.argv[sys.argv.index("--repo") + 1]).expanduser().resolve()
# --repo still means the repo root, as it reads. The web root is docs/ under it,
# so that webDir points at a directory holding only web assets.
ROOT = REPO / "docs"
MUTATE = sys.argv[sys.argv.index("--mutate") + 1] if "--mutate" in sys.argv else None

if not (ROOT / "map.html").exists():
    print("no map.html under %s — pass --repo /path/to/FieldGold" % ROOT)
    sys.exit(2)

# The page carried into the field. Measured in full.
FIELD_PAGE = "map.html"
# Everything else with a #panel. Same reachability walk, phone viewport only.
OTHER_PANEL_PAGES = ["stage1_map_test.html", "stage2_map.html", "stage3_map.html",
                     "stage4_map.html", "stage5_map.html"]

PHONES = [("iPhone 14", 390, 664), ("iPhone SE", 375, 553)]
DESKTOP = ("desktop", 1440, 900)
# A laptop window shorter than the panel's content (~872px). Above 600px wide
# the mobile full-screen-sheet rules do not apply, so this is the ONLY viewport
# where the base `max-height` + `overflow-y` on #panel is what keeps the notices
# reachable. Without it the `no-maxheight` mutant survives, because on a phone
# the sheet's top:0/bottom:0 bounds the panel anyway and on a 900px desktop the
# content happens to fit.
SHORT_DESKTOP = ("short window", 1280, 620)

# The two colours a warning is written in. #D29A3A is the amber "this is not
# what it looks like" voice; #B2402F is the red avoid voice. Anything painted in
# these is a notice rules 4 and 5 protect.
WARN_COLOURS = ("rgb(210, 154, 58)", "rgb(178, 64, 47)")

# Rule 4 in assertable form. These are the sentences that stop someone digging
# on ground the map cannot see. If a future edit trims one as clutter, this list
# is what says no. Matched against the panel's rendered text with whitespace
# collapsed, so re-wrapping the source is free and deleting the sentence is not.
REQUIRED_NOTICES = [
    'not the same as "no claims."',
    "does not draw those 22 claims",
    "12 of the 20 are on encumbered ground",
    "It does not find open ground.",
]

PASS = 0
FAILS = []


def check(name, cond, detail=""):
    global PASS
    if cond:
        PASS += 1
        print("  ok    " + name)
    else:
        FAILS.append(name)
        print("  FAIL  " + name + ("  -- " + str(detail)[:240] if detail else ""))


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(directory):
    handler = functools.partial(Quiet, directory=str(directory))

    # Threaded on purpose. test_sw_lifecycle.py hung forever on a single-threaded
    # server when a page kept a socket busy; shutdown() never returned and the
    # suite reported nothing instead of the failure it had already found.
    class Threaded(socketserver.ThreadingTCPServer):
        daemon_threads = True
        block_on_close = False

    httpd = Threaded(("127.0.0.1", 0), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


# ----------------------------------------------------------------------------
# The measurement. Runs in the page.
#
# Points are recorded in the panel's own CONTENT coordinates (offset from the
# panel's scroll origin), so the same physical point can be re-tested at every
# scroll offset. A point is REACHABLE if at some offset it is inside the
# viewport AND document.elementFromPoint returns panel content there.
#
# `elementFromPoint` is used rather than getBoundingClientRect comparisons
# because it answers the question actually being asked: what does the user's eye
# and finger land on. Rect maths would say the panel and the control merely
# intersect; only a hit test says which one WON.
# ----------------------------------------------------------------------------
WALK = """() => {
  const el = document.querySelector('#panel');
  if (!el) return {noPanel: true};
  const isLeaflet = e => !!(e && e.closest && e.closest('.leaflet-control-container'));
  const inPanel   = e => !!(e && e.closest && e.closest('#panel'));

  // #status is excluded deliberately. It is the run log, and it has its own
  // 64px-tall scroller (.status{max-height:64px;overflow:auto}), so scrolling
  // the PANEL can never bring its lower lines into view — every line past the
  // first four would count as unreachable and the suite would fail forever on a
  // box that is working as designed. The one land-status claim the log makes
  // ("basemap tiles unavailable") is asserted in test_offline_map.py section 6,
  // against the log's text rather than its pixels.
  const warns = [...el.querySelectorAll('b,span,div')].filter(n => {
      if (n.closest('#status')) return false;
      if (![...n.childNodes].some(c => c.nodeType === 3 && c.textContent.trim())) return false;
      const c = getComputedStyle(n).color;
      return c === 'rgb(210, 154, 58)' || c === 'rgb(178, 64, 47)';
  });

  const pr0 = el.getBoundingClientRect();
  const pts = [];
  for (const w of warns) {
    const r = w.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    for (let y = r.y + 3; y < r.bottom - 2; y += 8)
      for (let x = r.x + 3; x < r.right - 2; x += 12)
        pts.push({cx: x - pr0.x + el.scrollLeft, cy: y - pr0.y + el.scrollTop});
  }

  const reachable = new Array(pts.length).fill(false);
  let coveredByControl = 0;

  // `el.scrollTop = n` SUCCEEDS on an overflow:hidden element in Chromium. A
  // walk that just sets scrollTop therefore proves the text is programmatically
  // addressable, not that a human can get to it — and the `no-overflow` mutant
  // survived on exactly that. The scroll range a USER has is zero unless the
  // computed overflow actually offers them a scroller.
  const oy = getComputedStyle(el).overflowY;
  const userScrollable = (oy === 'auto' || oy === 'scroll' || oy === 'overlay');
  const contentOverflows = el.scrollHeight > el.clientHeight + 1;
  const max = userScrollable ? Math.max(0, el.scrollHeight - el.clientHeight) : 0;
  const stops = [];
  for (let t = 0; t <= max; t += 40) stops.push(t);
  if (stops[stops.length - 1] !== max) stops.push(max);

  for (const t of stops) {
    el.scrollTop = t;
    const pr = el.getBoundingClientRect();
    pts.forEach((p, i) => {
      const x = pr.x + p.cx - el.scrollLeft, y = pr.y + p.cy - el.scrollTop;
      if (y < 0 || y > innerHeight || x < 0 || x > innerWidth) return;
      const e = document.elementFromPoint(x, y);
      if (isLeaflet(e)) { coveredByControl++; return; }
      if (inPanel(e)) reachable[i] = true;
    });
  }

  // Can you get back OUT? At the deepest scroll the collapse control must still
  // be on screen, or reading to the bottom traps you away from the map.
  el.scrollTop = max;
  const h1 = document.querySelector('#panel h1');
  const hr = h1.getBoundingClientRect();
  const hx = hr.x + hr.width - 14, hy = hr.y + hr.height / 2;
  const hitH1 = document.elementFromPoint(hx, hy);
  const collapseReachable = hr.top >= -1 && hr.bottom <= innerHeight + 1
                            && !!(hitH1 && hitH1.closest && hitH1.closest('#panel h1'));

  // The primary action and the run log, at whatever offset reaches them.
  const seen = {};
  for (const [key, sel] of Object.entries({scanBtn: '#findopen', statusBox: '#status'})) {
    const n = document.querySelector(sel);
    if (!n) { seen[key] = null; continue; }
    seen[key] = false;
    for (const t of stops) {
      el.scrollTop = t;
      const r = n.getBoundingClientRect();
      if (r.top >= -1 && r.bottom <= innerHeight + 1) { seen[key] = true; break; }
    }
  }
  el.scrollTop = 0;

  const n = pts.length, r = reachable.filter(Boolean).length;
  return {warnRuns: warns.length, points: n, reachable: r, unreachable: n - r,
          coveredByControl: coveredByControl, collapseReachable: collapseReachable,
          scrollRange: max, scrollStops: stops.length,
          overflowY: oy, userScrollable: userScrollable,
          contentOverflows: contentOverflows,
          panelH: Math.round(pr0.height), vh: innerHeight,
          collapsed: el.classList.contains('collapsed'),
          text: el.innerText.replace(/\\s+/g, ' ').trim(),
          scanBtn: seen.scanBtn, statusBox: seen.statusBox};
}"""

ATTRIB = """() => {
  const a = document.querySelector('.leaflet-control-attribution');
  if (!a) return {missing: true};
  const r = a.getBoundingClientRect();
  if (r.width < 2 || r.height < 2) return {zeroSize: true};
  const e = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
  return {visible: !!(e && e.closest && e.closest('.leaflet-control-attribution')),
          hit: e ? (e.className && e.className.toString().slice(0, 40)) || e.tagName : null};
}"""


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

    if MUTATE == "z-1000":
        # Defect 1, exactly as it shipped: tie with .leaflet-top, lose on DOM order.
        edit("map.html", "#panel{position:absolute;z-index:1200;",
             "#panel{position:absolute;z-index:1000;")
    elif MUTATE == "no-maxheight":
        # Defect 2a: the panel grows past the fold again.
        edit("map.html", "max-height:calc(100vh - 20px);overflow-y:auto;",
             "overflow-y:auto;")
    elif MUTATE == "no-overflow":
        # Defect 2b: bounded, but the overflow is clipped away instead of scrolled.
        edit("map.html", "max-height:calc(100vh - 20px);overflow-y:auto;",
             "max-height:calc(100vh - 20px);overflow-y:hidden;")
    elif MUTATE == "no-sticky":
        # Read to the bottom, and the way back to the map has scrolled off.
        edit("map.html", "#panel:not(.collapsed) h1{position:sticky;top:0;",
             "#panel:not(.collapsed) h1{top:0;")
    elif MUTATE == "trim-warning":
        # Rule 4, tested rather than trusted: delete a notice as "clutter".
        edit("map.html",
             '<b style="color:#D29A3A;">This layer is blank over Hatcher Pass, '
             'and that is not the same as "no claims."</b>', "")
    else:
        print("unknown mutant: " + MUTATE)
        sys.exit(2)


def load(ctx, base, page_name, width):
    page = ctx.new_page()
    page.route("**/*", lambda route, req:
               route.continue_() if req.url.startswith(base) else route.abort())
    page.goto(base + "/" + page_name, wait_until="load")
    page.wait_for_timeout(1500)
    return page


def expand(page):
    """map.html auto-collapses the panel under 600px. Expanding it is what Alan
    does and is the state the defect lives in, so the measurement has to do it
    too — a suite that measures the collapsed panel measures nothing."""
    if page.evaluate("() => document.querySelector('#panel')"
                     ".classList.contains('collapsed')"):
        page.click("#panel h1")
        page.wait_for_timeout(400)


def main():
    root = ROOT
    if MUTATE:
        tmp = pathlib.Path(tempfile.mkdtemp()) / "repo"
        shutil.copytree(ROOT, tmp)
        root = tmp
        mutate(root)

    print("panel reachability suite  " + str(root)
          + ("  MUTANT=%s" % MUTATE if MUTATE else ""))

    # ------------------------------------------------------------------
    # 0. The harness can see something. Every assertion below is of the form
    #    "none of the warning points is unreachable", which a page with no
    #    warning points satisfies perfectly. This is the empty-scope trap that
    #    has already produced one false green in this repo (test_sw_lifecycle
    #    asserted a cache EXISTED when a failed install leaves an empty one).
    # ------------------------------------------------------------------
    print("[0] the scope is not empty")
    src = (root / FIELD_PAGE).read_text(encoding="utf-8")
    n_amber = len(re.findall(r"#D29A3A", src))
    n_red = len(re.findall(r"#B2402F", src))
    check("map.html contains warning-coloured text at all (a page with no "
          "notices passes every reachability check below vacuously)",
          n_amber + n_red >= 4, "amber=%s red=%s" % (n_amber, n_red))

    httpd, port = serve(root)
    base = "http://127.0.0.1:%d" % port

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # --------------------------------------------------------------
        # 1-4. The field page, on a phone.
        # --------------------------------------------------------------
        for label, w, h in PHONES:
            print("[1] %s %dx%d — map.html, panel expanded" % (label, w, h))
            ctx = browser.new_context(viewport={"width": w, "height": h},
                                      device_scale_factor=2, is_mobile=True,
                                      has_touch=True)
            page = load(ctx, base, FIELD_PAGE, w)
            expand(page)
            d = page.evaluate(WALK)

            check("%s: the panel is expanded — the collapsed panel is not the "
                  "state the defect lives in" % label, not d["collapsed"], d)
            check("%s: warning text was found to test (%d runs, %d sample "
                  "points)" % (label, d["warnRuns"], d["points"]),
                  d["points"] >= 100, d)
            check("%s: the panel has more content than fits, so the scroll "
                  "assertions are not vacuous" % label,
                  d["scrollRange"] > 0, "scrollRange=%s" % d["scrollRange"])
            check("%s: the panel overflows AND offers the user a scroller "
                  "(overflow-y is %r) — clipped overflow reads as reachable to "
                  "a script and is not reachable to a finger"
                  % (label, d["overflowY"]),
                  not d["contentOverflows"] or d["userScrollable"], d["overflowY"])
            check("%s: NO land-status warning is unreachable — this is the "
                  "defect. 102 of 256 points were unreachable before the fix"
                  % label, d["unreachable"] == 0,
                  "%s of %s unreachable" % (d["unreachable"], d["points"]))
            check("%s: no Leaflet control paints over warning text at ANY "
                  "scroll offset (the z-index 1000 tie did exactly this)"
                  % label, d["coveredByControl"] == 0,
                  "%s covered hits" % d["coveredByControl"])
            check("%s: the panel never extends past the viewport" % label,
                  d["panelH"] <= d["vh"] + 1, "panelH=%s vh=%s" % (d["panelH"], d["vh"]))
            check("%s: the collapse control is still reachable at the deepest "
                  "scroll — otherwise reading to the bottom traps you off the "
                  "map" % label, d["collapseReachable"], d)
            check("%s: the scan button is reachable" % label, d["scanBtn"] is True, d["scanBtn"])
            check("%s: the status log is reachable" % label, d["statusBox"] is True, d["statusBox"])

            flat = d["text"]
            for notice in REQUIRED_NOTICES:
                check("%s: the notice %r is still on the page (rule 4)"
                      % (label, notice[:38]), notice in flat, flat[:160])

            # The panel may cover the attribution while it is being read — it is
            # a modal reading surface at this width. Collapsing it must give the
            # attribution back; OSM's licence is not satisfied by "it was there
            # before you tapped".
            page.evaluate("() => document.querySelector('#panel')"
                          ".classList.add('collapsed')")
            page.wait_for_timeout(300)
            a = page.evaluate(ATTRIB)
            check("%s: the OSM attribution is visible with the panel collapsed"
                  % label, a.get("visible") is True, a)

            page.close()
            ctx.close()

        # --------------------------------------------------------------
        # 5. Desktop: the layout that was always fine, asserted so it stays fine.
        # --------------------------------------------------------------
        label, w, h = DESKTOP
        print("[2] %s %dx%d — map.html" % (label, w, h))
        ctx = browser.new_context(viewport={"width": w, "height": h})
        page = load(ctx, base, FIELD_PAGE, w)
        expand(page)
        d = page.evaluate(WALK)
        check("desktop: no warning is unreachable", d["unreachable"] == 0,
              "%s of %s" % (d["unreachable"], d["points"]))
        check("desktop: no Leaflet control covers a warning",
              d["coveredByControl"] == 0, d["coveredByControl"])
        a = page.evaluate(ATTRIB)
        check("desktop: the OSM attribution is visible with the panel EXPANDED "
              "— at this width the panel does not need to cover it",
              a.get("visible") is True, a)
        page.close()
        ctx.close()

        # --------------------------------------------------------------
        # 5b. A desktop window too short for the content. No mobile rules
        #     apply here, so the base max-height/overflow is on its own.
        # --------------------------------------------------------------
        label, w, h = SHORT_DESKTOP
        print("[2b] %s %dx%d — no mobile rules, base max-height on its own" % (label, w, h))
        ctx = browser.new_context(viewport={"width": w, "height": h})
        page = load(ctx, base, FIELD_PAGE, w)
        expand(page)
        d = page.evaluate(WALK)
        check("short window: the content really does overflow here, or this "
              "section proves nothing", d["contentOverflows"], d["contentOverflows"])
        check("short window: the panel is bounded by the viewport",
              d["panelH"] <= d["vh"] + 1, "panelH=%s vh=%s" % (d["panelH"], d["vh"]))
        check("short window: the panel offers the user a scroller (overflow-y "
              "is %r)" % d["overflowY"], d["userScrollable"], d["overflowY"])
        check("short window: no warning is unreachable", d["unreachable"] == 0,
              "%s of %s" % (d["unreachable"], d["points"]))
        page.close()
        ctx.close()

        # --------------------------------------------------------------
        # 6. The other pages with a panel. These pass today because their
        #    panels FIT, not because they were fixed — they are still
        #    z-index 1000 with no max-height. This is the tripwire for the day
        #    one of them grows past the fold.
        # --------------------------------------------------------------
        print("[3] the stage maps — same walk, a tripwire not a warranty")
        label, w, h = PHONES[0]
        for name in OTHER_PANEL_PAGES:
            if not (root / name).exists():
                continue
            ctx = browser.new_context(viewport={"width": w, "height": h},
                                      device_scale_factor=2, is_mobile=True,
                                      has_touch=True)
            page = load(ctx, base, name, w)
            expand(page)
            d = page.evaluate(WALK)
            if d.get("noPanel"):
                page.close(); ctx.close()
                continue
            # The point count is in the assertion NAME, not hidden in the detail
            # that only prints on failure. A stage map with no warning text
            # passes this vacuously, and a green run has to say so out loud —
            # "ok ... (0 points)" is a different claim from "ok ... (87 points)".
            check("%s: no warning text is unreachable at %dx%d (%d points, "
                  "panel %dpx in %dpx)"
                  % (name, w, h, d["points"], d["panelH"], d["vh"]),
                  d["unreachable"] == 0,
                  "%s of %s unreachable" % (d["unreachable"], d["points"]))
            check("%s: no Leaflet control covers warning text" % name,
                  d["coveredByControl"] == 0, d["coveredByControl"])
            page.close()
            ctx.close()

        browser.close()
    httpd.shutdown()

    print()
    print("%d passed, %d failed" % (PASS, len(FAILS)))
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
