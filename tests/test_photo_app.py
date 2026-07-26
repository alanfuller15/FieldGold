"""End-to-end check that the photo analyser actually carries land status.

The node suite proves contextForPoint() and landBriefForPrompt() behave. It
cannot prove index.html USES them. A build that computes a perfect land-status
context and then sends the bare VISION_PROMPT anyway would pass every unit
test and still tell a person standing inside a closing order where to put
their first pan.

So this drives the real page in a real browser engine, with window.fetch
stubbed so nothing leaves the machine and no API key is needed. It reads:

  * what was actually POSTed to api.anthropic.com, and
  * what is actually on the screen, on every path including the failure ones.

Requires: playwright + chromium (preinstalled). No network.

  python3 tests/test_photo_app.py
  python3 tests/test_photo_app.py --mutate no-brief    (prove it can fail)
"""
import base64
import functools
import http.server
import json
import pathlib
import socketserver
import sys
import threading

# Resolve the repo from THIS file, not the cwd.
ROOT = pathlib.Path(__file__).resolve().parent.parent
MUTATE = sys.argv[sys.argv.index("--mutate") + 1] if "--mutate" in sys.argv else None

PASS, FAILS = 0, []


def check(name, cond, detail=""):
    global PASS
    if cond:
        PASS += 1
        print(f"  ok    {name}")
    else:
        FAILS.append(name)
        print(f"  FAIL  {name}" + (f"  -- {detail}" if detail else ""))


def serve(directory):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(directory))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


# A 1x1 png. The stub never looks at it; it only has to be a valid data URL.
PNG = ("data:image/png;base64,"
       "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")

# The stub's canned model reply — deliberately a DISOBEDIENT one. It ignores
# the refusal instruction and hands out pan advice anyway, because that is the
# case the banner exists to cover. If the app only worked when the model
# complied, it would not be a safety control.
CANNED = """VERDICT: Promising
WHERE TO START: The gravel wedged in the bedrock crack at centre-left.
WHY: Classic trap geometry below a gradient break.
ALSO CHECK: The bar tail downstream.
LOOK CLOSER AT: The bank above the waterline.
CAUTION: Photo only shows one bank.
INDICATORS:
trap=strong
bedrock=moderate
blacksand=weak
gradient=moderate
bench=yes"""

STUB = """
(() => {
  window.__calls = [];
  window.fetch = async (url, opts) => {
    window.__calls.push({ url: String(url), body: opts && opts.body ? String(opts.body) : '' });
    if (window.__failMode === 'http') {
      return { ok: false, status: 401, json: async () => ({ error: { message: 'nope' } }) };
    }
    if (window.__failMode === 'net') { throw new Error('offline'); }
    return { ok: true, status: 200, json: async () => ({
      content: [{ type: 'text', text: %s }] }) };
  };
})();
""" % json.dumps(CANNED)


def main():
    from playwright.sync_api import sync_playwright

    root = ROOT
    if MUTATE:
        # Mutants operate on a throwaway copy of the repo, never on the real one.
        import shutil
        import tempfile
        root = pathlib.Path(tempfile.mkdtemp()) / "repo"
        shutil.copytree(ROOT, root)
        idx = root / "index.html"
        s = idx.read_text(encoding="utf-8")
        if MUTATE == "no-brief":
            # Send the bare prompt: compute the context, then ignore it.
            s = s.replace("(land && FieldGoldData.landBriefForPrompt\n"
                          "                                    ? FieldGoldData.landBriefForPrompt(land) : '') + VISION_PROMPT",
                          "VISION_PROMPT")
        elif MUTATE == "no-banner":
            s = s.replace("function landBanner(ctx) {\n  if (!ctx) return '';",
                          "function landBanner(ctx) {\n  if (ctx) return '';")
        elif MUTATE == "banner-only-on-success":
            s = s.replace("results.innerHTML = landBanner(land) + `<div class=\"card\" "
                          "style=\"border-color:var(--rust);\"><p class=\"small\" "
                          "style=\"color:var(--rust);font-weight:700;margin-bottom:6px;\">Connection failed</p>",
                          "results.innerHTML = `<div class=\"card\" "
                          "style=\"border-color:var(--rust);\"><p class=\"small\" "
                          "style=\"color:var(--rust);font-weight:700;margin-bottom:6px;\">Connection failed</p>")
        elif MUTATE == "stale-gps":
            s = s.replace("gps,\n      land,", "gps: window._pendingGps || null,\n      land,")
        else:
            print("unknown mutant: " + MUTATE)
            sys.exit(2)
        idx.write_text(s, encoding="utf-8")

    httpd, port = serve(root)
    base = f"http://127.0.0.1:{port}"
    print(f"photo land-status app suite  serving {root} on {base}"
          + (f"  MUTANT={MUTATE}" if MUTATE else ""))

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context()
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # -----------------------------------------------------------------
        # 0. Load the real bench data the way he would, so the context has
        #    something to work from. Same origin => same localStorage.
        # -----------------------------------------------------------------
        page.goto(f"{base}/load_rem_benches.html", wait_until="load")
        page.get_by_text("Load all 20 with status").click()
        counts = page.evaluate("() => FieldGoldData.statusCounts(FieldGoldData.get('bench'))")
        check("bench data loaded: 8 clean / 0 unchecked / 12 avoid",
              (counts["clean"], counts["unchecked"], counts["avoid"]) == (8, 0, 12),
              json.dumps(counts))

        avoid = page.evaluate(
            "() => FieldGoldData.get('bench').filter(b => FieldGoldData.isAvoid(b))[0]")
        clean = page.evaluate(
            "() => FieldGoldData.get('bench').filter(b => FieldGoldData.statusOf(b)==='clean')[0]")

        page.goto(f"{base}/index.html", wait_until="load")
        page.add_script_tag(content=STUB)
        page.evaluate("() => { S.apiKey = 'sk-ant-test'; switchView('photo'); }")

        # -----------------------------------------------------------------
        # 1. A photo taken ON a known-encumbered bench.
        # -----------------------------------------------------------------
        page.evaluate(
            "async ([lat, lon, png]) => { window._pendingGps = {lat, lon, acc: 5};"
            " await analyzePhoto(png, 'image/png'); }",
            [avoid["lat"], avoid["lon"], PNG])

        body = page.evaluate("() => window.__calls[0].body")
        url = page.evaluate("() => window.__calls[0].url")
        check("the request went to the Anthropic messages endpoint",
              "api.anthropic.com/v1/messages" in url, url)
        check("the prompt carries a LAND STATUS block",
              "LAND STATUS AT THIS POSITION" in body)
        check("the prompt states AVOID for this position",
              "AVOID" in body and "encumbered ground" in body,
              body[body.find("LAND STATUS"):][:160] if "LAND STATUS" in body else "(absent)")
        check("the prompt forbids WHERE TO START on this ground",
              "Do NOT output a WHERE TO START section" in body)
        check("the prompt forbids naming a spot to dig",
              "spot to put a pan, dig, or sample" in body)
        check("the prompt forbids a workaround",
              "do not speculate that it might not apply" in body)
        check("the encumbrance itself is quoted to the model",
              (avoid.get("status_label") or "")[:24] in body,
              (avoid.get("status_label") or "")[:40])

        # The model DISOBEYED and gave pan advice anyway. The screen must
        # still carry the warning -- that is the whole point of the banner.
        page.evaluate("() => openPhoto(S.photos[0].id)")
        modal = page.evaluate(
            "() => document.querySelector('.modal, #modal, [id*=modal]')"
            "        ? document.body.innerText : document.body.innerText")
        check("the model's reply did contain pan advice (the case being covered)",
              "WHERE TO START" in page.evaluate("() => S.photos[0].analysis"))
        check("the screen still shows AVOID for this photo",
              "AVOID" in modal and "encumbered ground" in modal,
              modal[:200])
        check("the stored photo record carries the land context",
              page.evaluate("() => S.photos[0].land && S.photos[0].land.tier") == "near_avoid")
        check("the stored context refuses advice",
              page.evaluate("() => S.photos[0].land.advice") is False)
        page.evaluate("() => closeModal()")

        # Copied text must carry the warning out of the app with it.
        # navigator.clipboard is a read-only accessor in Chromium: a plain
        # assignment fails silently and the capture stays null, which reads as
        # a product bug rather than a broken stub. defineProperty is required.
        copied = page.evaluate("""() => {
            window.__copied = null;
            Object.defineProperty(navigator, 'clipboard', {
                configurable: true,
                value: { writeText: t => { window.__copied = t; return Promise.resolve(); } }
            });
            copyPhoto(S.photos[0].id);
            return window.__copied;
        }""")
        check("copied analysis leads with the encumbrance",
              copied is not None and copied.strip().startswith("AVOID"),
              (copied or "")[:80])

        # -----------------------------------------------------------------
        # 2. A photo taken near a CLEAN bench must not read as clean.
        # -----------------------------------------------------------------
        page.evaluate("() => { window.__calls = []; }")
        page.evaluate(
            "async ([lat, lon, png]) => { window._pendingGps = {lat, lon, acc: 5};"
            " await analyzePhoto(png, 'image/png'); }",
            [clean["lat"] + 0.0009, clean["lon"], PNG])  # ~100 m north
        b2 = page.evaluate("() => window.__calls[0].body")
        check("100 m from a clean bench does NOT tell the model the ground is clear",
              "UNKNOWN, not clear" in b2)
        check("  ...and does not forbid advice there either",
              "Do NOT output a WHERE TO START section" not in b2)
        check("  ...and the tier stored is near_clean, not clean",
              page.evaluate("() => S.photos[0].land.tier") == "near_clean")
        check("  ...and the screen says NOT CHECKED HERE",
              "NOT CHECKED HERE" in page.evaluate("() => document.body.innerText"))

        # -----------------------------------------------------------------
        # 3. No GPS at all.
        # -----------------------------------------------------------------
        page.evaluate("() => { window.__calls = []; }")
        page.evaluate("async (png) => { window._pendingGps = null;"
                      " await analyzePhoto(png, 'image/png'); }", PNG)
        b3 = page.evaluate("() => window.__calls[0].body")
        check("with no GPS the model is told status is unknown",
              "NO LOCATION" in b3 and "UNKNOWN, not clear" in b3)
        check("with no GPS the screen says so",
              "NO LOCATION" in page.evaluate("() => document.body.innerText"))
        check("with no GPS the tier is no_position",
              page.evaluate("() => S.photos[0].land.tier") == "no_position")

        # -----------------------------------------------------------------
        # 4. The banner must survive both failure paths. An HTTP error or a
        #    dead connection is exactly when a person is standing outside
        #    with no answer -- the warning must not vanish with the result.
        # -----------------------------------------------------------------
        page.evaluate("() => { window.__failMode = 'http'; }")
        page.evaluate(
            "async ([lat, lon, png]) => { window._pendingGps = {lat, lon, acc: 5};"
            " await analyzePhoto(png, 'image/png'); }",
            [avoid["lat"], avoid["lon"], PNG])
        txt = page.evaluate("() => document.getElementById('photo-results').innerText")
        check("on a 401 the failure is reported", "Analysis failed" in txt)
        check("on a 401 the AVOID banner is still on screen",
              "AVOID" in txt and "encumbered ground" in txt, txt[:160])

        page.evaluate("() => { window.__failMode = 'net'; }")
        page.evaluate(
            "async ([lat, lon, png]) => { window._pendingGps = {lat, lon, acc: 5};"
            " await analyzePhoto(png, 'image/png'); }",
            [avoid["lat"], avoid["lon"], PNG])
        txt = page.evaluate("() => document.getElementById('photo-results').innerText")
        check("on a dead connection the failure is reported", "Connection failed" in txt)
        check("on a dead connection the AVOID banner is still on screen",
              "AVOID" in txt and "encumbered ground" in txt, txt[:160])
        page.evaluate("() => { window.__failMode = null; }")

        # -----------------------------------------------------------------
        # 5. A second photo started while the first is in flight must not
        #    steal the first one's location.
        # -----------------------------------------------------------------
        page.evaluate("() => { S.photos = []; window.__calls = []; }")
        stolen = page.evaluate(
            """async ([a, c, png]) => {
                 window._pendingGps = {lat: a.lat, lon: a.lon, acc: 5};
                 const p1 = analyzePhoto(png, 'image/png');
                 window._pendingGps = {lat: c.lat, lon: c.lon, acc: 5};
                 await p1;
                 return {tier: S.photos[0].land.tier, gps: S.photos[0].gps};
               }""", [avoid, clean, PNG])
        check("a location set mid-request does not overwrite the in-flight photo's",
              stolen["tier"] == "near_avoid", str(stolen["tier"]))
        # ...and the STORED gps must be the first photo's too. `land` is
        # snapshotted, but copyPhoto/openPhoto fall back to
        # landContextFor(p.gps) for records written before this change, so a
        # stale gps is a second, quieter route to the wrong banner.
        check("  ...and the stored gps is the first photo's, not the second's",
              stolen["gps"] is not None
              and abs(stolen["gps"]["lat"] - avoid["lat"]) < 1e-9
              and abs(stolen["gps"]["lon"] - avoid["lon"]) < 1e-9,
              str(stolen["gps"]))

        # -----------------------------------------------------------------
        # 6. A legacy photo record with no `land` field must not read as fine.
        # -----------------------------------------------------------------
        legacy_tier = page.evaluate(
            """([a]) => {
                 S.photos.unshift({ id: 'legacy1', thumb: '', analysis: 'old',
                   verdict: 'Promising', created: new Date().toISOString(),
                   gps: { lat: a.lat, lon: a.lon, acc: 9 } });
                 renderPhoto();
                 return document.getElementById('view-photo').innerText;
               }""", [avoid])
        check("a pre-land-status photo on encumbered ground still shows AVOID in the list",
              "AVOID" in legacy_tier, legacy_tier[:200])

        # -----------------------------------------------------------------
        # 7. The empty-device case: no bench records at all.
        # -----------------------------------------------------------------
        page.evaluate("() => { localStorage.removeItem('fieldgold_record');"
                      " S.photos = []; renderPhoto(); }")
        empty = page.evaluate("() => document.getElementById('view-photo').innerText")
        check("with no bench data the page says land status cannot be checked",
              "No land-status data on this device" in empty, empty[:200])

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
    print("PHOTO APP SUITE PASSED")


if __name__ == "__main__":
    main()
