/* ==========================================================================
   FieldGold shared data layer
   One common prospect record that every tool can write to and read from.
   Lives in same-origin localStorage — works because all four pages are on
   one site. Not a server: shared across tools on ONE device, not synced
   across devices. Export to a file (Field Brain) to move it between devices.

   Every entry has: id, kind, lat, lon, source, created, and kind-specific fields.
   kinds: 'site' (evaluated prospect), 'bench' (bench-hunter candidate),
          'occurrence' (map ARDF tap), 'photo' (photo analysis).
   ========================================================================== */
(function (global) {
  'use strict';

  var KEY = 'fieldgold_record';
  var fireAfterWrite = null; // set once listeners wired

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
    var rec = readAll();
    var i = rec.entries.findIndex(function (e) { return e.id === entry.id; });
    if (i >= 0) rec.entries[i] = entry; else rec.entries.push(entry);
    writeAll(rec);
    return entry;
  }

  // Replace ALL entries of one kind at once (used when a tool re-syncs its set).
  // Leaves other kinds untouched.
  function replaceKind(kind, entries) {
    var rec = readAll();
    rec.entries = rec.entries.filter(function (e) { return e.kind !== kind; });
    (entries || []).forEach(function (e) {
      e.kind = kind;
      if (!e.id) e.id = 'e' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
      if (!e.created) e.created = new Date().toISOString();
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
  var REM_BENCHES = [{"kind": "bench", "id": "rem-bench-1", "lat": 61.77256, "lon": -149.20759, "nearest": 14.0, "profile": "REM-1", "source": "REM", "area_m2": 59888, "height_sd_m": 3.3, "nearest_gold_m": null, "rank": 1, "score": 0.46, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-2", "lat": 61.72047, "lon": -149.23426, "nearest": 5.9, "profile": "REM-2", "source": "REM", "area_m2": 46483, "height_sd_m": 2.8, "nearest_gold_m": null, "rank": 2, "score": 0.433, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-3", "lat": 61.70343, "lon": -149.23852, "nearest": 7.9, "profile": "REM-3", "source": "REM", "area_m2": 864, "height_sd_m": 0.3, "nearest_gold_m": 643, "rank": 3, "score": 0.428, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-4", "lat": 61.70348, "lon": -149.23747, "nearest": 8.7, "profile": "REM-4", "source": "REM", "area_m2": 1002, "height_sd_m": 0.4, "nearest_gold_m": 664, "rank": 4, "score": 0.423, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-5", "lat": 61.71518, "lon": -149.23229, "nearest": 3.9, "profile": "REM-5", "source": "REM", "area_m2": 1002, "height_sd_m": 0.3, "nearest_gold_m": 665, "rank": 5, "score": 0.423, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-6", "lat": 61.75312, "lon": -149.23328, "nearest": 10.6, "profile": "REM-6", "source": "REM", "area_m2": 905, "height_sd_m": 0.8, "nearest_gold_m": 651, "rank": 6, "score": 0.42, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-7", "lat": 61.74385, "lon": -149.23236, "nearest": 6.0, "profile": "REM-7", "source": "REM", "area_m2": 40026, "height_sd_m": 2.8, "nearest_gold_m": null, "rank": 7, "score": 0.401, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-8", "lat": 61.75663, "lon": -149.22915, "nearest": 5.2, "profile": "REM-8", "source": "REM", "area_m2": 36644, "height_sd_m": 1.6, "nearest_gold_m": null, "rank": 8, "score": 0.384, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-9", "lat": 61.75472, "lon": -149.22742, "nearest": 17.7, "profile": "REM-9", "source": "REM", "area_m2": 951, "height_sd_m": 0.5, "nearest_gold_m": 628, "rank": 9, "score": 0.356, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-10", "lat": 61.69466, "lon": -149.24903, "nearest": 9.2, "profile": "REM-10", "source": "REM", "area_m2": 30540, "height_sd_m": 2.1, "nearest_gold_m": null, "rank": 10, "score": 0.353, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-11", "lat": 61.76431, "lon": -149.21701, "nearest": 4.9, "profile": "REM-11", "source": "REM", "area_m2": 920, "height_sd_m": 0.9, "nearest_gold_m": 1040, "rank": 11, "score": 0.341, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-12", "lat": 61.70423, "lon": -149.23742, "nearest": 8.3, "profile": "REM-12", "source": "REM", "area_m2": 17068, "height_sd_m": 1.0, "nearest_gold_m": null, "rank": 12, "score": 0.285, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-13", "lat": 61.73573, "lon": -149.23237, "nearest": 4.6, "profile": "REM-13", "source": "REM", "area_m2": 15738, "height_sd_m": 1.2, "nearest_gold_m": null, "rank": 13, "score": 0.279, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-14", "lat": 61.70224, "lon": -149.23989, "nearest": 4.8, "profile": "REM-14", "source": "REM", "area_m2": 13466, "height_sd_m": 0.8, "nearest_gold_m": null, "rank": 14, "score": 0.267, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-15", "lat": 61.71404, "lon": -149.23074, "nearest": 7.2, "profile": "REM-15", "source": "REM", "area_m2": 13221, "height_sd_m": 1.3, "nearest_gold_m": null, "rank": 15, "score": 0.266, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-16", "lat": 61.75209, "lon": -149.22982, "nearest": 9.2, "profile": "REM-16", "source": "REM", "area_m2": 13057, "height_sd_m": 1.5, "nearest_gold_m": null, "rank": 16, "score": 0.265, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-17", "lat": 61.75055, "lon": -149.23067, "nearest": 8.2, "profile": "REM-17", "source": "REM", "area_m2": 12960, "height_sd_m": 1.8, "nearest_gold_m": null, "rank": 17, "score": 0.265, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-18", "lat": 61.71062, "lon": -149.2329, "nearest": 3.7, "profile": "REM-18", "source": "REM", "area_m2": 11363, "height_sd_m": 0.4, "nearest_gold_m": null, "rank": 18, "score": 0.257, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-19", "lat": 61.76387, "lon": -149.21967, "nearest": 5.9, "profile": "REM-19", "source": "REM", "area_m2": 10437, "height_sd_m": 1.8, "nearest_gold_m": null, "rank": 19, "score": 0.252, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}, {"kind": "bench", "id": "rem-bench-20", "lat": 61.76936, "lon": -149.21246, "nearest": 4.1, "profile": "REM-20", "source": "REM", "area_m2": 8948, "height_sd_m": 0.6, "nearest_gold_m": null, "rank": 20, "score": 0.245, "note": "REM terrace candidate \u2014 geomorphically derived, ground-truth required"}];
  var SEED_FLAG = 'fieldgold_rem_seeded_v1';
  // Seed REM benches ONE time. Respects deletions: once seeded, never re-adds.
  // Won't touch Bench Hunter benches (those have source!=='REM').
  function seedREM() {
    try {
      if (localStorage.getItem(SEED_FLAG)) return false;
      var rec = readAll();
      var haveREM = {};
      rec.entries.forEach(function (e) { if (e.source === 'REM') haveREM[e.id] = 1; });
      var added = 0;
      REM_BENCHES.forEach(function (b) {
        if (!haveREM[b.id]) { rec.entries.push(Object.assign({}, b)); added++; }
      });
      if (added) writeAll(rec);
      localStorage.setItem(SEED_FLAG, String(Date.now()));
      return added;
    } catch (e) { return false; }
  }

  // ---- Reactive change notification (kills the refresh ritual) ----
  var listeners = [];
  function onChange(fn) { if (typeof fn === 'function') listeners.push(fn); }
  function fire() { listeners.forEach(function (fn) { try { fn(); } catch (e) {} }); }
  // Fire local listeners after any same-tab write, and cross-tab via storage event.
  window.addEventListener('storage', function (e) { if (e.key === KEY) fire(); });
  // Also re-fire when the page is shown again (bfcache / tab refocus).
  window.addEventListener('pageshow', function () { fire(); });
  document.addEventListener('visibilitychange', function () { if (!document.hidden) fire(); });

  fireAfterWrite = fire; // same-tab writes now notify
  seedREM();

  global.FieldGoldData = {
    get: get,
    put: put,
    replaceKind: replaceKind,
    remove: remove,
    readAll: readAll,
    onChange: onChange,
    seedREM: seedREM,
    KEY: KEY
  };
})(window);
