/* Adversarial test for the land-status schema in fieldgold-data.js.
 *
 * Runs under plain node with a fake localStorage and a fake `window`. No
 * browser, no DOM, no network.
 *
 * The point of this suite is not to show that the happy path works. It is to
 * show that the DANGEROUS direction fails: that nothing — a missing field, a
 * typo, a null, a number, an old record, a stale cache — can make unknown
 * ground read as clean. Run with `--mutate` to prove the suite can fail.
 */
'use strict';
const fs = require('fs');
const vm = require('vm');

// The default is derived from this file's own location, NOT hardcoded. It used
// to name an absolute path on the machine the suite was written on -- which
// existed there, held a DIFFERENT half-finished copy of fieldgold-data.js, and
// so reported green while testing bytes that were never shipped. On any other
// machine it would simply have thrown ENOENT. --src still overrides, which is
// what the mutation harness uses.
const path = require('path');
const SRC = process.argv.includes('--src')
  ? process.argv[process.argv.indexOf('--src') + 1]
  : path.join(path.dirname(__dirname), 'fieldgold-data.js');

const MUTATE = process.argv.includes('--mutate')
  ? process.argv[process.argv.indexOf('--mutate') + 1]
  : null;

// ------------------------------------------------------------------ harness

let PASS = 0;
const FAILS = [];
function check(name, cond, detail) {
  if (cond) { PASS++; console.log('  ok    ' + name); }
  else { FAILS.push(name); console.log('  FAIL  ' + name + (detail ? '  -- ' + detail : '')); }
}

function freshData() {
  // Fake localStorage: a plain object, string values only, like the real one.
  const store = {};
  const localStorage = {
    getItem: k => (Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: k => { delete store[k]; },
  };
  let code = fs.readFileSync(SRC, 'utf8');

  // ---- mutants: deliberate breakages, each of which SHOULD be caught ----
  if (MUTATE === 'default-clean') {
    // The single most dangerous edit anyone could make to this file.
    code = code.replace('return STATUS.UNCHECKED;\n  }\n\n  // Read the tier',
                        'return STATUS.CLEAN;\n  }\n\n  // Read the tier');
  } else if (MUTATE === 'unchecked-visitable') {
    code = code.replace("cls: 'unchecked', order: 1, visitable: false",
                        "cls: 'unchecked', order: 1, visitable: true");
  } else if (MUTATE === 'no-stamp') {
    code = code.replace("entry.land_status = statusOf(entry);", "/* stamp removed */");
  } else if (MUTATE === 'ignore-where') {
    code = code.replace("if (!where) return false;                // no predicate: clear the kind",
                        "return false;");
  } else if (MUTATE === 'sort-avoid-first') {
    code = code.replace("avoid: {\n      cls: 'avoid', order: 2",
                        "avoid: {\n      cls: 'avoid', order: -1");
  } else if (MUTATE === 'no-trim') {
    code = code.replace("var s = v.trim().toLowerCase();", "var s = v;");
  } else if (MUTATE) {
    throw new Error('unknown mutant: ' + MUTATE);
  }

  const sandbox = { window: {}, localStorage, Date, JSON, Array, Math, console };
  sandbox.global = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(code, sandbox, { filename: SRC });
  return sandbox.window.FieldGoldData;
}

const bench = (extra) => Object.assign({ kind: 'bench', lat: 61.7, lon: -149.2 }, extra);

// ------------------------------------------------------- A. the safe default

function test_unknown_never_reads_clean(D) {
  // Every one of these is a way a real record could arrive without a usable
  // status: written by an old build, hand-edited, corrupted, half-migrated.
  const junk = [
    bench({}),                                  // field absent entirely
    bench({ land_status: undefined }),
    bench({ land_status: null }),
    bench({ land_status: '' }),
    bench({ land_status: 'CLEAR' }),            // plausible typo for CLEAN
    bench({ land_status: 'cleanish' }),
    bench({ land_status: 'ok' }),
    bench({ land_status: 'verified' }),
    bench({ land_status: true }),
    bench({ land_status: 1 }),
    bench({ land_status: 0 }),
    bench({ land_status: ['clean'] }),
    bench({ land_status: { v: 'clean' } }),
    null, undefined, 42, 'clean', [],
  ];
  const bad = junk.filter(j => D.statusOf(j) === 'clean');
  check('no unknown/garbage value ever reads as clean',
        bad.length === 0, bad.length + ' of ' + junk.length + ' read clean');

  const allUnchecked = junk.every(j => D.statusOf(j) === 'unchecked');
  check('every unknown/garbage value reads as unchecked', allUnchecked);

  // And nothing in that list is routable.
  check('no unknown/garbage value is visitable',
        junk.every(j => D.isVisitable(j) === false));
}

function test_real_values_survive(D) {
  check('clean reads clean',       D.statusOf(bench({ land_status: 'clean' })) === 'clean');
  check('avoid reads avoid',       D.statusOf(bench({ land_status: 'avoid' })) === 'avoid');
  check('unchecked reads unchecked', D.statusOf(bench({ land_status: 'unchecked' })) === 'unchecked');
  // Case and whitespace are the sort of thing that creeps in through hand
  // edits and JSON round-trips. They should normalise, not degrade.
  check('CLEAN normalises',        D.statusOf(bench({ land_status: 'CLEAN' })) === 'clean');
  check('" Avoid " normalises',    D.statusOf(bench({ land_status: ' Avoid ' })) === 'avoid');
}

function test_visitable_is_strict(D) {
  check('clean is visitable',     D.isVisitable(bench({ land_status: 'clean' })) === true);
  check('unchecked is NOT visitable', D.isVisitable(bench({ land_status: 'unchecked' })) === false);
  check('avoid is NOT visitable', D.isVisitable(bench({ land_status: 'avoid' })) === false);
  check('isAvoid true only for avoid',
        D.isAvoid(bench({ land_status: 'avoid' })) === true &&
        D.isAvoid(bench({ land_status: 'clean' })) === false &&
        D.isAvoid(bench({})) === false);
}

// ----------------------------------------------------------- B. write path

function test_put_stamps_bench(D) {
  D.put(bench({ id: 'b1' }));
  const stored = D.get('bench').find(e => e.id === 'b1');
  check('put() stamps land_status onto a bench with none',
        stored && stored.land_status === 'unchecked',
        stored ? JSON.stringify(stored.land_status) : 'entry missing');

  D.put(bench({ id: 'b2', land_status: 'clean' }));
  check('put() preserves an explicit clean',
        D.get('bench').find(e => e.id === 'b2').land_status === 'clean');

  D.put(bench({ id: 'b3', land_status: 'sort-of-fine' }));
  check('put() rewrites a bogus value to unchecked, not clean',
        D.get('bench').find(e => e.id === 'b3').land_status === 'unchecked');
}

function test_put_leaves_other_kinds_alone(D) {
  D.put({ kind: 'photo', id: 'p1', lat: 61.7, lon: -149.2 });
  const p = D.get('photo')[0];
  check('put() does NOT invent a land status for a photo',
        p && !('land_status' in p));
}

// ------------------------------------------------- C. the data-loss scenario

function test_scoped_replace_preserves_rem(D) {
  // Set up the real situation: REM candidates with hard-won status, plus a
  // couple of the Bench Hunter's own cross-section benches.
  D.put(bench({ id: 'rem-bench-2',  source: 'REM', land_status: 'clean' }));
  D.put(bench({ id: 'rem-bench-14', source: 'REM', land_status: 'avoid' }));
  D.put(bench({ id: 'bh-1', source: 'benchhunter' }));

  // Bench Hunter re-syncs ITS benches. This is the call that used to wipe
  // everything.
  D.replaceKind('bench', [bench({ id: 'bh-9', source: 'benchhunter' })],
                { where: e => e.source !== 'REM' });

  const after = D.get('bench');
  const ids = after.map(e => e.id).sort();
  check('scoped replaceKind keeps both REM records',
        ids.includes('rem-bench-2') && ids.includes('rem-bench-14'), ids.join(','));
  check('scoped replaceKind drops the old bench-hunter record',
        !ids.includes('bh-1'), ids.join(','));
  check('scoped replaceKind adds the new bench-hunter record',
        ids.includes('bh-9'), ids.join(','));
  check('surviving REM status is intact (clean still clean, avoid still avoid)',
        after.find(e => e.id === 'rem-bench-2').land_status === 'clean' &&
        after.find(e => e.id === 'rem-bench-14').land_status === 'avoid');
  check('the re-synced bench-hunter record is stamped unchecked',
        after.find(e => e.id === 'bh-9').land_status === 'unchecked');
}

function test_unscoped_replace_still_clears(D) {
  // Backwards compatibility: two-arg calls elsewhere in the app must behave
  // exactly as before. index.html uses replaceKind('site', ...) this way.
  D.put({ kind: 'site', id: 's1', lat: 61.7, lon: -149.2 });
  D.put({ kind: 'site', id: 's2', lat: 61.7, lon: -149.2 });
  D.put(bench({ id: 'keepme', source: 'REM', land_status: 'clean' }));
  D.replaceKind('site', [{ id: 's9', lat: 61.7, lon: -149.2 }]);
  const sites = D.get('site').map(e => e.id).sort();
  check('unscoped replaceKind still clears the whole kind (2-arg compat)',
        sites.length === 1 && sites[0] === 's9', sites.join(','));
  check('unscoped replaceKind on one kind leaves another kind untouched',
        D.get('bench').some(e => e.id === 'keepme'));
}

// -------------------------------------------------------- D. ordering, counts

function test_sort_and_counts(D) {
  const list = [
    bench({ id: 'a', land_status: 'avoid' }),
    bench({ id: 'b' }),                            // unchecked by omission
    bench({ id: 'c', land_status: 'clean' }),
    bench({ id: 'd', land_status: 'avoid' }),
    bench({ id: 'e', land_status: 'clean' }),
  ];
  const order = D.sortByStatus(list).map(e => e.id).join('');
  check('sortByStatus is clean, then unchecked, then avoid',
        order === 'cebad', order);

  const c = D.statusCounts(list);
  check('statusCounts tallies correctly',
        c.clean === 2 && c.unchecked === 1 && c.avoid === 2 && c.total === 5,
        JSON.stringify(c));

  check('sortByStatus does not mutate the input order',
        list.map(e => e.id).join('') === 'abcde');
  check('sortByStatus survives an empty list and undefined',
        D.sortByStatus([]).length === 0 && D.sortByStatus().length === 0);
}

function test_meta_shape(D) {
  // Consumers index STATUS_META by tier and read .color/.label without
  // guarding. A missing key would throw at render time on the map.
  const ok = ['clean', 'unchecked', 'avoid'].every(k => {
    const m = D.STATUS_META[k];
    return m && typeof m.color === 'string' && typeof m.label === 'string'
             && typeof m.long === 'string' && typeof m.ink === 'string'
             && typeof m.order === 'number' && typeof m.visitable === 'boolean';
  });
  check('STATUS_META is complete for all three tiers', ok);
  check('statusMeta() on junk returns the unchecked meta, never undefined',
        D.statusMeta(null).cls === 'unchecked' &&
        D.statusMeta(bench({ land_status: 'nonsense' })).cls === 'unchecked');
}

// ---------------------------------------------------------------- E. round trip

function test_survives_json_round_trip(D) {
  // localStorage is strings. Anything that only lives in memory is a lie.
  D.put(bench({ id: 'rt', source: 'REM', land_status: 'avoid',
                status_label: 'MCO 549 — CLOSED to mineral entry' }));
  const raw = D.readAll();
  const again = JSON.parse(JSON.stringify(raw)).entries.find(e => e.id === 'rt');
  check('land_status survives the localStorage round trip',
        again && again.land_status === 'avoid' &&
        again.status_label === 'MCO 549 — CLOSED to mineral entry');
}

// -------------------------------------------------------------------- run

const TESTS = [
  test_unknown_never_reads_clean,
  test_real_values_survive,
  test_visitable_is_strict,
  test_put_stamps_bench,
  test_put_leaves_other_kinds_alone,
  test_scoped_replace_preserves_rem,
  test_unscoped_replace_still_clears,
  test_sort_and_counts,
  test_meta_shape,
  test_survives_json_round_trip,
];

console.log('land-status suite  src=' + SRC + (MUTATE ? '  MUTANT=' + MUTATE : ''));
for (const fn of TESTS) {
  // Per-test isolation: a fresh store each time, and a crash in one test must
  // not abort the rest and masquerade as coverage.
  try { fn(freshData()); }
  catch (exc) { FAILS.push(fn.name); console.log('  FAIL  ' + fn.name + ' threw ' + exc.message); }
}

console.log('');
console.log(PASS + ' passed, ' + FAILS.length + ' failed');
if (FAILS.length) { console.log('FAILED: ' + FAILS.join(', ')); process.exit(1); }
console.log('LAND-STATUS SUITE PASSED');
