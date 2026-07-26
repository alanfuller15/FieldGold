#!/usr/bin/env python3
"""The twenty bench records live in two files. This proves they agree.

    load_rem_benches.html   the manual loader page
    fieldgold-data.js       the auto-seed array, run by every page on load

Both are written by tools/build_loader.py from one `payload` string. That makes
them agree BY CONSTRUCTION — as long as nobody hand-edits either copy, and as
long as the generator is actually re-run after the STATUS table changes. This
suite checks the part construction cannot: what is on disk, right now.

The failure it exists to catch is specific. Before the generator owned the seed
array, the two copies were kept in step by hand and happened to match. Let them
drift and the loader page says REM-14 is inside Mineral Closing Order 549 while
the auto-seed writes REM-14 with no land status at all — so the map draws it as
an ordinary cyan diamond, the trip planner has nothing to withhold, and the
only symptom is a bench that looks fine. Nobody reads two JSON arrays side by
side to notice.

No browser and no network: this is file reading and a subprocess. Run it first.

    python3 tests/test_seed_drift.py
    python3 tests/test_seed_drift.py --mutate hand-edited-seed
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PASS = 0
FAILS = []


def check(name, cond, detail=""):
    global PASS
    if cond:
        PASS += 1
        print("  ok    " + name)
    else:
        FAILS.append(name)
        print("  FAIL  " + name + (("  -- " + str(detail)) if detail else ""))


def extract(path, decl):
    text = open(path, encoding="utf-8").read()
    hit = re.search(decl + r" REM_BENCHES = (\[.*?\]);", text, re.S)
    if not hit:
        return None, text
    return json.loads(hit.group(1)), text


# ---------------------------------------------------------------- the mutants
#
# Each one is a hand edit somebody could plausibly make, applied to a THROWAWAY
# copy of the repo. A mutant that this suite does not catch is a hand edit that
# would reach a phone.
MUTANTS = {
    # The whole reason this file exists: someone "fixes" a status in one copy.
    "hand-edited-seed": (
        "fieldgold-data.js",
        '"land_status": "avoid"',
        '"land_status": "clean"',
    ),
    # Subtler: the seed array is stale because the generator was never re-run
    # after the STATUS table changed. Simulated by deleting a record from one.
    "stale-seed": (
        "fieldgold-data.js",
        '"profile": "REM-14"',
        '"profile": "REM-14-STALE"',
    ),
    # The loader page edited instead of the generator.
    "hand-edited-loader": (
        "load_rem_benches.html",
        '"state_claim_proximity": "unknown"',
        '"state_claim_proximity": 0',
    ),
    # The markers removed, so the generator can no longer find the region and a
    # future run would fail — but the files still agree today, so ONLY the
    # marker assertion catches this one.
    "markers-removed": (
        "fieldgold-data.js",
        "  // ==== BEGIN GENERATED — tools/build_loader.py ==========================",
        "  // (region)",
    ),
}

MUTATE = None
if "--mutate" in sys.argv:
    MUTATE = sys.argv[sys.argv.index("--mutate") + 1]
    if MUTATE not in MUTANTS:
        sys.exit(f"unknown mutant {MUTATE!r}; have: {', '.join(sorted(MUTANTS))}")

# Work on a throwaway copy so a mutant can never touch the real tree.
WORK = tempfile.mkdtemp(prefix="fg-seed-drift-")
for name in ("load_rem_benches.html", "fieldgold-data.js"):
    shutil.copy2(os.path.join(ROOT, name), os.path.join(WORK, name))
os.makedirs(os.path.join(WORK, "tools"), exist_ok=True)
shutil.copy2(os.path.join(ROOT, "tools", "build_loader.py"),
             os.path.join(WORK, "tools", "build_loader.py"))

if MUTATE:
    fname, old, new = MUTANTS[MUTATE]
    target = os.path.join(WORK, fname)
    text = open(target, encoding="utf-8").read()
    # A mutation that changes nothing is not a mutation; it is a green tick for
    # free. Abort loudly rather than report a pass this suite did not earn.
    if old not in text:
        print(f"MUTANT {MUTATE!r} MATCHED NOTHING in {fname} — aborting.")
        print("  The suite cannot be shown to fail, so its passes mean nothing.")
        sys.exit(2)
    open(target, "w", encoding="utf-8").write(text.replace(old, new, 1))
    print(f"[mutant {MUTATE}: {fname}]")

HTML = os.path.join(WORK, "load_rem_benches.html")
JS = os.path.join(WORK, "fieldgold-data.js")

print("\n-- the two copies agree --")
loader, loader_text = extract(HTML, "const")
seed, seed_text = extract(JS, "var")

check("load_rem_benches.html carries a REM_BENCHES array", loader is not None)
check("fieldgold-data.js carries a REM_BENCHES array", seed is not None)

if loader is None or seed is None:
    print(f"\n{PASS} passed, {len(FAILS)} failed")
    sys.exit(0 if MUTATE and FAILS else 1)

check("both carry 20 records", len(loader) == 20 and len(seed) == 20,
      f"{len(loader)} / {len(seed)}")
check("THE TWO PAYLOADS ARE IDENTICAL", loader == seed,
      "the loader page and the auto-seed disagree about the twenty benches")

if loader != seed:
    ids_l = {b.get("id") for b in loader}
    ids_s = {b.get("id") for b in seed}
    if ids_l != ids_s:
        print(f"        ids only in loader: {sorted(ids_l - ids_s)}")
        print(f"        ids only in seed:   {sorted(ids_s - ids_l)}")
    for a in loader:
        b = next((x for x in seed if x.get("id") == a.get("id")), None)
        if b is not None and a != b:
            diff = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
            print(f"        {a.get('profile')}: fields disagree: {sorted(diff)}")

print("\n-- the seed array is inside the generated region --")
BEGIN = "// ==== BEGIN GENERATED"
END = "// ==== END GENERATED"
check("the BEGIN marker is present", BEGIN in seed_text)
check("the END marker is present", END in seed_text)
if BEGIN in seed_text and END in seed_text:
    i, j = seed_text.index(BEGIN), seed_text.index(END)
    check("the markers are in order", i < j)
    region = seed_text[i:j]
    check("the array declaration is INSIDE the markers",
          "var REM_BENCHES" in region,
          "the seed array sits outside the region the generator rewrites, so a "
          "generator run would leave it stale and say nothing")

print("\n-- no record escapes without both registers --")
REQUIRED = ("land_status", "state_claim", "state_claim_checked",
            "state_claim_register", "state_claim_proximity", "status_checked")
missing = [(b.get("profile"), k) for b in seed for k in REQUIRED if k not in b]
check("every seeded record carries both registers", not missing, missing[:4])

bad = [b.get("profile") for b in seed
       if b.get("land_status") not in ("clean", "unchecked", "avoid")]
check("every land_status is one of the three tiers", not bad, bad)

# The auto-seed runs on EVERY page load, on a phone, with no prompt. A record
# reaching storage with state_claim 'none' and no date is a rumour presented as
# a result, and nothing downstream can tell the difference.
undated = [b.get("profile") for b in seed
           if b.get("state_claim") == "none" and not b.get("state_claim_checked")]
check("no 'none' claim result is undated", not undated, undated)

zeroed = [b.get("profile") for b in seed
          if b.get("state_claim_proximity") != "unknown"]
check("claim proximity is 'unknown' on every record, never a number", not zeroed,
      "per-bench proximity was never measured; a number here is a fabrication")

n_clean = sum(1 for b in seed if b.get("land_status") == "clean")
n_avoid = sum(1 for b in seed if b.get("land_status") == "avoid")
check("the seed carries 8 clean and 12 avoid", (n_clean, n_avoid) == (8, 12),
      f"clean={n_clean} avoid={n_avoid}")

print("\n-- the checked-in files are what the generator produces --")
before = {p: open(p, "rb").read() for p in (HTML, JS)}
run = subprocess.run([sys.executable, os.path.join(WORK, "tools", "build_loader.py")],
                     capture_output=True, text=True)
after = {p: open(p, "rb").read() for p in (HTML, JS)}
check("the generator runs clean on the tree", run.returncode == 0,
      (run.stderr or run.stdout)[-300:])
check("re-running it changes NOTHING (the tree is generated, not hand-made)",
      before == after,
      "a file on disk differs from what the generator would write — someone "
      "edited output instead of the STATUS table, or never re-ran it")

print(f"\n{PASS} passed, {len(FAILS)} failed")
shutil.rmtree(WORK, ignore_errors=True)

if MUTATE:
    # Under --mutate the suite is being tested, not the repo: a mutant that
    # gets caught is the SUCCESS case.
    if FAILS:
        print(f"MUTANT {MUTATE!r} CAUGHT by: {FAILS[0]}")
        sys.exit(0)
    print(f"MUTANT {MUTATE!r} SURVIVED — this suite does not catch it.")
    sys.exit(1)

if FAILS:
    print("SEED-DRIFT SUITE FAILED")
    sys.exit(1)
print("SEED-DRIFT SUITE PASSED")
