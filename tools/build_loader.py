"""Regenerate the REM bench payload — into BOTH files that carry it.

Coordinates are CARRIED OVER PROGRAMMATICALLY from the original file, never
retyped. Retyping 20 lat/lon pairs by hand is exactly the kind of silent
transcription error that would send someone to the wrong bench, and it would
not show up in any test.

TWO OUTPUTS, ONE PAYLOAD.  The twenty records live in two places:

  load_rem_benches.html   the manual loader page ("Load all 20 with status")
  fieldgold-data.js       the AUTO-SEED array, which every page runs on load

Before this script owned the second one they were kept in step by hand, and
they happened to agree. That is not a property, that is a coincidence with a
deadline. The failure it invites is specific and bad: the loader page says
REM-14 is inside MCO 549 and the auto-seed writes REM-14 with no land status at
all, so the map draws it as an ordinary cyan diamond and the trip planner has
nothing to withhold. One generator writes both, from the same `payload` string,
and tests/test_seed_drift.py fails the build if the two copies ever differ.
"""
import json
import re
import sys

# SRC and DST are the SAME file: this script reads the existing loader, carries
# its coordinates forward, and rewrites it in place. Paths are resolved from
# THIS FILE's location (repo_root/tools/build_loader.py -> repo_root/...), not
# from the current working directory, so it does the same thing no matter where
# you run it from. See the idempotency note near geo_score/geo_rank below --
# running this twice must be a no-op, and there are assertions that fail loudly
# if it ever stops being one.
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(_ROOT, "load_rem_benches.html")
DST = SRC
DATA_JS = os.path.join(_ROOT, "fieldgold-data.js")

# The generated region in fieldgold-data.js. Everything between these two lines
# is this script's to write; everything outside them is hand-maintained.
JS_BEGIN = "  // ==== BEGIN GENERATED — tools/build_loader.py =========================="
JS_END = "  // ==== END GENERATED ===================================================="

# ---------------------------------------------------------------------------
# Land status, transcribed from HATCHER_SU_RESEARCH_LOG.md Threads 9 and 11.
# Every entry here is either a point-in-polygon result against the DNR ArcGIS
# services (positive-control verified) or an explicit "never checked".
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# State mining claims — DNR ME112 (active) and ME13 (pending).
#
# This is a DIFFERENT REGISTER from the encumbrance battery above, asked
# separately, and it stays a separate field on every record. A bench can be
# clean on every encumbrance layer and still sit inside an active claim.
#
# All 20 points were queried against ME112 as part of their land-status
# battery (Thread 9/11 for the eight dated 2026-07-21, Thread 16 for the twelve
# dated 2026-07-25). Every one returned an empty feature array. Five of them —
# REM-1, REM-2, REM-11, REM-19, REM-20 — were re-fetched directly on 2026-07-25
# and returned empty again.
#
# What is NOT established, and is therefore stated on the page rather than
# implied away: HOW NEAR the nearest claim is. There are 22 active claims in
# the reach envelope and 3 inside the box holding REM-1/11/19/20. Per-bench
# proximity counts could not be collected — the fetch proxy began rejecting the
# envelope-count form partway through the session and it was not routed around.
STATE_CLAIM_REGISTER = ("DNR ME112 active / ME13 pending, "
                        "Mapper/Mineral_Estate_Layers")
STATE_CLAIM_REACH_ACTIVE = 22
STATE_CLAIM_REACH_PENDING = 0

# Every field this script DERIVES, as opposed to carries forward.
#
# SRC and DST are the same file, so each of these already sits in the record
# this script just read: it is the previous run's output. That makes a derived
# field self-perpetuating — delete its assignment below and the value keeps
# appearing on every record, inherited from the file, with the assertions still
# green and the output still byte-identical. Found by a mutation test on
# state_claim that DELETED the assignment and could not fail.
#
# So they are dropped from the carried-forward dict before anything is written.
# A derived field that stops being derived now DISAPPEARS, loudly, and both the
# assertions below and the byte-comparison in tests/test_state_claims.py catch
# it. geo_score/geo_rank are deliberately absent from this list: they are the
# one pair that MUST be inherited, for the reason recorded at their assignment.
DERIVED = ("rank", "score", "land_status", "status_label", "status_detail",
           "in_pua", "status_checked", "status_depth", "status_source", "note",
           "state_claim", "state_claim_checked", "state_claim_register",
           "state_claim_proximity")

STATUS = {
    # =======================================================================
    # TIER 1 — CLEAN.  Ordered by DEPTH OF EVIDENCE first, then PUA, then
    # geomorphic rank.  The three Thread 9/11 candidates went through the FULL
    # 16-layer battery; the five added on 2026-07-25 went through an 8-layer
    # Tier-1 battery only.  Ranking a shallower-checked bench above a
    # deeply-checked one would hide that difference behind a number.
    # =======================================================================
    "REM-2": dict(
        cls="clean", order=1, pua=True, checked="2026-07-21", depth="full",
        label="CLEAN — verified (full 16-layer battery)",
        detail="No mineral closing order, no leasehold location order, no active "
               "or pending claim, no lease, no park closure. Inside Hatcher Pass "
               "Management Area-East, where DNR allows recreational panning with "
               "hand pick, shovel and pan. Well log 86093 (720 m S) shows bedrock "
               "at 20 ft under 17 ft of sand and gravel — the best structural "
               "setting on the reach for hand work."),
    "REM-13": dict(
        cls="clean", order=2, pua=True, checked="2026-07-21", depth="full",
        label="CLEAN — verified (full 16-layer battery)",
        detail="Same clean result as REM-2 on every layer. Inside Hatcher Pass "
               "Management Area-East, so recreational panning is allowed. No "
               "well-log control on depth to bedrock here."),
    "REM-7": dict(
        cls="clean", order=3, pua=False, checked="2026-07-21", depth="full",
        label="CLEAN — verified, but OUTSIDE the Public Use Area",
        detail="Clean on all encumbrance layers, and specifically NOT inside ADL "
               "229824. But it falls outside Hatcher Pass Management Area-East, so "
               "it does NOT inherit the PUA panning permission — the permission "
               "here is ordinary state-land rules, not the PUA fact sheet. Three "
               "well logs within 560 m show 120–215 ft of boulders and gravel with "
               "bedrock never reached. Pan the bench gravel; there is no reachable "
               "bedrock target."),

    "REM-1": dict(
        cls="clean", order=4, pua=True, checked="2026-07-25", depth="tier1",
        label="CLEAN — 8-layer check, inside the Public Use Area",
        detail="Zero hits on all seven encumbrance layers run (mineral order, "
               "leasehold location order, active claim, pending claim, prospecting "
               "site, mineral-estate permit/lease, land-estate permit/lease), and "
               "inside Hatcher Pass Management Area-East, so recreational panning "
               "with hand pick, shovel and pan is allowed. Largest terrace on the "
               "whole list at 59,888 m², but it sits ~14 m above the channel — the "
               "highest of any candidate — so it is the oldest surface here and "
               "may be a glacial deposit rather than a river terrace. NOT checked "
               "against the eight rarer Tier-2 layers (native allotment, Mental "
               "Health Trust, federal action, easement, land disposal, management "
               "agreement, agreement/settlement, restricted-use authorization)."),
    "REM-5": dict(
        cls="clean", order=5, pua=True, checked="2026-07-25", depth="tier1",
        label="CLEAN — 8-layer check, inside the Public Use Area",
        detail="Zero hits on all seven encumbrance layers run; inside Hatcher Pass "
               "Management Area-East. Small terrace (1,002 m²) but only 3.9 m above "
               "the channel and very flat (height SD 0.3 m) — the tightest, "
               "lowest-standing surface on the list, which is the geometry a young "
               "fluvial terrace should have. NOT checked against the eight rarer "
               "Tier-2 layers."),
    "REM-11": dict(
        cls="clean", order=6, pua=True, checked="2026-07-25", depth="tier1",
        label="CLEAN — 8-layer check, inside the Public Use Area",
        detail="Zero hits on all seven encumbrance layers run; inside Hatcher Pass "
               "Management Area-East. 920 m², 4.9 m above the channel. Note that "
               "REM-19, only ~140 m to the southwest, falls OUTSIDE the PUA — the "
               "boundary runs between them, so do not assume the permission "
               "carries across the gap. NOT checked against the eight rarer Tier-2 "
               "layers."),
    "REM-20": dict(
        cls="clean", order=7, pua=True, checked="2026-07-25", depth="tier1",
        label="CLEAN — 8-layer check, inside the Public Use Area",
        detail="Zero hits on all seven encumbrance layers run; inside Hatcher Pass "
               "Management Area-East. Smallest terrace on the list (8,948 m² is "
               "misleading — height SD 0.6 m, 4.1 m above channel) and the "
               "furthest upstream of the clean set. NOT checked against the eight "
               "rarer Tier-2 layers."),
    "REM-19": dict(
        cls="clean", order=8, pua=False, checked="2026-07-25", depth="tier1",
        label="CLEAN — 8-layer check, but OUTSIDE the Public Use Area",
        detail="Zero hits on all eight layers run, INCLUDING the park-boundary "
               "layer: this point is not inside Hatcher Pass Management Area-East. "
               "That is not an encumbrance, but it means the PUA fact sheet's "
               "recreational-panning permission does NOT apply here — the same "
               "caveat as REM-7. REM-11 is ~140 m northeast and IS inside the PUA; "
               "the boundary runs between the two, and a hand-held GPS fix is not "
               "accurate enough to stand on that line with confidence. If you want "
               "PUA cover, work REM-11 and leave this one. NOT checked against the "
               "eight rarer Tier-2 layers."),

    # =======================================================================
    # TIER 3 — AVOID.  Ordered softest-first: pending applications (exposure,
    # not prohibition), then LLO 5 (minerals by lease only), then MCO 549
    # (hard closure).
    # =======================================================================
    # --- Pending ADL 229824, INSIDE the PUA -------------------------------
    # These four are the uncomfortable ones. The ONLY hit is a PENDING
    # industrial/commercial lease application — case status 10, "ADDTL INFO
    # REQUESTED". It is not an active lease and it does not close the ground
    # today, and all four are inside the PUA where panning is allowed. They
    # are graded AVOID for consistency with REM-6 and on exposure alone. If
    # the DMLW call comes back clear on pending applications, these four
    # should move to CLEAN and REM-8 would rank near the top of the list.
    "REM-8": dict(
        cls="avoid", order=9, pua=True, checked="2026-07-25", depth="tier1",
        label="SKIP on exposure — pending application ADL 229824 (not a closure)",
        detail="Clean on every mineral-estate layer. The one hit is ADL 229824 "
               "(Fishhook Renewable Energy LLC), case type verbatim \"NEG LEASE "
               "NON-COMP (553)\", special code \"INDUSTRL/COMMERCIAL (5015)\", "
               "status \"ADDTL INFO REQUESTED (10)\" — a PENDING application, not "
               "an active lease. This point is also inside the PUA, so recreational "
               "panning is otherwise allowed. Graded avoid on exposure only, the "
               "same call already made for REM-6. Worth raising on the DMLW call: "
               "at 36,644 m² and 5.2 m above the channel this is the third-best "
               "geometry on the list, and it is being set aside for a reason that "
               "may not survive one phone call."),
    "REM-9": dict(
        cls="avoid", order=10, pua=True, checked="2026-07-25", depth="tier1",
        label="SKIP on exposure — pending application ADL 229824 (not a closure)",
        detail="Same single hit as REM-8: pending ADL 229824, status 10. Inside "
               "the PUA. Graded avoid on exposure only. Weak geometry regardless "
               "(951 m², 17.7 m above the channel — the highest surface on the "
               "list, most likely glacial rather than fluvial)."),
    "REM-16": dict(
        cls="avoid", order=11, pua=True, checked="2026-07-25", depth="tier1",
        label="SKIP on exposure — pending application ADL 229824 (not a closure)",
        detail="Same single hit as REM-8: pending ADL 229824, status 10. Inside "
               "the PUA. Graded avoid on exposure only. 13,057 m², 9.2 m above "
               "the channel."),
    "REM-17": dict(
        cls="avoid", order=12, pua=True, checked="2026-07-25", depth="tier1",
        label="SKIP on exposure — pending application ADL 229824 (not a closure)",
        detail="Same single hit as REM-8: pending ADL 229824, status 10. Inside "
               "the PUA. Graded avoid on exposure only. 12,960 m², 8.2 m above "
               "the channel."),
    # --- Pending ADL 229824, OUTSIDE the PUA ------------------------------
    "REM-6": dict(
        cls="avoid", order=13, pua=False, checked="2026-07-21", depth="full",
        label="SKIP — inside a pending application",
        detail="Clean on every hard encumbrance, BUT the point falls inside ADL "
               "229824 (Fishhook Renewable Energy LLC), status 10 — a PENDING "
               "application, case type verbatim \"NEG LEASE NON-COMP (553)\". Not "
               "an active lease, so it does not close the ground today. Skipped on "
               "exposure, not prohibition: ground inside a live application "
               "footprint can change status without notice. Also outside the PUA."),
    # --- LLO 5, Little Susitna River Corridor -----------------------------
    "REM-3": dict(
        cls="avoid", order=14, pua=False, checked="2026-07-21", depth="full",
        label="LLO 5 — minerals by lease only",
        detail="Inside LLO 5 \"Little Susitna River Corridor\" (Leasehold Location "
               "Order, Active/Restricted). Minerals are acquirable only by lease, "
               "not by staking a claim. Whether LLO 5 bars RECREATIONAL hand "
               "panning is UNRESOLVED — see the open question below."),
    "REM-4": dict(
        cls="avoid", order=15, pua=False, checked="2026-07-21", depth="full",
        label="LLO 5 — minerals by lease only",
        detail="Inside LLO 5 \"Little Susitna River Corridor\", same as REM-3. "
               "Recreational panning status unresolved."),
    "REM-10": dict(
        cls="avoid", order=16, pua=False, checked="2026-07-25", depth="tier1",
        label="LLO 5 — minerals by lease only",
        detail="Inside LLO 5 \"Little Susitna River Corridor\" (CASE_ID \"LLO 5\", "
               "ACTIVE (50), RESTRICTED (RD)). Clean on every other layer run, and "
               "NOT inside the PUA. 30,540 m² at 9.2 m above the channel — the best "
               "geometry of the six LLO 5 candidates, and the one with most to gain "
               "if the DMLW call comes back permissive. Recreational panning status "
               "unresolved."),
    "REM-12": dict(
        cls="avoid", order=17, pua=False, checked="2026-07-21", depth="full",
        label="LLO 5 — minerals by lease only",
        detail="Inside LLO 5 \"Little Susitna River Corridor\", same as REM-3. "
               "Recreational panning status unresolved."),
    "REM-15": dict(
        cls="avoid", order=18, pua=False, checked="2026-07-25", depth="tier1",
        label="LLO 5 — minerals by lease only",
        detail="Inside LLO 5 \"Little Susitna River Corridor\" (ACTIVE/RESTRICTED). "
               "Clean on every other layer run, and NOT inside the PUA. 13,221 m², "
               "7.2 m above the channel. Recreational panning status unresolved."),
    "REM-18": dict(
        cls="avoid", order=19, pua=True, checked="2026-07-25", depth="tier1",
        label="LLO 5 — minerals by lease only (and inside the PUA)",
        detail="Inside LLO 5 \"Little Susitna River Corridor\" (ACTIVE/RESTRICTED) "
               "AND inside Hatcher Pass Management Area-East. That overlap is "
               "exactly the unresolved question: the PUA fact sheet allows "
               "recreational panning, LLO 5 restricts mineral acquisition to lease. "
               "This is the single best point to put to DMLW on the phone, because "
               "the answer decides six candidates at once. 11,363 m², only 3.7 m "
               "above the channel and very flat (height SD 0.4 m) — the lowest and "
               "flattest surface of any candidate on the list."),
    # --- MCO 549, hardest closure -----------------------------------------
    "REM-14": dict(
        cls="avoid", order=20, pua=False, checked="2026-07-21", depth="full",
        label="MCO 549 — CLOSED to mineral entry",
        detail="Inside Mineral Closing Order 549, \"Hatcher Pass / Government Peak "
               "Ski Area\". This is the hardest closure of any candidate on the "
               "list. Do not work this ground."),
}

# Every one of the 20 is now land-status checked. If a profile ever goes
# missing from STATUS the build must FAIL rather than quietly emit a record
# with no tier — a bench with no land_status is the exact failure this whole
# schema exists to prevent.

# ---------------------------------------------------------------------------
src = open(SRC, encoding="utf-8").read()
m = re.search(r"const REM_BENCHES = (\[.*?\]);", src, re.S)
if not m:
    sys.exit("ERROR: could not find the REM_BENCHES array in the source file.")
original = json.loads(m.group(1))
if len(original) != 20:
    sys.exit(f"ERROR: expected 20 benches, found {len(original)}")

out = []
for b in original:
    prof = b["profile"]
    st = STATUS[prof]
    nb = dict(b)                      # carry lat/lon/id/area/etc. UNTOUCHED
    for k in DERIVED:                 # ...but never a previous run's OUTPUT
        nb.pop(k, None)
    # BUG FIXED 2026-07-25: this used to read b["score"]/b["rank"] unconditionally.
    # Because SRC and DST are the same file, a SECOND run would then copy the
    # PREVIOUS run's land-status ordering into geo_rank and destroy the real
    # geomorphic ranking — silently, with every coordinate still correct, so no
    # coordinate assertion would have caught it. Carry the geomorphic values
    # forward when they already exist; only derive them on the first pass.
    nb["geo_score"] = b.get("geo_score", b["score"])
    nb["geo_rank"] = b.get("geo_rank", b["rank"])
    nb["rank"] = st["order"]          # rank is now the VERIFIED ordering
    nb["score"] = st["order"]
    nb["land_status"] = st["cls"]
    nb["status_label"] = st["label"]
    nb["status_detail"] = st["detail"]
    nb["in_pua"] = st["pua"]
    nb["status_checked"] = st["checked"]
    nb["status_depth"] = st["depth"]
    # A second register, kept as its own field. Merging it into land_status
    # would let an unchecked claim inherit a clean encumbrance call.
    nb["state_claim"] = "none"
    nb["state_claim_checked"] = st["checked"]
    nb["state_claim_register"] = STATE_CLAIM_REGISTER
    nb["state_claim_proximity"] = "unknown"
    nb["status_source"] = (
        "HATCHER_SU_RESEARCH_LOG.md Thread 9/11 — DNR ArcGIS point-in-polygon, "
        "16-layer battery, positive-control verified"
        if st["depth"] == "full" else
        "HATCHER_SU_RESEARCH_LOG.md Thread 16 — DNR ArcGIS point-in-polygon, "
        "8-layer Tier-1 battery, every CLEAN call re-fetched independently, "
        "positive-control verified")
    nb["note"] = ("REM terrace candidate — geomorphically derived, ground-truth "
                  "required. " + st["label"])
    out.append(nb)

out.sort(key=lambda b: b["rank"])

# --- assertions: the patch must not have moved anything it should not have ---
by_id = {b["id"]: b for b in original}
for b in out:
    o = by_id[b["id"]]
    assert b["lat"] == o["lat"] and b["lon"] == o["lon"], f"COORD MOVED: {b['id']}"
    assert b["profile"] == o["profile"], f"PROFILE REMAPPED: {b['id']}"
    assert b["kind"] == "bench" and b["source"] == "REM"
assert sorted(b["rank"] for b in out) == list(range(1, 21)), "ranks not 1..20"
assert len(out) == 20
n_clean = sum(1 for b in out if b["land_status"] == "clean")
n_unch = sum(1 for b in out if b["land_status"] == "unchecked")
n_avoid = sum(1 for b in out if b["land_status"] == "avoid")
assert (n_clean, n_unch, n_avoid) == (8, 0, 12), (n_clean, n_unch, n_avoid)
assert all(b["status_checked"] for b in out), "a record escaped with no check date"
# 'none' is a RESULT and must carry the date it was taken. A claim check with no
# date is not a result, it is a rumour, and the UI has no way to tell the
# difference once the field is written.
assert all(b["state_claim"] == "none" for b in out), \
    "every point was queried against ME112 and every one came back empty"
assert all(b["state_claim_checked"] == b["status_checked"] for b in out), \
    "the claim check rode along with the land-status battery; the dates must agree"
assert all(b["state_claim_proximity"] == "unknown" for b in out), \
    "per-bench claim proximity was never measured — do not let it read as zero"
assert all(b["in_pua"] in (True, False) for b in out), "in_pua must be decided"
assert len(STATUS) == 20, f"STATUS table has {len(STATUS)} entries, expected 20"
# The guard for the bug above: geomorphic scores are REM fitness values in
# (0,1). Land-status orders are integers 1..20. If a clobber ever happens again
# these assertions fail immediately instead of shipping a scrambled ranking.
assert all(0 < b["geo_score"] < 1 for b in out), \
    "geo_score looks like a rank, not a score — the geomorphic ranking was clobbered"
assert sorted(b["geo_rank"] for b in out) == list(range(1, 21)), \
    "geo_rank is not a permutation of 1..20"

payload = json.dumps(out, indent=1)

HTML = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Load REM Benches — FieldGold</title>
<style>
 body{background:#14110C;color:#F2EDE0;font-family:-apple-system,system-ui,sans-serif;
   max-width:680px;margin:0 auto;padding:32px 20px;line-height:1.6}
 h1{color:#E8C04A;font-size:1.4rem} h2{font-size:1.05rem;margin:26px 0 8px}
 .gold{color:#E8C04A}
 .card{background:#1E1A13;border:1px solid #332C1E;border-radius:10px;padding:16px;margin:14px 0}
 button{background:#C9A227;color:#14110C;border:0;border-radius:8px;padding:12px 20px;
   font-weight:700;font-size:1rem;cursor:pointer;margin:8px 8px 0 0}
 button.ghost{background:transparent;color:#C9A227;border:1px solid #C9A227}
 .warn{background:#2E2410;border:1px solid #C9A227;border-radius:8px;padding:12px;
   font-size:.9rem;color:#E8C04A;margin:14px 0}
 .stop{background:#2E1512;border:1px solid #C0392B;color:#F0A79E}
 code{background:#0d0b08;padding:1px 5px;border-radius:3px}
 .n{color:#9C9684;font-size:.85rem}
 ul{padding-left:20px} li{margin:5px 0}
 .row{display:flex;gap:10px;align-items:baseline;padding:7px 0;border-bottom:1px solid #241F16}
 .row:last-child{border-bottom:0}
 .rk{color:#9C9684;font-size:.8rem;min-width:26px}
 .nm{font-weight:700;min-width:66px}
 .tag{font-size:.72rem;padding:2px 7px;border-radius:4px;white-space:nowrap}
 .t-clean{background:#16301B;color:#7BD88F;border:1px solid #2C5C36}
 .t-unchecked{background:#2B2617;color:#D8C07B;border:1px solid #5C4F2C}
 .t-avoid{background:#2E1512;color:#F0A79E;border:1px solid #5C2C28}
 .d{font-size:.82rem;color:#9C9684;margin:2px 0 0 96px}
</style></head><body>
<h1>Load REM Terrace Candidates</h1>
<p>Adds <span class="gold">20 REM-derived bench candidates</span> to your FieldGold
shared record, <b>each carrying its DNR land status</b>. As of 2026-07-25 every one
of the 20 has been checked; none are left unknown.</p>

<div class="warn">
 <b>Honest about what these are:</b> geomorphically-derived terrace candidates —
 flat ground at bench height above the real river, extracted by the published REM /
 TerEx method from lidar. They are <b>NOT</b> confirmed benches and <b>NOT</b> gold.
 The Little Su's gold is likely morainal (glacial), which a REM can't distinguish
 from sorted fluvial terraces. These are <b>first-pass targets to go pan</b> — the
 ground makes the call.
</div>

<div class="warn stop">
 <b>All 20 are now land-status checked. 12 of them are not ground to work.</b>
 This list used to be ranked by terrace area alone, which put never-checked ground
 at #1. It is now ranked by <b>land status first</b>, geometry second.
 <b>8 of 20 came back clean</b> — but two of those eight (REM-7 and REM-19) are
 <b>outside</b> the Hatcher Pass Public Use Area and so do <b>not</b> get the PUA's
 recreational-panning permission. The other <b>12 are flagged AVOID</b>: one inside
 Mineral Closing Order 549, six inside LLO 5, five inside pending application
 ADL 229824.
 <br><br>
 <b>Two of the eight clean are checked more deeply than the other six.</b> REM-2,
 REM-13 and REM-7 went through a full 16-layer battery on 2026-07-21. REM-1, REM-5,
 REM-11, REM-19 and REM-20 went through an 8-layer Tier-1 battery on 2026-07-25 —
 every one of those CLEAN calls was re-fetched independently rather than taken on
 trust, but eight rarer layers (native allotment, Mental Health Trust, federal
 action, easement, land disposal, management agreement, agreement/settlement,
 restricted-use authorization) were <b>not run on any of them</b>. That is why the
 shallower five rank below the deeper three even where their geometry is better.
</div>

<div class="card">
 <button onclick="load('all')">Load all 20 with status</button>
 <button class="ghost" onclick="load('clean')">Load only the 8 clean</button>
 <p id="status" class="n"></p>
 <p class="n">Safe to re-run: entries upsert by <code>id</code>, so this <b>replaces</b>
 any older copies already on your device rather than duplicating them. If you loaded
 the old unranked list before, running this once fixes it.</p>
</div>

<h2>What you'd be loading</h2>
<div class="card" id="list"></div>

<div class="warn">
 <b>Two questions still open — neither is answered by this page.</b>
 <ul>
  <li><b>No bench sits inside a state mining claim — but claims are near.</b>
      All 20 points were queried against DNR <code>ME112</code> (active state
      mining claims) and all 20 came back empty. That is the register that
      governs this ground; the BLM federal layer on the map is not. What is
      <b>not</b> known is how near the nearest claim is: there are <b>22 active
      claims</b> in the reach and <b>3</b> in the box holding REM-1, REM-11,
      REM-19 and REM-20. Proximity was never measured. Do not read "no claim on
      the point" as "nothing around you."</li>
  <li><b>Claims can be staked at any time.</b> The clean result is dated
      <b>2026-07-21</b>. Re-run the claim check the week you travel; a bench that was
      clear in July can be staked in August.</li>
  <li><b>LLO 5 and MCO 549 govern mineral-RIGHTS acquisition.</b> Whether they also
      bar <i>recreational hand panning</i> inside the Public Use Area is unresolved
      — DNR's PUA fact sheet allows panning "anywhere within the boundaries...
      except for several valid mining claims." This now blocks <b>six</b>
      candidates: REM-3, REM-4, REM-10, REM-12, REM-15 and REM-18. Put
      <b>REM-18</b> to DNR Division of Mining, Land &amp; Water (907-269-8600)
      specifically — it is inside LLO 5 <i>and</i> inside the PUA, so it is the one
      point whose answer settles all six.</li>
  <li><b>A pending application is not a closure.</b> REM-8, REM-9, REM-16 and
      REM-17 are clean on every mineral layer and inside the PUA. Their only hit is
      ADL 229824 (Fishhook Renewable Energy LLC), status "ADDTL INFO REQUESTED
      (10)" — a <i>pending</i> industrial/commercial lease application. They are
      flagged AVOID on exposure alone, for consistency with REM-6, not because the
      ground is closed. Ask DMLW about pending applications on the same call: if
      the answer is permissive, REM-8 (36,644 m², 5.2 m above the channel) belongs
      near the top of this list, not near the bottom.</li>
 </ul>
</div>

<p class="n">REM benches are tagged <code>source: REM</code> and labeled
<code>REM-1..N</code> so they stay distinct from your Bench Hunter benches, which
this page never touches.</p>

<script src="fieldgold-data.js"></script>
<script>
const REM_BENCHES = __PAYLOAD__;

const LABEL = {clean:'CLEAN', unchecked:'NOT CHECKED', avoid:'AVOID'};

function render(){
  document.getElementById('list').innerHTML = REM_BENCHES.map(b =>
    '<div class="row"><span class="rk">#'+b.rank+'</span>'+
    '<span class="nm">'+b.profile+'</span>'+
    '<span class="tag t-'+b.land_status+'">'+LABEL[b.land_status]+'</span>'+
    '<span class="n">'+b.lat.toFixed(5)+', '+b.lon.toFixed(5)+'</span></div>'+
    '<div class="d">'+b.status_label+'</div>').join('');
}

function load(which){
  const el = document.getElementById('status');
  if(!window.FieldGoldData){ el.textContent =
    'Error: open this from the same site as FieldGold (alanfuller15.github.io/FieldGold/).';
    return; }
  const set = which === 'clean'
    ? REM_BENCHES.filter(b => b.land_status === 'clean')
    : REM_BENCHES;
  set.forEach(b => FieldGoldData.put(b));
  const nAvoid = set.filter(b => b.land_status === 'avoid').length;
  const nUnch  = set.filter(b => b.land_status === 'unchecked').length;
  el.textContent = 'Loaded ' + set.length + ' candidates ('
    + set.filter(b => b.land_status === 'clean').length + ' verified clean, '
    + nUnch + ' unchecked, ' + nAvoid + ' flagged avoid). '
    + 'Open the main app -> Sites -> Plan to see them.';
}
render();
</script>
</body></html>
"""

# ---------------------------------------------------------------------------
# Build BOTH outputs before writing EITHER.
#
# The ordering matters. If the HTML were written first and the data-layer write
# then failed -- missing markers, unwritable file, a typo in this script -- the
# repo would be left in exactly the drifted state this whole arrangement exists
# to prevent, and nothing would say so until someone read a map at a trailhead.
# So: construct both strings, fail on anything wrong, and only then write.
# ---------------------------------------------------------------------------
html_out = HTML.replace("__PAYLOAD__", payload)

data_js = open(DATA_JS, encoding="utf-8").read()
if JS_BEGIN not in data_js or JS_END not in data_js:
    sys.exit(
        "ERROR: could not find the BEGIN/END GENERATED markers in "
        f"{DATA_JS}.\nThe seed array is generated; the markers are how this "
        "script finds it. If they were removed or reworded, restore them "
        "rather than pasting an array in by hand -- a hand-pasted array is "
        "the drift this script exists to make impossible."
    )
head, _, rest = data_js.partition(JS_BEGIN)
_, _, tail = rest.partition(JS_END)
js_out = head + JS_BEGIN + "\n  var REM_BENCHES = " + payload + ";\n" + JS_END + tail

open(DST, "w", encoding="utf-8").write(html_out)
open(DATA_JS, "w", encoding="utf-8").write(js_out)

# Read both back off disk and confirm they carry the same twenty records. This
# is not paranoia about the filesystem; it is the assertion that makes "one
# payload, two files" a checked fact rather than a comment.
def _extract(path, decl):
    text = open(path, encoding="utf-8").read()
    hit = re.search(decl + r" REM_BENCHES = (\[.*?\]);", text, re.S)
    if not hit:
        sys.exit(f"ERROR: wrote {path} but cannot read REM_BENCHES back out of it")
    return json.loads(hit.group(1))

back_html = _extract(DST, "const")
back_js = _extract(DATA_JS, "var")
if back_html != back_js:
    sys.exit("ERROR: the two payloads disagree immediately after being written")
if back_html != out:
    sys.exit("ERROR: what landed on disk is not what this run computed")

print(f"wrote {DST}")
print(f"wrote {DATA_JS}  (generated region only)")
print(f"  clean={n_clean}  unchecked={n_unch}  avoid={n_avoid}")
print(f"  both files carry the same {len(back_js)} records")
print("  verified order:", ", ".join(b["profile"] for b in out))
