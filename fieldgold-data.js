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

  global.FieldGoldData = {
    get: get,
    put: put,
    replaceKind: replaceKind,
    remove: remove,
    readAll: readAll,
    KEY: KEY
  };
})(window);
