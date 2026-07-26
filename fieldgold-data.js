/* ==========================================================================
   FieldGold shared data layer
   One common prospect record that every tool can write to and read from.
   Lives in same-origin localStorage — works because all four pages are on
   one site. Not a server: shared across tools on ONE device, not synced
   across devices. Export to a file (Field Brain) to move it between devices.

   Every entry has: id, kind, lat, lon, source, created, and kind-specific fields.
   kinds: 'site' (evaluated prospect), 'bench' (bench-hunter candidate),
          'occurrence' (map ARDF tap), 'photo' (photo analysis).

   ---------------------------------------------------------------------------
   LAND STATUS (added 2026-07-25)
   ---------------------------------------------------------------------------
   Bench entries carry a land-status tier saying whether the ground has been
   checked against DNR records and what was found:

       'clean'     checked, nothing found — no effective closing order, no
                   active lease, no park boundary
       'unchecked' NEVER CHECKED — status unknown
       'avoid'     checked, an encumbrance was found (closing order, lease,
                   park boundary, pending application)

   THE DEFAULT IS 'unchecked', AND THAT IS THE WHOLE POINT. A bench with no
   land_status field, an unrecognised value, a null, a typo, a number, or a
   record written by an older version of a tool — every one of those reads
   back as 'unchecked'. Nothing is ever promoted to 'clean' by accident. If
   you change statusOf() so an unknown value falls through to 'clean', you
   have converted a data gap into a green light on a page someone reads at a
   trailhead.

   'clean' means somebody did the work and wrote it down. Nothing else earns it.

   ---------------------------------------------------------------------------
   THE SEED ARRAY IS GENERATED. DO NOT HAND-EDIT IT.
   ---------------------------------------------------------------------------
   REM_BENCHES below sits between BEGIN/END GENERATED markers and is written by
   tools/build_loader.py, which writes the SAME payload into
   load_rem_benches.html. Two copies of twenty land-status calls, maintained by
   hand, is a drift bug waiting to happen: the page would say AVOID and the
   auto-seed would say nothing at all, on the same bench, on the same phone.
   One generator owns both. tests/test_seed_drift.py fails the build if they
   ever stop matching.
   ========================================================================== */
(function (global) {
  'use strict';

  var KEY = 'fieldgold_record';
  var fireAfterWrite = null; // assigned once the reactive layer is wired, below

  // ------------------------------------------------------------------ status

  var STATUS = { CLEAN: 'clean', UNCHECKED: 'unchecked', AVOID: 'avoid' };

  // order     — sort key, lowest first: clean, then unchecked, then avoid.
  // visitable — is it defensible to route someone here? ONLY 'clean' is true.
  //             'unchecked' is not "probably fine", it is "we do not know".
  var STATUS_META = {
    clean: {
      cls: 'clean', order: 0, visitable: true,
      label: 'CLEAN',
      long: 'Land status checked — no closing order, lease or park boundary found',
      color: '#4E9A5F', ink: '#0B140D'
    },
    unchecked: {
      cls: 'unchecked', order: 1, visitable: false,
      label: 'NOT CHECKED',
      long: 'Land status unknown — this candidate has never been run through the DNR check',
      color: '#D29A3A', ink: '#14110C'
    },
    avoid: {
      cls: 'avoid', order: 2, visitable: false,
      label: 'AVOID',
      long: 'Encumbered — a closing order, lease, park boundary or pending application was found',
      color: '#B2402F', ink: '#170B08'
    }
  };

  // Normalise anything at all into one of the three tiers.
  // Unknown input -> 'unchecked'. Never 'clean'.
  function normalizeStatus(v) {
    if (typeof v !== 'string') return STATUS.UNCHECKED;
    var s = v.trim().toLowerCase();
    if (s === STATUS.CLEAN || s === STATUS.AVOID || s === STATUS.UNCHECKED) return s;
    return STATUS.UNCHECKED;
  }

  // Read the tier off an entry. Safe on null / undefined / non-objects.
  function statusOf(entry) {
    if (!entry || typeof entry !== 'object') return STATUS.UNCHECKED;
    return normalizeStatus(entry.land_status);
  }

  // Display metadata for an entry's tier. Always returns an object.
  function statusMeta(entry) {
    return STATUS_META[statusOf(entry)];
  }

  function isAvoid(entry) { return statusOf(entry) === STATUS.AVOID; }

  // The one question routing code should ask before sending someone somewhere.
  // Deliberately strict: unchecked is NOT visitable.
  function isVisitable(entry) { return STATUS_META[statusOf(entry)].visitable; }

  // Stable sort: clean, then unchecked, then avoid. Ties keep input order.
  function sortByStatus(list) {
    return (list || [])
      .map(function (e, i) { return { e: e, i: i }; })
      .sort(function (a, b) {
        var d = STATUS_META[statusOf(a.e)].order - STATUS_META[statusOf(b.e)].order;
        return d !== 0 ? d : a.i - b.i;
      })
      .map(function (x) { return x.e; });
  }

  // Count each tier in a list. For "12 of 20 unchecked" style notices.
  function statusCounts(list) {
    var c = { clean: 0, unchecked: 0, avoid: 0, total: 0 };
    (list || []).forEach(function (e) { c[statusOf(e)]++; c.total++; });
    return c;
  }

  // ------------------------------------------------ state mining claims
  //
  // A SECOND register, asked separately, kept separate on purpose.
  //
  // `land_status` answers "did DNR's encumbrance battery find a closing order,
  // a leasehold order, a lease or a park closure on this point". It does NOT
  // answer "is there an active state MINING CLAIM on this point" — that is
  // layer ME112, and a bench can be clean on every encumbrance layer and still
  // sit inside somebody's claim. Folding the two into one tier would let a
  // claim hide behind a clean land-status call.
  //
  // Measured 2026-07-25 against DNR
  // Mapper/Mineral_Estate_Layers/MapServer/112 (State Mining Claim Poly, active)
  // and .../13 (pending): 22 active claims inside the reach envelope, 0 pending,
  // against ONE polygon in BLM's federal register over the same ground. The
  // claims are real and they are near. None of them contains a bench point.
  var STATE_CLAIM = { NONE: 'none', CLAIMED: 'claimed', UNCHECKED: 'unchecked' };

  var STATE_CLAIM_META = {
    none: {
      cls: 'none', label: 'NO STATE CLAIM ON THIS POINT',
      long: 'DNR ME112 (active state mining claims) returned nothing at this exact position',
      color: '#4E9A5F'
    },
    claimed: {
      cls: 'claimed', label: 'INSIDE A STATE MINING CLAIM',
      long: 'DNR ME112 returned an active state mining claim covering this position',
      color: '#B2402F'
    },
    unchecked: {
      cls: 'unchecked', label: 'STATE CLAIMS NOT CHECKED',
      long: 'The state mining-claim register has not been queried for this position',
      color: '#D29A3A'
    }
  };

  // Unknown input -> 'unchecked'. NEVER 'none'. Same invariant as
  // normalizeStatus, and for the same reason: on this screen "we did not ask"
  // and "we asked and the answer was no" must not render the same way.
  function normalizeStateClaim(v) {
    if (typeof v !== 'string') return STATE_CLAIM.UNCHECKED;
    var s = v.trim().toLowerCase();
    if (s === STATE_CLAIM.NONE || s === STATE_CLAIM.CLAIMED ||
        s === STATE_CLAIM.UNCHECKED) return s;
    return STATE_CLAIM.UNCHECKED;
  }

  function stateClaimOf(entry) {
    if (!entry || typeof entry !== 'object') return STATE_CLAIM.UNCHECKED;
    return normalizeStateClaim(entry.state_claim);
  }

  function stateClaimMeta(entry) {
    return STATE_CLAIM_META[stateClaimOf(entry)];
  }

  // A claim check has a shelf life. Claims can be staked any day, so a 'none'
  // with no date on it is not a result, it is a rumour. Returns null when the
  // record does not carry one, and the UI must say so rather than omit it.
  function stateClaimCheckedOn(entry) {
    if (!entry || typeof entry !== 'object') return null;
    var d = entry.state_claim_checked;
    return (typeof d === 'string' && d.trim()) ? d.trim() : null;
  }

  // ---------------------------------------------------- context for a position
  //
  // Given a position — a photo's GPS fix, say — and the bench records we have
  // land-status calls for, say what is honestly known about the ground under
  // that position.
  //
  // THE ASYMMETRY BELOW IS THE WHOLE DESIGN. Read it before changing anything.
  //
  //   AVOID PROPAGATES OUTWARD. The things that make a bench 'avoid' — a
  //   mineral closing order, a leasehold location order, a park boundary, a
  //   pending application — are AREAL. They cover polygons measured in square
  //   kilometres. A point 1 km from a point known to sit inside MCO 549 is
  //   very plausibly inside MCO 549 as well. So nearness to an 'avoid' bench
  //   raises the warning, and it does so even when a 'clean' bench is closer.
  //
  //   'CLEAN' DOES NOT PROPAGATE AT ALL. It was established by a
  //   point-in-polygon query against one coordinate. It says nothing about a
  //   coordinate 200 m away, which may sit inside an active claim that the
  //   checked point falls just outside of. THIS FUNCTION NEVER REPORTS A
  //   POSITION AS CLEAN. The most it will ever say is "the nearest point
  //   anybody checked came back clean, you are N metres from it, and that
  //   check does not extend to where you are standing."
  //
  // If you are here because the amber notices feel excessive and you want a
  // green tier for positions near clean benches: that is precisely the edit
  // that turns this file into a go-ahead on unverified ground. Don't.

  // The radii below are NOT guesses. They were set by measuring the twenty
  // checked candidates against each other:
  //
  //   nearest-neighbour spacing   min 56 m   median 196 m   max 971 m
  //   clean bench -> nearest avoid bench:  151, 739, 747, 947, 1066, 1650,
  //                                        1666, 2103 m
  //
  // The candidates sit in tight clusters ~3.3 km apart, and the clusters are
  // status-MIXED — REM-5 is clean and sits 151 m from REM-15, which is not.
  // An early draft of this used a flat 2000 m avoid radius. Against the real
  // geometry that flags SEVEN of the eight clean benches as encumbered, which
  // is not caution, it is a warning that fires everywhere and therefore gets
  // dismissed everywhere — including the once it is right. Numbers checked
  // before shipping, not after.
  //
  // So: an avoid bench controls when it is the NEAREST checked point, or when
  // it is close enough that boundary uncertainty dominates regardless of what
  // else is nearby. At 250 m exactly one clean bench (REM-5) is overridden,
  // and it is the one that genuinely should be.

  var AVOID_HARD_M     = 250;   // this close, an avoid bench overrides everything
  var AVOID_MENTION_M  = 2000;  // this close, it gets NAMED even when not controlling
  var CONTEXT_RADIUS_M = 1500;  // past this, no bench says anything about you

  function distanceM(lat1, lon1, lat2, lon2) {
    var R = 6371008.8, p = Math.PI / 180;
    var dLat = (lat2 - lat1) * p, dLon = (lon2 - lon1) * p;
    var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * p) * Math.cos(lat2 * p) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return 2 * R * Math.asin(Math.min(1, Math.sqrt(a)));
  }

  function finiteNum(v) { return typeof v === 'number' && isFinite(v); }

  // tier   — 'near_avoid' | 'near_clean' | 'unchecked' | 'no_position'
  // advice — may a model give "put your first pan here" for this position?
  //          ONLY false for near_avoid. The other three tiers are unknowns,
  //          not prohibitions, and a control that fires everywhere is a
  //          control that gets switched off.
  // NOTE none of the three non-avoid tiers is coloured differently from the
  // others. near_clean, unchecked and no_position all mean "nobody checked
  // where you are standing". Giving near_clean its own colour would encode a
  // safety difference that does not exist.
  function contextForPoint(lat, lon, list) {
    var AMBER = { color: '#D29A3A', ink: '#14110C' };
    var RUST  = { color: '#B2402F', ink: '#170B08' };

    if (!finiteNum(lat) || !finiteNum(lon)) {
      return {
        tier: 'no_position', advice: true, nearest: null, distance_m: null,
        in_pua: null, color: AMBER.color, ink: AMBER.ink,
        headline: 'NO LOCATION — land status not checked for this photo',
        detail: 'This photo has no GPS fix, so nothing can be said about ' +
                'whether the ground in it is open to mineral entry. Treat it ' +
                'as unchecked.'
      };
    }

    var benches = (list || get('bench')).filter(function (b) {
      return b && finiteNum(b.lat) && finiteNum(b.lon);
    });

    var nearAvoid = null, nearAny = null;
    benches.forEach(function (b) {
      var d = distanceM(lat, lon, b.lat, b.lon);
      if (!nearAny || d < nearAny.d) nearAny = { e: b, d: d };
      if (isAvoid(b) && (!nearAvoid || d < nearAvoid.d)) nearAvoid = { e: b, d: d };
    });

    function name(e) { return e.profile || e.id || 'a checked bench'; }

    // A named, distance-stamped mention of encumbered ground that is close but
    // not controlling. It goes in the detail of EVERY non-avoid tier, so the
    // reassuring-sounding cases never hide it.
    var mention = '';
    if (nearAvoid && nearAvoid.d <= AVOID_MENTION_M) {
      mention = ' Separately: encumbered ground (' + name(nearAvoid.e) + ', ' +
                Math.round(nearAvoid.d) + ' m away) is within walking distance ' +
                'of here, so a boundary is close. ' +
                (nearAvoid.e.status_label || '');
    }

    // 1. An avoid bench close enough that boundary uncertainty dominates
    //    overrides anything nearer. 2. Otherwise the NEAREST checked point is
    //    the most relevant evidence, and if it is encumbered, so are you,
    //    probably.
    var avoidControls = nearAvoid && (
      nearAvoid.d <= AVOID_HARD_M ||
      (nearAny && nearAny.e === nearAvoid.e && nearAvoid.d <= CONTEXT_RADIUS_M));

    if (avoidControls) {
      var a = nearAvoid.e;
      return {
        tier: 'near_avoid', advice: false, nearest: a,
        distance_m: Math.round(nearAvoid.d),
        in_pua: (typeof a.in_pua === 'boolean') ? a.in_pua : null,
        color: RUST.color, ink: RUST.ink,
        headline: 'AVOID — encumbered ground ' + Math.round(nearAvoid.d) +
                  ' m away (' + name(a) + ')',
        detail: (a.status_label || 'An encumbrance was found at the nearest ' +
                'checked point.') + ' ' + (a.status_detail || '') +
                ' Closing orders and leasehold orders cover areas, not points, ' +
                'so this very likely applies where you are standing too. ' +
                'Confirm in Alaska Mapper before working this ground.'
      };
    }

    if (nearAny && nearAny.d <= CONTEXT_RADIUS_M && statusOf(nearAny.e) === 'clean') {
      var c = nearAny.e;
      return {
        tier: 'near_clean', advice: true, nearest: c,
        distance_m: Math.round(nearAny.d),
        in_pua: (typeof c.in_pua === 'boolean') ? c.in_pua : null,
        color: AMBER.color, ink: AMBER.ink,
        headline: 'NOT CHECKED HERE — nearest checked point (' + name(c) + ', ' +
                  Math.round(nearAny.d) + ' m) came back clean',
        detail: 'That check was a point query against ' + name(c) +
                ', not against your position. It does not carry ' +
                Math.round(nearAny.d) + ' m. ' +
                (c.in_pua === true
                  ? 'The nearest checked point is inside Hatcher Pass ' +
                    'Management Area-East, where DNR allows recreational ' +
                    'panning with hand pick, shovel and pan except on valid ' +
                    'active claims — but the boundary is a boundary, and you ' +
                    'may be outside it.'
                  : 'The nearest checked point is OUTSIDE the Public Use Area, ' +
                    'so no recreational-panning permission is inherited here.') +
                mention
      };
    }

    return {
      tier: 'unchecked', advice: true, nearest: null, distance_m: null,
      in_pua: null, color: AMBER.color, ink: AMBER.ink,
      headline: 'NOT CHECKED — no land-status query covers this position',
      detail: 'No bench candidate within ' + CONTEXT_RADIUS_M + ' m of here ' +
              'has been run through the DNR check. Status is unknown, which ' +
              'is not the same as clear.' + mention
    };
  }

  // The block that gets prepended to the vision prompt. Kept here, next to the
  // rules it describes, so the text and the tiers cannot drift apart — and so
  // it can be tested under node with no browser.
  //
  // Worth being blunt about what this is: an INSTRUCTION TO A MODEL, which is
  // a request, not an enforcement mechanism. The thing that actually stops a
  // person reading pan advice on closed ground is the banner the app draws
  // from contextForPoint(), which no model output can suppress. This block
  // makes the answer better; the banner makes it safe.
  function landBriefForPrompt(ctx) {
    if (!ctx) return '';
    var out = 'LAND STATUS AT THIS POSITION (supplied by the app, not by you — ' +
              'treat it as fact and do not second-guess it):\n' +
              ctx.headline + '\n' + ctx.detail + '\n\n';
    if (ctx.advice === false) {
      out += 'BECAUSE THIS GROUND IS ENCUMBERED, YOUR ANSWER MUST CHANGE ' +
             'SHAPE:\n' +
             '- Open with the encumbrance above, in your own words, as the ' +
             'first thing the reader sees.\n' +
             '- Do NOT output a WHERE TO START section, and do NOT name a ' +
             'spot to put a pan, dig, or sample. Omit ALSO CHECK as well.\n' +
             '- You may describe what the photo shows and still output the ' +
             'INDICATORS block — that is data, not an instruction to dig.\n' +
             '- Do not soften, hedge, or offer a workaround for the ' +
             'encumbrance, and do not speculate that it might not apply.\n\n';
    } else {
      out += 'Land status here is UNKNOWN, not clear. Give your normal ' +
             'analysis, and in CAUTION state plainly that the legal status of ' +
             'this ground has not been verified and must be checked in Alaska ' +
             'Mapper before any digging.\n\n';
    }
    return out;
  }

  // Stamp BOTH registers so they are genuinely part of the stored record,
  // rather than something every reader has to remember to default. Applied to
  // benches on write. Other kinds are left alone — a photo has no land status.
  //
  // state_claim is stamped here too, and for the same reason land_status is: a
  // bench record that reaches storage with no state_claim key is a record whose
  // claim status is decided by whoever reads it next. Both defaults are the
  // pessimistic one — 'unchecked', never 'clean', never 'none'.
  function stampStatus(entry) {
    if (entry && typeof entry === 'object' && entry.kind === 'bench') {
      entry.land_status = statusOf(entry);
      entry.state_claim = stateClaimOf(entry);
    }
    return entry;
  }

  // ------------------------------------------------------------- storage I/O

  function readAll() {
    try {
      var raw = localStorage.getItem(KEY);
      if (!raw) return { updated: 0, entries: [] };
      var parsed = JSON.parse(raw);
      if (!parsed || !Array.isArray(parsed.entries)) return { updated: 0, entries: [] };
      return parsed;
    } catch (e) {
      return { updated: 0, entries: [] };
    }
  }

  function writeAll(rec) {
    try {
      rec.updated = Date.now();
      localStorage.setItem(KEY, JSON.stringify(rec));
      if (typeof fireAfterWrite === 'function') fireAfterWrite();
      return true;
    } catch (e) {
      return false;
    }
  }

  // Return entries, optionally filtered by kind ('site','bench','occurrence','photo')
  function get(kind) {
    var entries = readAll().entries;
    if (!kind) return entries;
    return entries.filter(function (e) { return e.kind === kind; });
  }

  // Upsert one entry by id (replaces if id exists, else adds). Returns the entry.
  function put(entry) {
    if (!entry || !entry.id) { entry.id = 'e' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }
    if (!entry.created) entry.created = new Date().toISOString();
    stampStatus(entry);
    var rec = readAll();
    var i = rec.entries.findIndex(function (e) { return e.id === entry.id; });
    if (i >= 0) rec.entries[i] = entry; else rec.entries.push(entry);
    writeAll(rec);
    return entry;
  }

  // Replace entries of one kind at once (used when a tool re-syncs its set).
  // Leaves other kinds untouched.
  //
  // opts.where — optional predicate. When given, ONLY existing entries of this
  // kind for which where(entry) is true are cleared; the rest survive.
  //
  // This exists because a tool that owns part of a kind must not delete the
  // part it does not own. The Bench Hunter re-syncs its own cross-section
  // benches; the REM candidates share the 'bench' kind and carry land status
  // that took DNR queries to establish and that nothing else can regenerate.
  // Wiping them turns verified ground into a blank list with no error message.
  function replaceKind(kind, entries, opts) {
    var where = opts && typeof opts.where === 'function' ? opts.where : null;
    var rec = readAll();
    rec.entries = rec.entries.filter(function (e) {
      if (e.kind !== kind) return true;        // other kinds always survive
      if (!where) return false;                // no predicate: clear the kind
      return !where(e);                        // predicate: keep non-matching
    });
    (entries || []).forEach(function (e) {
      e.kind = kind;
      if (!e.id) e.id = 'e' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
      if (!e.created) e.created = new Date().toISOString();
      stampStatus(e);
      rec.entries.push(e);
    });
    writeAll(rec);
    return rec.entries.filter(function (e) { return e.kind === kind; });
  }

  function remove(id) {
    var rec = readAll();
    rec.entries = rec.entries.filter(function (e) { return e.id !== id; });
    writeAll(rec);
  }

  // ---- REM terrace candidates (auto-seeded once; separate 'source:REM') ----
  //
  // GENERATED. Everything between the two markers below is written by
  // tools/build_loader.py from the STATUS table in that file, and the same
  // payload is written into load_rem_benches.html. Hand-editing either copy
  // makes them disagree; tests/test_seed_drift.py exists to catch exactly that.

  // ==== BEGIN GENERATED — tools/build_loader.py ==========================
  var REM_BENCHES = [
 {
  "kind": "bench",
  "id": "rem-bench-2",
  "lat": 61.72047,
  "lon": -149.23426,
  "nearest": 5.9,
  "profile": "REM-2",
  "source": "REM",
  "area_m2": 46483,
  "height_sd_m": 2.8,
  "nearest_gold_m": null,
  "geo_score": 0.433,
  "geo_rank": 2,
  "rank": 1,
  "score": 1,
  "land_status": "clean",
  "status_label": "CLEAN \u2014 verified (full 16-layer battery)",
  "status_detail": "No mineral closing order, no leasehold location order, no active or pending claim, no lease, no park closure. Inside Hatcher Pass Management Area-East, where DNR allows recreational panning with hand pick, shovel and pan. Well log 86093 (720 m S) shows bedrock at 20 ft under 17 ft of sand and gravel \u2014 the best structural setting on the reach for hand work.",
  "in_pua": true,
  "status_checked": "2026-07-21",
  "status_depth": "full",
  "state_claim": "none",
  "state_claim_checked": "2026-07-21",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 9/11 \u2014 DNR ArcGIS point-in-polygon, 16-layer battery, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. CLEAN \u2014 verified (full 16-layer battery)"
 },
 {
  "kind": "bench",
  "id": "rem-bench-13",
  "lat": 61.73573,
  "lon": -149.23237,
  "nearest": 4.6,
  "profile": "REM-13",
  "source": "REM",
  "area_m2": 15738,
  "height_sd_m": 1.2,
  "nearest_gold_m": null,
  "geo_score": 0.279,
  "geo_rank": 13,
  "rank": 2,
  "score": 2,
  "land_status": "clean",
  "status_label": "CLEAN \u2014 verified (full 16-layer battery)",
  "status_detail": "Same clean result as REM-2 on every layer. Inside Hatcher Pass Management Area-East, so recreational panning is allowed. No well-log control on depth to bedrock here.",
  "in_pua": true,
  "status_checked": "2026-07-21",
  "status_depth": "full",
  "state_claim": "none",
  "state_claim_checked": "2026-07-21",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 9/11 \u2014 DNR ArcGIS point-in-polygon, 16-layer battery, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. CLEAN \u2014 verified (full 16-layer battery)"
 },
 {
  "kind": "bench",
  "id": "rem-bench-7",
  "lat": 61.74385,
  "lon": -149.23236,
  "nearest": 6.0,
  "profile": "REM-7",
  "source": "REM",
  "area_m2": 40026,
  "height_sd_m": 2.8,
  "nearest_gold_m": null,
  "geo_score": 0.401,
  "geo_rank": 7,
  "rank": 3,
  "score": 3,
  "land_status": "clean",
  "status_label": "CLEAN \u2014 verified, but OUTSIDE the Public Use Area",
  "status_detail": "Clean on all encumbrance layers, and specifically NOT inside ADL 229824. But it falls outside Hatcher Pass Management Area-East, so it does NOT inherit the PUA panning permission \u2014 the permission here is ordinary state-land rules, not the PUA fact sheet. Three well logs within 560 m show 120\u2013215 ft of boulders and gravel with bedrock never reached. Pan the bench gravel; there is no reachable bedrock target.",
  "in_pua": false,
  "status_checked": "2026-07-21",
  "status_depth": "full",
  "state_claim": "none",
  "state_claim_checked": "2026-07-21",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 9/11 \u2014 DNR ArcGIS point-in-polygon, 16-layer battery, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. CLEAN \u2014 verified, but OUTSIDE the Public Use Area"
 },
 {
  "kind": "bench",
  "id": "rem-bench-1",
  "lat": 61.77256,
  "lon": -149.20759,
  "nearest": 14.0,
  "profile": "REM-1",
  "source": "REM",
  "area_m2": 59888,
  "height_sd_m": 3.3,
  "nearest_gold_m": null,
  "geo_score": 0.46,
  "geo_rank": 1,
  "rank": 4,
  "score": 4,
  "land_status": "clean",
  "status_label": "CLEAN \u2014 8-layer check, inside the Public Use Area",
  "status_detail": "Zero hits on all seven encumbrance layers run (mineral order, leasehold location order, active claim, pending claim, prospecting site, mineral-estate permit/lease, land-estate permit/lease), and inside Hatcher Pass Management Area-East, so recreational panning with hand pick, shovel and pan is allowed. Largest terrace on the whole list at 59,888 m\u00b2, but it sits ~14 m above the channel \u2014 the highest of any candidate \u2014 so it is the oldest surface here and may be a glacial deposit rather than a river terrace. NOT checked against the eight rarer Tier-2 layers (native allotment, Mental Health Trust, federal action, easement, land disposal, management agreement, agreement/settlement, restricted-use authorization).",
  "in_pua": true,
  "status_checked": "2026-07-25",
  "status_depth": "tier1",
  "state_claim": "none",
  "state_claim_checked": "2026-07-25",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 16 \u2014 DNR ArcGIS point-in-polygon, 8-layer Tier-1 battery, every CLEAN call re-fetched independently, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. CLEAN \u2014 8-layer check, inside the Public Use Area"
 },
 {
  "kind": "bench",
  "id": "rem-bench-5",
  "lat": 61.71518,
  "lon": -149.23229,
  "nearest": 3.9,
  "profile": "REM-5",
  "source": "REM",
  "area_m2": 1002,
  "height_sd_m": 0.3,
  "nearest_gold_m": 665,
  "geo_score": 0.423,
  "geo_rank": 5,
  "rank": 5,
  "score": 5,
  "land_status": "clean",
  "status_label": "CLEAN \u2014 8-layer check, inside the Public Use Area",
  "status_detail": "Zero hits on all seven encumbrance layers run; inside Hatcher Pass Management Area-East. Small terrace (1,002 m\u00b2) but only 3.9 m above the channel and very flat (height SD 0.3 m) \u2014 the tightest, lowest-standing surface on the list, which is the geometry a young fluvial terrace should have. NOT checked against the eight rarer Tier-2 layers.",
  "in_pua": true,
  "status_checked": "2026-07-25",
  "status_depth": "tier1",
  "state_claim": "none",
  "state_claim_checked": "2026-07-25",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 16 \u2014 DNR ArcGIS point-in-polygon, 8-layer Tier-1 battery, every CLEAN call re-fetched independently, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. CLEAN \u2014 8-layer check, inside the Public Use Area"
 },
 {
  "kind": "bench",
  "id": "rem-bench-11",
  "lat": 61.76431,
  "lon": -149.21701,
  "nearest": 4.9,
  "profile": "REM-11",
  "source": "REM",
  "area_m2": 920,
  "height_sd_m": 0.9,
  "nearest_gold_m": 1040,
  "geo_score": 0.341,
  "geo_rank": 11,
  "rank": 6,
  "score": 6,
  "land_status": "clean",
  "status_label": "CLEAN \u2014 8-layer check, inside the Public Use Area",
  "status_detail": "Zero hits on all seven encumbrance layers run; inside Hatcher Pass Management Area-East. 920 m\u00b2, 4.9 m above the channel. Note that REM-19, only ~140 m to the southwest, falls OUTSIDE the PUA \u2014 the boundary runs between them, so do not assume the permission carries across the gap. NOT checked against the eight rarer Tier-2 layers.",
  "in_pua": true,
  "status_checked": "2026-07-25",
  "status_depth": "tier1",
  "state_claim": "none",
  "state_claim_checked": "2026-07-25",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 16 \u2014 DNR ArcGIS point-in-polygon, 8-layer Tier-1 battery, every CLEAN call re-fetched independently, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. CLEAN \u2014 8-layer check, inside the Public Use Area"
 },
 {
  "kind": "bench",
  "id": "rem-bench-20",
  "lat": 61.76936,
  "lon": -149.21246,
  "nearest": 4.1,
  "profile": "REM-20",
  "source": "REM",
  "area_m2": 8948,
  "height_sd_m": 0.6,
  "nearest_gold_m": null,
  "geo_score": 0.245,
  "geo_rank": 20,
  "rank": 7,
  "score": 7,
  "land_status": "clean",
  "status_label": "CLEAN \u2014 8-layer check, inside the Public Use Area",
  "status_detail": "Zero hits on all seven encumbrance layers run; inside Hatcher Pass Management Area-East. Smallest terrace on the list (8,948 m\u00b2 is misleading \u2014 height SD 0.6 m, 4.1 m above channel) and the furthest upstream of the clean set. NOT checked against the eight rarer Tier-2 layers.",
  "in_pua": true,
  "status_checked": "2026-07-25",
  "status_depth": "tier1",
  "state_claim": "none",
  "state_claim_checked": "2026-07-25",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 16 \u2014 DNR ArcGIS point-in-polygon, 8-layer Tier-1 battery, every CLEAN call re-fetched independently, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. CLEAN \u2014 8-layer check, inside the Public Use Area"
 },
 {
  "kind": "bench",
  "id": "rem-bench-19",
  "lat": 61.76387,
  "lon": -149.21967,
  "nearest": 5.9,
  "profile": "REM-19",
  "source": "REM",
  "area_m2": 10437,
  "height_sd_m": 1.8,
  "nearest_gold_m": null,
  "geo_score": 0.252,
  "geo_rank": 19,
  "rank": 8,
  "score": 8,
  "land_status": "clean",
  "status_label": "CLEAN \u2014 8-layer check, but OUTSIDE the Public Use Area",
  "status_detail": "Zero hits on all eight layers run, INCLUDING the park-boundary layer: this point is not inside Hatcher Pass Management Area-East. That is not an encumbrance, but it means the PUA fact sheet's recreational-panning permission does NOT apply here \u2014 the same caveat as REM-7. REM-11 is ~140 m northeast and IS inside the PUA; the boundary runs between the two, and a hand-held GPS fix is not accurate enough to stand on that line with confidence. If you want PUA cover, work REM-11 and leave this one. NOT checked against the eight rarer Tier-2 layers.",
  "in_pua": false,
  "status_checked": "2026-07-25",
  "status_depth": "tier1",
  "state_claim": "none",
  "state_claim_checked": "2026-07-25",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 16 \u2014 DNR ArcGIS point-in-polygon, 8-layer Tier-1 battery, every CLEAN call re-fetched independently, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. CLEAN \u2014 8-layer check, but OUTSIDE the Public Use Area"
 },
 {
  "kind": "bench",
  "id": "rem-bench-8",
  "lat": 61.75663,
  "lon": -149.22915,
  "nearest": 5.2,
  "profile": "REM-8",
  "source": "REM",
  "area_m2": 36644,
  "height_sd_m": 1.6,
  "nearest_gold_m": null,
  "geo_score": 0.384,
  "geo_rank": 8,
  "rank": 9,
  "score": 9,
  "land_status": "avoid",
  "status_label": "SKIP on exposure \u2014 pending application ADL 229824 (not a closure)",
  "status_detail": "Clean on every mineral-estate layer. The one hit is ADL 229824 (Fishhook Renewable Energy LLC), case type verbatim \"NEG LEASE NON-COMP (553)\", special code \"INDUSTRL/COMMERCIAL (5015)\", status \"ADDTL INFO REQUESTED (10)\" \u2014 a PENDING application, not an active lease. This point is also inside the PUA, so recreational panning is otherwise allowed. Graded avoid on exposure only, the same call already made for REM-6. Worth raising on the DMLW call: at 36,644 m\u00b2 and 5.2 m above the channel this is the third-best geometry on the list, and it is being set aside for a reason that may not survive one phone call.",
  "in_pua": true,
  "status_checked": "2026-07-25",
  "status_depth": "tier1",
  "state_claim": "none",
  "state_claim_checked": "2026-07-25",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 16 \u2014 DNR ArcGIS point-in-polygon, 8-layer Tier-1 battery, every CLEAN call re-fetched independently, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. SKIP on exposure \u2014 pending application ADL 229824 (not a closure)"
 },
 {
  "kind": "bench",
  "id": "rem-bench-9",
  "lat": 61.75472,
  "lon": -149.22742,
  "nearest": 17.7,
  "profile": "REM-9",
  "source": "REM",
  "area_m2": 951,
  "height_sd_m": 0.5,
  "nearest_gold_m": 628,
  "geo_score": 0.356,
  "geo_rank": 9,
  "rank": 10,
  "score": 10,
  "land_status": "avoid",
  "status_label": "SKIP on exposure \u2014 pending application ADL 229824 (not a closure)",
  "status_detail": "Same single hit as REM-8: pending ADL 229824, status 10. Inside the PUA. Graded avoid on exposure only. Weak geometry regardless (951 m\u00b2, 17.7 m above the channel \u2014 the highest surface on the list, most likely glacial rather than fluvial).",
  "in_pua": true,
  "status_checked": "2026-07-25",
  "status_depth": "tier1",
  "state_claim": "none",
  "state_claim_checked": "2026-07-25",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 16 \u2014 DNR ArcGIS point-in-polygon, 8-layer Tier-1 battery, every CLEAN call re-fetched independently, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. SKIP on exposure \u2014 pending application ADL 229824 (not a closure)"
 },
 {
  "kind": "bench",
  "id": "rem-bench-16",
  "lat": 61.75209,
  "lon": -149.22982,
  "nearest": 9.2,
  "profile": "REM-16",
  "source": "REM",
  "area_m2": 13057,
  "height_sd_m": 1.5,
  "nearest_gold_m": null,
  "geo_score": 0.265,
  "geo_rank": 16,
  "rank": 11,
  "score": 11,
  "land_status": "avoid",
  "status_label": "SKIP on exposure \u2014 pending application ADL 229824 (not a closure)",
  "status_detail": "Same single hit as REM-8: pending ADL 229824, status 10. Inside the PUA. Graded avoid on exposure only. 13,057 m\u00b2, 9.2 m above the channel.",
  "in_pua": true,
  "status_checked": "2026-07-25",
  "status_depth": "tier1",
  "state_claim": "none",
  "state_claim_checked": "2026-07-25",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 16 \u2014 DNR ArcGIS point-in-polygon, 8-layer Tier-1 battery, every CLEAN call re-fetched independently, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. SKIP on exposure \u2014 pending application ADL 229824 (not a closure)"
 },
 {
  "kind": "bench",
  "id": "rem-bench-17",
  "lat": 61.75055,
  "lon": -149.23067,
  "nearest": 8.2,
  "profile": "REM-17",
  "source": "REM",
  "area_m2": 12960,
  "height_sd_m": 1.8,
  "nearest_gold_m": null,
  "geo_score": 0.265,
  "geo_rank": 17,
  "rank": 12,
  "score": 12,
  "land_status": "avoid",
  "status_label": "SKIP on exposure \u2014 pending application ADL 229824 (not a closure)",
  "status_detail": "Same single hit as REM-8: pending ADL 229824, status 10. Inside the PUA. Graded avoid on exposure only. 12,960 m\u00b2, 8.2 m above the channel.",
  "in_pua": true,
  "status_checked": "2026-07-25",
  "status_depth": "tier1",
  "state_claim": "none",
  "state_claim_checked": "2026-07-25",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 16 \u2014 DNR ArcGIS point-in-polygon, 8-layer Tier-1 battery, every CLEAN call re-fetched independently, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. SKIP on exposure \u2014 pending application ADL 229824 (not a closure)"
 },
 {
  "kind": "bench",
  "id": "rem-bench-6",
  "lat": 61.75312,
  "lon": -149.23328,
  "nearest": 10.6,
  "profile": "REM-6",
  "source": "REM",
  "area_m2": 905,
  "height_sd_m": 0.8,
  "nearest_gold_m": 651,
  "geo_score": 0.42,
  "geo_rank": 6,
  "rank": 13,
  "score": 13,
  "land_status": "avoid",
  "status_label": "SKIP \u2014 inside a pending application",
  "status_detail": "Clean on every hard encumbrance, BUT the point falls inside ADL 229824 (Fishhook Renewable Energy LLC), status 10 \u2014 a PENDING application, case type verbatim \"NEG LEASE NON-COMP (553)\". Not an active lease, so it does not close the ground today. Skipped on exposure, not prohibition: ground inside a live application footprint can change status without notice. Also outside the PUA.",
  "in_pua": false,
  "status_checked": "2026-07-21",
  "status_depth": "full",
  "state_claim": "none",
  "state_claim_checked": "2026-07-21",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 9/11 \u2014 DNR ArcGIS point-in-polygon, 16-layer battery, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. SKIP \u2014 inside a pending application"
 },
 {
  "kind": "bench",
  "id": "rem-bench-3",
  "lat": 61.70343,
  "lon": -149.23852,
  "nearest": 7.9,
  "profile": "REM-3",
  "source": "REM",
  "area_m2": 864,
  "height_sd_m": 0.3,
  "nearest_gold_m": 643,
  "geo_score": 0.428,
  "geo_rank": 3,
  "rank": 14,
  "score": 14,
  "land_status": "avoid",
  "status_label": "LLO 5 \u2014 minerals by lease only",
  "status_detail": "Inside LLO 5 \"Little Susitna River Corridor\" (Leasehold Location Order, Active/Restricted). Minerals are acquirable only by lease, not by staking a claim. Whether LLO 5 bars RECREATIONAL hand panning is UNRESOLVED \u2014 see the open question below.",
  "in_pua": false,
  "status_checked": "2026-07-21",
  "status_depth": "full",
  "state_claim": "none",
  "state_claim_checked": "2026-07-21",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 9/11 \u2014 DNR ArcGIS point-in-polygon, 16-layer battery, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. LLO 5 \u2014 minerals by lease only"
 },
 {
  "kind": "bench",
  "id": "rem-bench-4",
  "lat": 61.70348,
  "lon": -149.23747,
  "nearest": 8.7,
  "profile": "REM-4",
  "source": "REM",
  "area_m2": 1002,
  "height_sd_m": 0.4,
  "nearest_gold_m": 664,
  "geo_score": 0.423,
  "geo_rank": 4,
  "rank": 15,
  "score": 15,
  "land_status": "avoid",
  "status_label": "LLO 5 \u2014 minerals by lease only",
  "status_detail": "Inside LLO 5 \"Little Susitna River Corridor\", same as REM-3. Recreational panning status unresolved.",
  "in_pua": false,
  "status_checked": "2026-07-21",
  "status_depth": "full",
  "state_claim": "none",
  "state_claim_checked": "2026-07-21",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 9/11 \u2014 DNR ArcGIS point-in-polygon, 16-layer battery, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. LLO 5 \u2014 minerals by lease only"
 },
 {
  "kind": "bench",
  "id": "rem-bench-10",
  "lat": 61.69466,
  "lon": -149.24903,
  "nearest": 9.2,
  "profile": "REM-10",
  "source": "REM",
  "area_m2": 30540,
  "height_sd_m": 2.1,
  "nearest_gold_m": null,
  "geo_score": 0.353,
  "geo_rank": 10,
  "rank": 16,
  "score": 16,
  "land_status": "avoid",
  "status_label": "LLO 5 \u2014 minerals by lease only",
  "status_detail": "Inside LLO 5 \"Little Susitna River Corridor\" (CASE_ID \"LLO 5\", ACTIVE (50), RESTRICTED (RD)). Clean on every other layer run, and NOT inside the PUA. 30,540 m\u00b2 at 9.2 m above the channel \u2014 the best geometry of the six LLO 5 candidates, and the one with most to gain if the DMLW call comes back permissive. Recreational panning status unresolved.",
  "in_pua": false,
  "status_checked": "2026-07-25",
  "status_depth": "tier1",
  "state_claim": "none",
  "state_claim_checked": "2026-07-25",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 16 \u2014 DNR ArcGIS point-in-polygon, 8-layer Tier-1 battery, every CLEAN call re-fetched independently, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. LLO 5 \u2014 minerals by lease only"
 },
 {
  "kind": "bench",
  "id": "rem-bench-12",
  "lat": 61.70423,
  "lon": -149.23742,
  "nearest": 8.3,
  "profile": "REM-12",
  "source": "REM",
  "area_m2": 17068,
  "height_sd_m": 1.0,
  "nearest_gold_m": null,
  "geo_score": 0.285,
  "geo_rank": 12,
  "rank": 17,
  "score": 17,
  "land_status": "avoid",
  "status_label": "LLO 5 \u2014 minerals by lease only",
  "status_detail": "Inside LLO 5 \"Little Susitna River Corridor\", same as REM-3. Recreational panning status unresolved.",
  "in_pua": false,
  "status_checked": "2026-07-21",
  "status_depth": "full",
  "state_claim": "none",
  "state_claim_checked": "2026-07-21",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 9/11 \u2014 DNR ArcGIS point-in-polygon, 16-layer battery, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. LLO 5 \u2014 minerals by lease only"
 },
 {
  "kind": "bench",
  "id": "rem-bench-15",
  "lat": 61.71404,
  "lon": -149.23074,
  "nearest": 7.2,
  "profile": "REM-15",
  "source": "REM",
  "area_m2": 13221,
  "height_sd_m": 1.3,
  "nearest_gold_m": null,
  "geo_score": 0.266,
  "geo_rank": 15,
  "rank": 18,
  "score": 18,
  "land_status": "avoid",
  "status_label": "LLO 5 \u2014 minerals by lease only",
  "status_detail": "Inside LLO 5 \"Little Susitna River Corridor\" (ACTIVE/RESTRICTED). Clean on every other layer run, and NOT inside the PUA. 13,221 m\u00b2, 7.2 m above the channel. Recreational panning status unresolved.",
  "in_pua": false,
  "status_checked": "2026-07-25",
  "status_depth": "tier1",
  "state_claim": "none",
  "state_claim_checked": "2026-07-25",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 16 \u2014 DNR ArcGIS point-in-polygon, 8-layer Tier-1 battery, every CLEAN call re-fetched independently, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. LLO 5 \u2014 minerals by lease only"
 },
 {
  "kind": "bench",
  "id": "rem-bench-18",
  "lat": 61.71062,
  "lon": -149.2329,
  "nearest": 3.7,
  "profile": "REM-18",
  "source": "REM",
  "area_m2": 11363,
  "height_sd_m": 0.4,
  "nearest_gold_m": null,
  "geo_score": 0.257,
  "geo_rank": 18,
  "rank": 19,
  "score": 19,
  "land_status": "avoid",
  "status_label": "LLO 5 \u2014 minerals by lease only (and inside the PUA)",
  "status_detail": "Inside LLO 5 \"Little Susitna River Corridor\" (ACTIVE/RESTRICTED) AND inside Hatcher Pass Management Area-East. That overlap is exactly the unresolved question: the PUA fact sheet allows recreational panning, LLO 5 restricts mineral acquisition to lease. This is the single best point to put to DMLW on the phone, because the answer decides six candidates at once. 11,363 m\u00b2, only 3.7 m above the channel and very flat (height SD 0.4 m) \u2014 the lowest and flattest surface of any candidate on the list.",
  "in_pua": true,
  "status_checked": "2026-07-25",
  "status_depth": "tier1",
  "state_claim": "none",
  "state_claim_checked": "2026-07-25",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 16 \u2014 DNR ArcGIS point-in-polygon, 8-layer Tier-1 battery, every CLEAN call re-fetched independently, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. LLO 5 \u2014 minerals by lease only (and inside the PUA)"
 },
 {
  "kind": "bench",
  "id": "rem-bench-14",
  "lat": 61.70224,
  "lon": -149.23989,
  "nearest": 4.8,
  "profile": "REM-14",
  "source": "REM",
  "area_m2": 13466,
  "height_sd_m": 0.8,
  "nearest_gold_m": null,
  "geo_score": 0.267,
  "geo_rank": 14,
  "rank": 20,
  "score": 20,
  "land_status": "avoid",
  "status_label": "MCO 549 \u2014 CLOSED to mineral entry",
  "status_detail": "Inside Mineral Closing Order 549, \"Hatcher Pass / Government Peak Ski Area\". This is the hardest closure of any candidate on the list. Do not work this ground.",
  "in_pua": false,
  "status_checked": "2026-07-21",
  "status_depth": "full",
  "state_claim": "none",
  "state_claim_checked": "2026-07-21",
  "state_claim_register": "DNR ME112 active / ME13 pending, Mapper/Mineral_Estate_Layers",
  "state_claim_proximity": "unknown",
  "status_source": "HATCHER_SU_RESEARCH_LOG.md Thread 9/11 \u2014 DNR ArcGIS point-in-polygon, 16-layer battery, positive-control verified",
  "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required. MCO 549 \u2014 CLOSED to mineral entry"
 }
];
  // ==== END GENERATED ====================================================

  // The version suffix is part of the contract, not decoration. v1 seeded
  // twenty benches carrying NO land status at all, and any device that ran it
  // still holds them: twenty cyan diamonds on the map, twelve of which sit on
  // ground since found encumbered (MCO 549, LLO 5, pending ADL 229824). If this
  // flag had stayed at v1 those devices would never have seen the status, and
  // the whole point of shipping it would have been missed on the only devices
  // that matter. Bump it whenever the seed payload's MEANING changes, not
  // whenever the file changes.
  var SEED_FLAG    = 'fieldgold_rem_seeded_v2';
  var SEED_FLAG_V1 = 'fieldgold_rem_seeded_v1';

  // Seed REM benches ONE time per seed version.
  //
  // Two things it must do, and one it must not:
  //   ADD    — on a device that has never seeded, write all twenty.
  //   UPGRADE — on a device that seeded v1, overwrite the fields the generator
  //            owns on the records still present. That is the migration: it is
  //            how a phone already carrying statusless benches learns that
  //            twelve of them are encumbered.
  //   NOT RESURRECT — if v1 seeded a bench and it is gone now, the user deleted
  //            it. Deletion is a decision and this function does not overrule
  //            it. (A device that never seeded has no deletions to respect, so
  //            the missing-record case there means "new", not "deleted".)
  //
  // Bench Hunter benches are never touched: they have source !== 'REM'.
  function seedREM() {
    try {
      if (localStorage.getItem(SEED_FLAG)) return false;
      var seededBefore = !!localStorage.getItem(SEED_FLAG_V1);
      var rec = readAll();
      var byId = {};
      rec.entries.forEach(function (e) {
        if (e && e.source === 'REM' && e.id) byId[e.id] = e;
      });
      var added = 0, upgraded = 0;
      REM_BENCHES.forEach(function (b) {
        var cur = byId[b.id];
        if (cur) {
          // The seed owns every key it carries. Anything the record has that
          // the seed does not — `created`, a user's own additions — survives.
          var before = JSON.stringify(cur);
          Object.keys(b).forEach(function (k) { cur[k] = b[k]; });
          stampStatus(cur);
          if (JSON.stringify(cur) !== before) upgraded++;
        } else if (!seededBefore) {
          rec.entries.push(stampStatus(Object.assign({}, b)));
          added++;
        }
      });
      if (added || upgraded) writeAll(rec);
      localStorage.setItem(SEED_FLAG, String(Date.now()));
      return added + upgraded;
    } catch (e) { return false; }
  }

  // ---- Reactive change notification (kills the refresh ritual) ----
  //
  // The guards on addEventListener are not defensive noise: this file is loaded
  // under plain node by tests/test_land_status.js and
  // tests/test_photo_land_context.js, in a sandbox with a fake localStorage and
  // no DOM at all. Without them the whole data layer would fail to parse there
  // and two suites would go dark. The listeners themselves are exercised for
  // real in the browser by tests/test_reactive_refresh.py.
  var listeners = [];
  function onChange(fn) { if (typeof fn === 'function') listeners.push(fn); }
  function fire() { listeners.forEach(function (fn) { try { fn(); } catch (e) {} }); }
  // Fire local listeners after any same-tab write, and cross-tab via storage event.
  if (global && typeof global.addEventListener === 'function') {
    global.addEventListener('storage', function (e) { if (e.key === KEY) fire(); });
    // Re-fire when the page comes BACK from the back/forward cache, where the
    // DOM was restored wholesale and may be showing markers built from a record
    // another tab has since changed.
    //
    // Guarded on e.persisted, which is the whole point of the listener. pageshow
    // also fires on every ordinary load, right after the page has just drawn
    // itself from current data — so an unguarded fire() means every page draws
    // twice on arrival. That is invisible for markers, which are cleared and
    // redrawn, and NOT invisible for the status log, which appends: 'site
    // dropped — no usable coordinates' printed once per bad record turns into
    // twice per bad record, and the reader has no way to tell five malformed
    // sites from ten.
    global.addEventListener('pageshow', function (e) { if (e && e.persisted) fire(); });
  }
  if (typeof document !== 'undefined' && typeof document.addEventListener === 'function') {
    document.addEventListener('visibilitychange', function () { if (!document.hidden) fire(); });
  }

  fireAfterWrite = fire; // same-tab writes now notify
  seedREM();

  global.FieldGoldData = {
    get: get,
    put: put,
    replaceKind: replaceKind,
    remove: remove,
    readAll: readAll,
    KEY: KEY,

    // reactive refresh
    onChange: onChange,

    // the generated seed
    seedREM: seedREM,
    REM_BENCHES: REM_BENCHES,
    SEED_FLAG: SEED_FLAG,
    SEED_FLAG_V1: SEED_FLAG_V1,

    // land status
    STATUS: STATUS,
    STATUS_META: STATUS_META,
    statusOf: statusOf,
    statusMeta: statusMeta,
    isAvoid: isAvoid,
    isVisitable: isVisitable,
    sortByStatus: sortByStatus,
    statusCounts: statusCounts,

    // state mining claims — a SECOND register, deliberately not merged above
    STATE_CLAIM: STATE_CLAIM,
    STATE_CLAIM_META: STATE_CLAIM_META,
    stateClaimOf: stateClaimOf,
    stateClaimMeta: stateClaimMeta,
    stateClaimCheckedOn: stateClaimCheckedOn,

    // position -> what is known about the ground there
    contextForPoint: contextForPoint,
    landBriefForPrompt: landBriefForPrompt,
    distanceM: distanceM,
    AVOID_HARD_M: AVOID_HARD_M,
    AVOID_MENTION_M: AVOID_MENTION_M,
    CONTEXT_RADIUS_M: CONTEXT_RADIUS_M
  };
})(window);
