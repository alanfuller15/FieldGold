#!/usr/bin/env python3
"""Adversarial test for the SERVICE-WORKER TAKEOVER — the update path.

WHY THIS SUITE EXISTS.

Every other suite in `tests/` loads a page and asks whether the code is right.
None of them asks the question that decides whether a phone in the field ever
SEES that code: when a device is already holding cache `fieldgold-vN` and the
server starts serving `fieldgold-vN+1`, does the new worker install, activate,
delete the old cache, and take control of the page?

That question was driven by hand through Chrome DevTools on 2026-07-26 and it
could not be answered. Seven theories, each stated with a confidence level,
each falsified by the next measurement; the run ended with an ACTIVATED worker
holding ZERO caches, which is a state the shipped `sw.js` has no branch for —
`install` either resolves (and `fieldgold-vN` exists) or rejects (and the worker
goes redundant). Forty minutes of hand-driven archaeology produced a result no
branch of the code can produce, which means the instrument was wrong, not the
theory. This is the instrument.

The specific thing hand-driving CANNOT see: `install` fails inside the worker's
own `waitUntil` promise. `caches.addAll` rejects atomically — one 404 among
fifteen URLs and NOTHING is cached — and the rejection is not visible in the
page's console, not visible in `caches.keys()` (which just stays empty), and not
visible in the registration object (which reports the OLD worker, still fine).
So this suite probes every SHELL entry over HTTP itself and prints the status of
each one, which turns "the worker didn't install" into "the worker didn't
install BECAUSE ./vendor/leaflet/layers.png is 404".

WHAT IT DOES.

One HTTP server whose document root can be swapped mid-run — that is the whole
trick, and it is what makes this a takeover test rather than a first-install
test:

  1. serve the OLD tree, register the worker, wait for `activated`
  2. assert the OLD cache exists  (without this the suite has an empty scope —
     see step 5's note)
  3. swap the document root to the tree as it is in this repo, right now
  4. reload; the browser byte-compares `sw.js` and finds it changed
  5. assert the NEW cache exists, the OLD one is GONE, and the page is
     CONTROLLED by the new worker

WHAT "THE OLD TREE" IS, AND WHAT THAT COSTS.

It is a copy of this repo with `sw.js`'s CACHE constant rewritten to the
previous version number. It is NOT the real pre-patch checkout. That is a real
limitation and it is stated here rather than buried: this suite proves the
takeover mechanism works when the worker's bytes change, not that any specific
historical release upgrades cleanly. What it does buy is that it runs from a
bare clone with no git history, on any machine, identically.

WHAT IT STILL DOES NOT PROVE.

This harness is `http.server`: no `Cache-Control` header at all. GitHub Pages
sends `max-age=600`. Chromium has bypassed the HTTP cache for the worker's own
script since Chrome 68 (`updateViaCache` defaults to `imports`), so the update
check itself is not affected — but the SHELL assets fetched during `install`
are, and a green run here is not a promise about production. If a phone that
already has the app does not pick up the change, deleting and re-adding the
home-screen icon forces it. That sentence belongs in the release notes, not in
a comment nobody reads.

  python3 tests/test_sw_lifecycle.py
  python3 tests/test_sw_lifecycle.py --mutate no-skip-waiting
  python3 tests/test_sw_lifecycle.py --mutate no-activate-cleanup
  python3 tests/test_sw_lifecycle.py --mutate shell-404
  python3 tests/test_sw_lifecycle.py --mutate no-version-bump
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

# Defaults to the repo this file lives in. `--repo PATH` exists so the suite can
# be run from a kit directory against a repo it is not inside — which is how you
# test a tree you have not decided to commit to yet, without leaving an
# untracked file in a working tree you are about to push.
ROOT = pathlib.Path(__file__).resolve().parent.parent
if "--repo" in sys.argv:
    ROOT = pathlib.Path(sys.argv[sys.argv.index("--repo") + 1]).expanduser().resolve()
MUTATE = sys.argv[sys.argv.index("--mutate") + 1] if "--mutate" in sys.argv else None

if not (ROOT / "sw.js").exists():
    print("no sw.js under %s — pass --repo /path/to/FieldGold" % ROOT)
    sys.exit(2)

# The version the OLD tree pretends to be on. Any value that is not the current
# one works; v3 is used because that is what the device under investigation on
# 2026-07-26 was actually holding.
OLD_VERSION = "fieldgold-v3"

# How long to let a state transition happen before calling it a failure. The
# worker fetches fifteen shell files from a loopback server; this is generous
# on purpose, because a flaky timeout in a suite about caching would be read as
# a caching bug.
SETTLE_MS = 8000

PASS = 0
FAILS = []


def check(name, cond, detail=""):
    global PASS
    if cond:
        PASS += 1
        print("  ok    " + name)
    else:
        FAILS.append(name)
        print("  FAIL  " + name + ("  -- " + str(detail)[:300] if detail else ""))


# ---------------------------------------------------------------------------
# A server whose document root can be swapped while it is running.
#
# SimpleHTTPRequestHandler takes `directory` at construction time, and it is
# constructed per-request, so a mutable holder read inside __init__ is enough.
# This is the whole mechanism the suite is built on: same origin, same port,
# same registration, different bytes.
# ---------------------------------------------------------------------------
class Swappable(http.server.SimpleHTTPRequestHandler):
    holder = {"dir": None}
    sw_304 = []          # every 304 this server ever sent for sw.js

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(Swappable.holder["dir"]), **kw)

    def log_message(self, *a):
        pass

    # -- THE INSTRUMENT'S OWN BUG, FOUND BY RUNNING IT ----------------------
    # First run of this suite failed exactly the way Alan's phone-side
    # investigation failed: new tree served, worker never updated. Measured
    # cause, with the request logged:
    #
    #   REQ /sw.js  If-Modified-Since: <date>  ->  304   (serving the new tree)
    #
    # Chromium sends `If-Modified-Since` on the service-worker update fetch.
    # SimpleHTTPRequestHandler answers it from the file's MTIME — and
    # `shutil.copytree` preserves mtimes, so the new tree's sw.js is OLDER than
    # the old tree's rewritten one. The server said "not modified" about a file
    # whose bytes were completely different, and Chromium believed it. No
    # update, forever, with nothing on screen to say why.
    #
    # So the harness must not answer revalidation at all. Under a swapped
    # document root, mtime is not evidence about content.
    #
    # This is a HARNESS artifact, not a production risk, and the distinction
    # matters: GitHub Pages revalidates on ETag, which is derived from the
    # bytes, so a changed sw.js gets a 200 there no matter what any timestamp
    # says. It IS a live risk for anyone reproducing a version bump locally by
    # pointing `python3 -m http.server` at a different directory, which is
    # precisely what was being done by hand on 2026-07-26.
    def do_GET(self):
        del self.headers["If-Modified-Since"]
        del self.headers["If-None-Match"]
        super().do_GET()

    def send_response(self, code, message=None):
        if code == 304 and self.path.endswith("sw.js"):
            Swappable.sw_304.append(self.path)
        super().send_response(code, message)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def serve():
    # Threaded, and it has to be. Single-threaded, a worker whose `install` is
    # failing keeps the socket busy retrying and `shutdown()` never returns —
    # the suite hangs instead of reporting the failure it just caught. Found by
    # running --mutate shell-404, which is what mutants are for.
    class Threaded(socketserver.ThreadingTCPServer):
        daemon_threads = True
        block_on_close = False
    httpd = Threaded(("127.0.0.1", 0), Swappable)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def read_cache_version(tree):
    m = re.search(r"const CACHE = '([^']+)';", (tree / "sw.js").read_text(encoding="utf-8"))
    return m.group(1) if m else None


def read_shell(tree):
    src = re.search(r"const SHELL = \[(.*?)\];",
                    (tree / "sw.js").read_text(encoding="utf-8"), re.S)
    return re.findall(r"'([^']+)'", src.group(1)) if src else []


def edit(tree, relpath, a, b):
    """A mutation whose replace() matches nothing must ABORT. A green run
    against unmutated code reads as proof and is worse than no mutation test
    at all — this repo has already been bitten once (test_offline_map.py's
    sw-stale-cache went silently un-runnable for two releases)."""
    p = tree / relpath
    s0 = p.read_text(encoding="utf-8")
    s = s0.replace(a, b)
    if s == s0:
        print("mutant " + str(MUTATE) + " did not match " + relpath
              + "; refusing to report a pass on an unmutated tree")
        sys.exit(2)
    p.write_text(s, encoding="utf-8")


def mutate(new_tree):
    if MUTATE == "no-skip-waiting":
        # The classic. The new worker installs correctly and then sits in
        # `waiting` until every tab is closed — which on a phone with the app
        # on the home screen can be days. The old cache is still what serves.
        edit(new_tree, "sw.js", ".then(() => self.skipWaiting())", "")
    elif MUTATE == "no-activate-cleanup":
        # New cache written, old cache never deleted. Disk grows, and a stale
        # entry can still be matched by a worker that falls back to it.
        edit(new_tree, "sw.js",
             "caches.keys().then(keys =>\n      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))\n    )",
             "Promise.resolve()")
    elif MUTATE == "shell-404":
        # The suspected real-world failure: one bad SHELL path makes addAll
        # reject ATOMICALLY, so nothing at all is cached and the worker never
        # activates. This mutant exists mostly to prove the per-URL diagnostic
        # below actually fires and names the offender.
        edit(new_tree, "sw.js", "  './manifest.json',",
             "  './manifest.json',\n  './vendor/leaflet/images/does-not-exist.png',")
    elif MUTATE == "no-version-bump":
        # Files changed, CACHE constant not bumped. The worker script still
        # differs so it installs and activates — and then `activate` deletes
        # every key that is not CACHE, which is now the SAME name, so the stale
        # entries survive under the old name. Rule: bump or field devices keep
        # serving the old copy.
        cur = read_cache_version(new_tree)
        edit(new_tree, "sw.js", "const CACHE = '%s';" % cur,
             "const CACHE = '%s';\n// forced drift" % OLD_VERSION)
    else:
        print("unknown mutant: " + str(MUTATE))
        sys.exit(2)


def sw_state(page):
    """Everything the registration knows, in one round trip."""
    return page.evaluate("""async () => {
      const r = await navigator.serviceWorker.getRegistration();
      return {
        regs: (await navigator.serviceWorker.getRegistrations()).length,
        scope: r && r.scope,
        installing: r && r.installing && r.installing.state,
        waiting: r && r.waiting && r.waiting.state,
        active: r && r.active && r.active.state,
        activeScript: r && r.active && r.active.scriptURL,
        controller: navigator.serviceWorker.controller
                    && navigator.serviceWorker.controller.scriptURL,
        caches: await caches.keys()
      };
    }""")


def poll(page, expr, arg=None, timeout_ms=SETTLE_MS, interval_ms=250):
    """Evaluate `expr` until it returns truthy, or give up. Returns the last
    value either way — the caller asserts on it, so a timeout produces an
    honest failure rather than an exception out of the harness.

    NOT `page.wait_for_function`. THREE of this suite's own waits were written
    with it and NONE of them waited:

        pg.wait_for_function("() => new Promise(r => setTimeout(()=>r(false), 3000))")
        -> returned after 3.03s with the value False

    It resolves the promise and then stops, truthy or not. Every wait in this
    suite is inherently async — `caches.keys()`, `getRegistration()` — so every
    one of them returned on the first tick, and the suite's first "15 passed,
    0 failed" was a fixed 1200 ms sleep getting lucky. Five consecutive re-runs
    afterwards said 13/2. `page.evaluate` DOES await promises correctly, so the
    loop lives here, in Python, where it can be read.

    A wait that does not wait is the same defect this whole project is an audit
    of: a check whose name promises something its behaviour does not deliver,
    failing quietly instead of loudly."""
    import time as _t
    deadline = _t.time() + timeout_ms / 1000.0
    val = None
    while True:
        val = page.evaluate(expr, arg) if arg is not None else page.evaluate(expr)
        if val:
            return val
        if _t.time() >= deadline:
            return val
        page.wait_for_timeout(interval_ms)


def probe_shell(page, base, shell):
    """What the worker's own addAll would have hit, one URL at a time.

    This is the diagnostic that hand-driven DevTools could not produce.
    `caches.addAll` rejects atomically and tells you nothing about WHICH url
    failed; an empty caches.keys() looks identical whether the cause is a 404,
    a redirect, or an opaque response."""
    return page.evaluate("""async ([base, shell]) => {
      const out = [];
      for (const rel of shell) {
        const url = new URL(rel, base + '/').href;
        try {
          const r = await fetch(url, {cache: 'no-store'});
          out.push([rel, r.status, r.redirected ? 'REDIRECTED' : '', r.type]);
        } catch (e) {
          out.push([rel, 'THREW', e.name + ': ' + e.message, '']);
        }
      }
      return out;
    }""", [base, shell])


def main():
    # ------------------------------------------------------------------
    # Two trees. NEW is a copy even in the unmutated case, so that a bug in
    # this suite can never write to the working repo.
    # ------------------------------------------------------------------
    tmp = pathlib.Path(tempfile.mkdtemp())
    new_tree = tmp / "new"
    old_tree = tmp / "old"
    shutil.copytree(ROOT, new_tree)
    shutil.copytree(ROOT, old_tree)
    if MUTATE:
        mutate(new_tree)

    new_ver = read_cache_version(new_tree)
    cur_ver = read_cache_version(ROOT)
    if not cur_ver:
        print("cannot read `const CACHE = '...'` out of sw.js — refusing to run")
        sys.exit(2)
    if cur_ver == OLD_VERSION:
        # The suite's premise is that OLD and NEW differ. If the repo is ever
        # actually on v3 this stops being a takeover test and starts being a
        # no-op that reports green.
        print("sw.js is on %s, which is this suite's OLD_VERSION — the two trees "
              "would be identical. Bump OLD_VERSION." % cur_ver)
        sys.exit(2)
    edit(old_tree, "sw.js", "const CACHE = '%s';" % cur_ver,
         "const CACHE = '%s';" % OLD_VERSION)

    print("sw lifecycle suite  " + str(ROOT) + (f"  MUTANT={MUTATE}" if MUTATE else ""))
    print("  old tree serves %s, new tree serves %s" % (OLD_VERSION, new_ver))

    shell = read_shell(new_tree)
    Swappable.holder["dir"] = old_tree
    httpd, port = serve()
    base = f"http://127.0.0.1:{port}"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context()
        page = ctx.new_page()
        page_errors = []
        console = []
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("console", lambda m: console.append(m.type + ": " + m.text))

        # --------------------------------------------------------------
        # 1. The OLD worker, on the OLD tree.
        # --------------------------------------------------------------
        print("[1] a device that already has the app")
        page.goto(base + "/index.html", wait_until="load")
        reg = page.evaluate("""async () => {
          try {
            const r = await navigator.serviceWorker.register('./sw.js');
            await navigator.serviceWorker.ready;
            return {ok: true, scope: r.scope};
          } catch (e) { return {ok: false, err: e.name + ': ' + e.message}; }
        }""")
        check("the old worker registered at all", reg.get("ok"), reg.get("err"))
        if not reg.get("ok"):
            # Everything below is meaningless without this. Say so and stop
            # rather than emitting forty cascading failures.
            print("\n  registration itself failed — nothing below would mean anything.")
            print("  shell probe against the OLD tree:")
            for row in probe_shell(page, base, shell):
                print("    " + "  ".join(str(c) for c in row))
            browser.close(); httpd.shutdown()
            print("\n%d passed, %d failed" % (PASS, len(FAILS)))
            sys.exit(1)

        poll(page, "async want => (await caches.keys()).includes(want)", OLD_VERSION)
        s1 = sw_state(page)
        # THE EMPTY-SCOPE GUARD. If the old cache never appears, step 3's
        # "the old cache is gone" is trivially true and this whole suite
        # reports a takeover that never happened.
        check("the OLD cache %s exists — otherwise every assertion below "
              "runs on an empty scope" % OLD_VERSION,
              OLD_VERSION in s1["caches"], s1["caches"])
        check("the old worker reached `activated`", s1["active"] == "activated", s1)
        if OLD_VERSION not in s1["caches"]:
            print("  install of the OLD worker did not produce a cache. Per-URL "
                  "probe of what addAll would have fetched:")
            for row in probe_shell(page, base, shell):
                print("    " + "  ".join(str(c) for c in row))

        # --------------------------------------------------------------
        # 2. Swap the bytes under it. Same origin, same port, same
        #    registration — exactly what `git push` does to a phone.
        # --------------------------------------------------------------
        print("[2] the server starts serving the new tree")
        Swappable.holder["dir"] = new_tree
        on_wire = page.evaluate(
            "async b => (await (await fetch(b + '/sw.js', {cache:'no-store'})).text())"
            ".match(/fieldgold-v\\d+/)[0]", base)
        # Reading the wire, not the disk. `fetch` from a controlled page goes
        # THROUGH the worker — this one is a network request only because
        # sw.js's fetch handler falls through to the network on a cache miss,
        # and the old worker never cached the new bytes. Worth stating: an
        # earlier hand-run misread exactly this and concluded the server had
        # not moved.
        check("the server is now serving the new sw.js", on_wire == new_ver, on_wire)

        # --------------------------------------------------------------
        # 3. The takeover.
        # --------------------------------------------------------------
        print("[3] the takeover")
        page.goto(base + "/index.html", wait_until="load")
        page.evaluate("""async () => {
          const r = await navigator.serviceWorker.getRegistration();
          if (r) { try { await r.update(); } catch (e) {} }
        }""")
        # Wait for `activate` to FINISH, rather than sleeping a round number and
        # hoping. The first draft slept 1200 ms — tuned on one fast run, and it
        # caught the worker in state `activating` with the old cache still there
        # on the very next run. A green suite that depends on the machine's mood
        # is worse than a red one: it teaches you to re-run until it agrees.
        #
        # Note what is polled: `installing` must be finished AND the old cache
        # gone. Polling only for `fieldgold-v4 in caches.keys()` would return in
        # 60 ms — measured — because `caches.open(CACHE)` creates the empty
        # cache before `addAll` fetches a single byte.
        poll(page, """async old => {
               const r = await navigator.serviceWorker.getRegistration();
               const k = await caches.keys();
               return !!r && !r.installing && r.active
                      && r.active.state === 'activated' && !k.includes(old);
             }""", OLD_VERSION)
        s2 = sw_state(page)

        # -- A CACHE WITH THE RIGHT NAME IS NOT AN INSTALLED WORKER ---------
        # The first version of this check was `new_ver in caches`, and it
        # PASSED under --mutate shell-404 — a mutant that makes install fail
        # outright. `caches.open(CACHE)` creates the cache before `addAll`
        # ever runs, so a total install failure still leaves a correctly-named
        # EMPTY cache behind. The check read as "the worker installed" and
        # actually meant "something called caches.open once". Exactly the
        # defect this repo keeps finding: a name standing in for the thing the
        # name refers to. Contents are the evidence; the name is not.
        filled = page.evaluate(
            "async n => (await caches.keys()).includes(n)"
            " ? (await (await caches.open(n)).keys()).length : -1", new_ver)
        check("the NEW cache %s exists AND holds entries (an empty cache with "
              "the right name is what a FAILED install leaves behind)" % new_ver,
              filled > 0, "entries=%s caches=%s" % (filled, s2["caches"]))
        check("the OLD cache %s was deleted by `activate`" % OLD_VERSION,
              OLD_VERSION not in s2["caches"], s2["caches"])
        check("no worker is stuck in `waiting` — skipWaiting() did its job",
              not s2["waiting"], s2)
        check("a worker is `activated`", s2["active"] == "activated", s2)
        check("the page is CONTROLLED by a worker — an activated worker that "
              "controls nothing still serves the user the old bytes",
              bool(s2["controller"]), s2)

        if filled <= 0:
            print("  the new worker did not produce its cache. Per-URL probe of "
                  "what addAll would have fetched from the NEW tree:")
            for row in probe_shell(page, base, shell):
                print("    " + "  ".join(str(c) for c in row))
            print("  registration state: " + str(s2))

        # --------------------------------------------------------------
        # 4. A cache with the right NAME is not a cache with the right
        #    CONTENTS. Assert the shell is actually in there.
        # --------------------------------------------------------------
        print("[4] the new cache holds the whole shell")
        cached = page.evaluate("""async ([name, base, shell]) => {
          if (!(await caches.keys()).includes(name)) return null;
          const c = await caches.open(name);
          const miss = [];
          for (const rel of shell) {
            const url = new URL(rel, base + '/').href;
            if (!(await c.match(url))) miss.push(rel);
          }
          return miss;
        }""", [new_ver, base, shell])
        check("every SHELL entry is present in the new cache",
              cached == [], cached if cached is not None else "no such cache")
        check("the SHELL is not empty (a cache of nothing satisfies the line above)",
              len(shell) > 0, len(shell))

        # --------------------------------------------------------------
        # 5. The reason any of this matters: pull the plug.
        # --------------------------------------------------------------
        print("[5] with the server stopped, the app still opens")
        httpd.shutdown()
        offline = page.evaluate("""async b => {
          try {
            const r = await fetch(b + '/index.html');
            return {ok: r.ok, status: r.status, len: (await r.text()).length};
          } catch (e) { return {ok: false, err: e.name + ': ' + e.message}; }
        }""", base)
        check("index.html is served from the cache with the server DOWN",
              offline.get("ok") and offline.get("len", 0) > 0, offline)

        # The instrument checking itself. The first version of this suite
        # reported a failed takeover that was entirely its own 304; if that
        # ever comes back, it must be named as a harness fault rather than
        # blamed on sw.js.
        check("the harness never answered 304 for sw.js (a stale-revalidation "
              "answer here is a HARNESS fault, not a service-worker fault)",
              not Swappable.sw_304, Swappable.sw_304)

        sw_errors = [c for c in console
                     if c.startswith("error") and "favicon" not in c]
        check("no console errors during the whole lifecycle",
              not sw_errors, sw_errors[:3])
        check("no uncaught page errors", not page_errors, page_errors[:2])

        browser.close()

    try:
        httpd.shutdown()
    except Exception:
        pass
    shutil.rmtree(tmp, ignore_errors=True)

    print()
    print("%d passed, %d failed" % (PASS, len(FAILS)))
    for f in FAILS:
        print("  FAILED: " + f)
    # Same inverted convention as test_offline_map.py: under --mutate, a
    # surviving mutant is the failure. CLAUDE.md records that this repo has two
    # conventions; do not "fix" one to match the other without reading both.
    if MUTATE and not FAILS:
        print("MUTANT SURVIVED — this suite would not have caught the bug.")
        sys.exit(1)
    if MUTATE and FAILS:
        print("mutant caught (failures above are the expected outcome)")
        sys.exit(0)
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
