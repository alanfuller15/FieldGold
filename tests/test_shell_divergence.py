#!/usr/bin/env python3
"""The Pages build and the iOS shell must not diverge silently.

WHY THIS SUITE EXISTS.

Three defects reached a physical iPhone in one day, and they share a shape:
CORRECT ON GITHUB PAGES, BROKEN IN THE IOS SHELL, NOTHING REPORTED ON SCREEN.
Not a bug in either distribution — a divergence between them, failing silently,
which is why none was found before a device existed.

  1. `sw.js` is the whole update path on Pages; `navigator.serviceWorker` does
     not exist under `capacitor://localhost`, so it never registers.
  2. `target="_blank"` opens a tab on Pages; in the shell the popup delegate
     hands a `capacitor://` URL to `UIApplication.shared.open()`, iOS refuses
     the scheme, and the tap does NOTHING AT ALL.
  3. Safe-area insets are irrelevant to a browser tab; the shell's webview is
     full-bleed and `env()` read 0 for want of `viewport-fit=cover`.

Defect 2 is what this suite was opened for, because it was the worst: `map.html`
was referenced EXACTLY ONCE in `index.html` and that reference was the dead
anchor. No other link, no `location.href`, no `window.open`. So on a phone the
primary field tool — the only field map screen, the one carrying the land-status
colours — could not be opened at all. A person holding this app on the ground
had the launcher and nothing else.

WHAT IT CANNOT DO. Everything here runs in Chromium. Chromium is not WKWebView:
it has no popup delegate, no `capacitor://` scheme and no native chrome. This
suite cannot prove the fix works in the shell — the device did that, before the
fix was written, by navigating with `location.href` in the Web Inspector. What
it CAN do is hold the shape of the fix: that the three internal links stay
attribute-free, that the NINE working external ones keep the attribute they
need, and that every page you can navigate to has a way back.

THE BLANKET STRIP IS THE MISTAKE THIS SUITE EXISTS TO CATCH. Of 12
`target="_blank"` anchors in `index.html`, only 3 were internal and dead. The
other 9 are `https://` and work BECAUSE of it, established on the device by a
control test on the same anchor pattern through the same delegate under the same
gesture. Two of the nine are template-interpolated, so no static rule about
relative hrefs can be trusted either. Fix links by href; never by the attribute.

EXIT CONVENTION: INVERTED under --mutate, matching test_offline_map.py and
test_panel_reachability.py — caught -> 0, SURVIVED -> 1. Plain runs are the
normal 0/1. CLAUDE.md's table records which suites invert; do not trust it
without running one.

  python3 tests/test_shell_divergence.py
  python3 tests/test_shell_divergence.py --mutate blank-back
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
ROOT = REPO / "docs"
MUTATE = sys.argv[sys.argv.index("--mutate") + 1] if "--mutate" in sys.argv else None

# The three that were dead. Each is reachable from the Field tools sheet and
# each is a same-origin page in this bundle.
INTERNAL_CARDS = ["map.html", "bench_hunter.html", "creek_manual.html"]
# Measured on the tree 2026-07-28 and again 2026-07-29: 12 anchors carried the
# attribute, 3 internal and 9 external. If this number moves, a link was added
# or removed and somebody has to say which.
EXPECTED_EXTERNAL_BLANK = 9

# iPhone 14 portrait — the device every measurement in STATE.md was taken on.
SA_TOP, SA_BOTTOM = 47, 34
INJECT = (":root{--sa-top:%dpx;--sa-bottom:%dpx;--sa-left:0px;--sa-right:0px}"
          % (SA_TOP, SA_BOTTOM))

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
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def mutate(root):
    """A mutant that matches nothing must ABORT. A green run against unmutated
    code reads as proof and is worse than no mutation testing at all."""
    def edit(relpath, a, b):
        p = root / relpath
        s0 = p.read_text(encoding="utf-8")
        s = s0.replace(a, b)
        if s == s0:
            print("mutant " + MUTATE + " did not match " + relpath
                  + "; refusing to report a pass on an unmutated tree")
            sys.exit(2)
        p.write_text(s, encoding="utf-8")

    if MUTATE == "blank-back":
        # Put the shipped defect back on the one link that matters most.
        edit("index.html", '<a class="card tappable" href="map.html"',
             '<a class="card tappable" href="map.html" target="_blank" rel="noopener"')
    elif MUTATE == "strip-all-blank":
        # THE BLANKET STRIP. Fixes the three dead links by breaking the nine
        # working ones — the exact wrong fix, made assertable.
        edit("index.html", ' target="_blank" rel="noopener"', '')
    elif MUTATE == "no-back-link":
        # Reachable, and a one-way trip: nothing goes back to the launcher and
        # the shell provides no gesture that would.
        edit("map.html", '<a class="fg-back" href="index.html">', '<a class="fg-back">')
    elif MUTATE == "back-at-top":
        # Move the bar into the status-bar strip, where elementFromPoint would
        # report it reachable and a finger would not reach it.
        edit("fieldgold-chrome.css",
             "position:fixed;left:0;right:0;bottom:0;", "position:fixed;left:0;right:0;top:0;")
    elif MUTATE == "no-bottom-inset":
        # The bar renders under the home indicator.
        edit("fieldgold-chrome.css",
             "padding:0 calc(12px + var(--sa-right,0px)) var(--sa-bottom,0px) "
             "calc(12px + var(--sa-left,0px));",
             "padding:0 12px 0 12px;")
    elif MUTATE == "chrome-uncached":
        # Shipped, works on the desk, and gone on the first phone that installs
        # from a cold cache: the back bar loses its stylesheet.
        edit("sw.js", "  './fieldgold-chrome.css',\n", "")
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

    print("shell divergence suite  " + str(root)
          + ("  MUTANT=%s" % MUTATE if MUTATE else ""))

    idx = (root / "index.html").read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # 1. The three internal cards navigate in the webview.
    # ------------------------------------------------------------------
    print("[1] the three internal links carry no target")
    for href in INTERNAL_CARDS:
        m = re.search(r'<a class="card tappable" href="%s"[^>]*>' % re.escape(href), idx)
        check("index.html links %s with no target attribute" % href,
              bool(m) and "target=" not in m.group(0),
              m.group(0)[:160] if m else "no card anchor for " + href)

    # ------------------------------------------------------------------
    # 2. And the nine that work still do. This is the half a "helpful"
    #    cleanup deletes.
    # ------------------------------------------------------------------
    print("[2] the nine external links keep the attribute they need")
    anchors = re.findall(r'<a\b[^>]*target="_blank"[^>]*>', idx)
    hrefs = [re.search(r'href="([^"]*)"', a).group(1) for a in anchors
             if re.search(r'href="([^"]*)"', a)]
    check("exactly %d anchors still carry target=\"_blank\" (was 12: 3 internal "
          "and dead, 9 external and working)" % EXPECTED_EXTERNAL_BLANK,
          len(anchors) == EXPECTED_EXTERNAL_BLANK,
          {"count": len(anchors), "hrefs": hrefs})
    check("none of them is an internal page — a relative href on this "
          "attribute is a dead link in the shell",
          all(h.startswith("https://") or h.startswith("${") for h in hrefs),
          [h for h in hrefs if not (h.startswith("https://") or h.startswith("${"))])
    check("the interpolated ones are still there (two of the nine are "
          "${st.link}/${st.link2}, so no static rule about relative hrefs is "
          "safe — fix links by href, never by the attribute)",
          sum(1 for h in hrefs if h.startswith("${")) == 2,
          [h for h in hrefs if h.startswith("${")])

    # ------------------------------------------------------------------
    # 3. Every page you can now navigate to has a way back.
    # ------------------------------------------------------------------
    print("[3] every tool page carries the same way back")
    for f in INTERNAL_CARDS:
        s = (root / f).read_text(encoding="utf-8")
        check("%s links the shared chrome stylesheet" % f,
              'href="fieldgold-chrome.css"' in s)
        check("%s has a back link to index.html" % f,
              bool(re.search(r'<a class="fg-back" href="index\.html"', s)),
              "no fg-back anchor")
    sw = (root / "sw.js").read_text(encoding="utf-8")
    shell_src = re.search(r"const SHELL = \[(.*?)\];", sw, re.S)
    shell = re.findall(r"'([^']+)'", shell_src.group(1)) if shell_src else []
    check("sw.js caches the chrome stylesheet — uncached, the back bar loses "
          "its styling on the first cold-cache install",
          "./fieldgold-chrome.css" in shell, shell)

    # ------------------------------------------------------------------
    # 4. In a browser. Chromium is NOT WKWebView — this cannot prove the shell
    #    behaviour, only that the same-window navigation is what the markup
    #    now asks for, and that the way back works.
    # ------------------------------------------------------------------
    print("[4] navigation in a browser (Chromium, NOT the shell — see docstring)")
    httpd, port = serve(root)
    base = "http://127.0.0.1:%d" % port
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 390, "height": 844})
        page = ctx.new_page()
        page.route("**/*", lambda route, req:
                   route.continue_() if req.url.startswith(base) else route.abort())

        popups = []
        ctx.on("page", lambda pg: popups.append(pg.url))

        page.goto(base + "/index.html", wait_until="load")
        page.wait_for_timeout(600)
        page.evaluate("() => openTools()")
        page.wait_for_timeout(300)
        page.click('a.card.tappable[href="map.html"]')
        page.wait_for_timeout(1200)
        check("tapping the Gold map card navigates THIS page to map.html "
              "(the whole defect was that it did nothing at all)",
              page.url.endswith("/map.html"), page.url)
        check("  ...and opens no second page — a popup is the path that dies in "
              "the shell", not popups, popups)

        page.add_style_tag(content=INJECT)
        page.wait_for_timeout(200)
        back = page.evaluate("""() => {
            const a = document.querySelector('a.fg-back');
            if (!a) return null;
            const r = a.getBoundingClientRect();
            const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
            const hit = document.elementFromPoint(cx, cy);
            return {top: r.top, bottom: r.bottom, h: r.height, w: r.width,
                    vh: window.innerHeight,
                    hit: hit ? (hit.closest('a.fg-back') ? 'fg-back' : hit.tagName) : null}; }""")
        check("map.html: the back control exists and is at the BOTTOM, not in "
              "the status-bar strip (top=%s of %s)"
              % (back and back["top"], back and back["vh"]),
              bool(back) and back["top"] > back["vh"] / 2, back)
        check("map.html: it is at least a 44x44 tap target (%sx%s)"
              % (back and back["w"], back and back["h"]),
              bool(back) and back["h"] >= 44 and back["w"] >= 44, back)
        check("map.html: it clears the home indicator (bottom=%s, must be <= "
              "%s)" % (back and back["bottom"], (back and back["vh"]) and back["vh"] - SA_BOTTOM),
              bool(back) and back["bottom"] <= back["vh"] - SA_BOTTOM + 0.5, back)
        # A hit test is meaningful HERE and would not be at the top: the blind
        # spot is native chrome composited above the webview, and that is the
        # status bar. The home indicator does not eat touches the same way.
        check("map.html: the back control wins its own hit test",
              bool(back) and back["hit"] == "fg-back", back)

        # The bar must not be able to cover panel text — the failure a floating
        # control would have reintroduced. The sheet ends above the bar.
        # EVERY EVALUATION BELOW RETURNS null RATHER THAN THROWING ON A MISSING
        # ELEMENT, and the click is guarded. The blank-back mutant restores
        # target="_blank" on the map card; in Chromium that opens a POPUP and
        # leaves this page on index.html, where #panel and a.fg-back do not
        # exist. The first version threw a TypeError out of the harness and the
        # run exited 1 with ZERO reported failures — which under this suite's
        # inverted convention reads as MUTANT SURVIVED. A suite that crashes
        # where it should fail hides every assertion after it, and here it hid
        # the single most important one.
        gap = page.evaluate("""() => {
            const p = document.querySelector('#panel');
            const c = document.querySelector('.fg-chrome');
            if (!p || !c) return null;
            p.classList.remove('collapsed');
            return {panelBottom: p.getBoundingClientRect().bottom,
                    barTop: c.getBoundingClientRect().top}; }""")
        page.wait_for_timeout(300)
        gap = page.evaluate("""() => {
            const p = document.querySelector('#panel');
            const c = document.querySelector('.fg-chrome');
            if (!p || !c) return null;
            return {panelBottom: p.getBoundingClientRect().bottom,
                    barTop: c.getBoundingClientRect().top}; }""") or gap
        check("map.html: the expanded panel ends above the chrome bar, so the "
              "bar cannot cover warning text (%s)" % gap,
              bool(gap) and gap["panelBottom"] <= gap["barTop"] + 0.5, gap)

        if page.query_selector("a.fg-back"):
            page.click("a.fg-back")
            page.wait_for_timeout(900)
        check("map.html: the back control returns to the launcher",
              page.url.endswith("/index.html"), page.url)

        for f in ["bench_hunter.html", "creek_manual.html"]:
            page.goto(base + "/" + f, wait_until="load")
            page.wait_for_timeout(500)
            page.add_style_tag(content=INJECT)
            page.wait_for_timeout(150)
            b = page.evaluate("""() => {
                const a = document.querySelector('a.fg-back');
                if (!a) return null;
                const r = a.getBoundingClientRect();
                const hit = document.elementFromPoint(r.left + r.width/2, r.top + r.height/2);
                return {top: r.top, bottom: r.bottom, h: r.height, vh: window.innerHeight,
                        hit: hit ? (hit.closest('a.fg-back') ? 'fg-back' : hit.tagName) : null}; }""")
            check("%s: back control at the bottom, >=44px, clears the home "
                  "indicator, wins its hit test" % f,
                  bool(b) and b["top"] > b["vh"] / 2 and b["h"] >= 44
                  and b["bottom"] <= b["vh"] - SA_BOTTOM + 0.5 and b["hit"] == "fg-back", b)
            if page.query_selector("a.fg-back"):
                page.click("a.fg-back")
                page.wait_for_timeout(900)
            check("%s: the back control returns to the launcher" % f,
                  page.url.endswith("/index.html"), page.url)

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
