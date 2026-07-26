/* Adversarial test for contextForPoint() / landBriefForPrompt().
 *
 * The unit suite next door proves the three-tier schema is safe. This one
 * proves the DIFFERENT question is answered safely: "what is known about the
 * ground under this position", which is what the photo analyser asks before it
 * sends a picture and a persona to a vision model.
 *
 * The dangerous direction here is not "unknown reads as clean". It is
 * "somewhere NEAR a clean point reads as clean", and "an avoid bench is
 * out-voted by a closer clean one". Both are tested below, in both directions.
 *
 * Run with --mutate <name> to prove the suite can actually fail.
 *   node tests/test_photo_land_context.js
 *   node tests/test_photo_land_context.js --mutate clean-propagates
 */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

// Resolve from THIS file, not the cwd. (Same lesson as tools/build_loader.py:
// a test that only passes from one directory is a test you stop running.)
const ROOT = path.dirname(__dirname);
const SRC = process.argv.includes('--src')
  ? process.argv[process.argv.indexOf('--src') + 1]
  : path.join(ROOT, 'fieldgold-data.js');

const MUTATE = process.argv.includes('--mutate')
  ? process.argv[process.argv.indexOf('--mutate') + 1]
  : null;

let PASS = 0;
const FAILS = [];
function check(name, cond, detail) {
  if (cond) { PASS++; console.log('  ok    ' + name); }
  else { FAILS.push(name); console.log('  FAIL  ' + name + (detail ? '  -- ' + detail : '')); }
}

function load() {
  const store = {};
  const localStorage = {
    getItem: k => (Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: k => { delete store[k]; },
  };
  let code = fs.readFileSync(SRC, 'utf8');

  // ---- mutants: each one SHOULD be caught by something below ----
  if (MUTATE === 'clean-propagates') {
    // The single most dangerous edit available here: promote "near a clean
    // point" into an actual clean verdict.
    code = code.replace("tier: 'near_clean', advice: true", "tier: 'clean', advice: true");
  } else if (MUTATE === 'avoid-not-nearest') {
    // Drop the "nearest checked point controls" clause, so an avoid bench that
    // is the closest thing to you stops firing once it is past AVOID_HARD_M.
    code = code.replace(
      '(nearAny && nearAny.e === nearAvoid.e && nearAvoid.d <= CONTEXT_RADIUS_M));',
      'false);');
  } else if (MUTATE === 'avoid-hard-tiny') {
    code = code.replace('var AVOID_HARD_M     = 250;', 'var AVOID_HARD_M     = 5;');
  } else if (MUTATE === 'mention-dropped') {
    // Silently stop naming nearby encumbered ground in the non-avoid tiers.
    // This is the quiet version of "never soften a land-status warning".
    code = code.replace('if (nearAvoid && nearAvoid.d <= AVOID_MENTION_M) {',
                        'if (false) {');
  } else if (MUTATE === 'advice-on-avoid') {
    code = code.replace("tier: 'near_avoid', advice: false", "tier: 'near_avoid', advice: true");
  } else if (MUTATE === 'no-position-guard') {
    code = code.replace('if (!finiteNum(lat) || !finiteNum(lon)) {', 'if (false) {');
  } else if (MUTATE === 'brief-drops-refusal') {
    code = code.replace("'- Do NOT output a WHERE TO START section, and do NOT name a ' +\n             'spot to put a pan, dig, or sample. Omit ALSO CHECK as well.\\n' +", "");
  } else if (MUTATE === 'typo-status-is-clean') {
    // Treat anything that is not literally 'avoid' as good enough for the
    // reassuring tier — so 'cleen' or a null reads as near_clean.
    code = code.replace("statusOf(nearAny.e) === 'clean'", "statusOf(nearAny.e) !== 'avoid'");
  } else if (MUTATE) {
    console.error('unknown mutant: ' + MUTATE); process.exit(2);
  }

  const sandbox = { window: {}, localStorage, console, Date, Math, JSON, isFinite };
  sandbox.global = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(code.replace('})(window);', '})(this.window);'), sandbox);
  return sandbox.window.FieldGoldData;
}

// ------------------------------------------------------------------ fixtures
// Real coordinates from the REM work, so the distances in these tests are the
// distances that actually occur on this reach.
const REM2  = { kind: 'bench', id: 'rem-bench-2',  profile: 'REM-2',  lat: 61.72047, lon: -149.23426,
                land_status: 'clean', status_label: 'CLEAN — verified (full 16-layer battery)',
                status_detail: 'No closing order.', in_pua: true };
const REM14 = { kind: 'bench', id: 'rem-bench-14', profile: 'REM-14', lat: 61.73900, lon: -149.24800,
                land_status: 'avoid', status_label: 'AVOID — inside MCO 549, closed to mineral entry',
                status_detail: 'Mineral closing order 549.', in_pua: true };

// A point offset north from `b` by roughly `m` metres.
function north(b, m) { return { lat: b.lat + m / 111320, lon: b.lon }; }

const TIERS = ['near_avoid', 'near_clean', 'unchecked', 'no_position'];

// ---------------------------------------------------------------------- tests

function t_no_position(D) {
  const bad = [[null, null], [undefined, undefined], [NaN, -149.2], [61.7, NaN],
               ['61.72', '-149.23'], [{}, []], [Infinity, -149.2]];
  let allNo = true, sawClean = false;
  bad.forEach(([a, b]) => {
    const c = D.contextForPoint(a, b, [REM2, REM14]);
    if (c.tier !== 'no_position') allNo = false;
    if (/\bCLEAN\b/.test(c.headline) && c.tier !== 'no_position') sawClean = true;
  });
  check('every unusable coordinate returns no_position', allNo);
  check('no_position never claims clean', !sawClean);
  check('no_position says so in the headline',
        /NO LOCATION/i.test(D.contextForPoint(null, null, []).headline));
}

function t_on_avoid_ground(D) {
  const c = D.contextForPoint(REM14.lat, REM14.lon, [REM2, REM14]);
  check('standing on an avoid bench returns near_avoid', c.tier === 'near_avoid', c.tier);
  check('near_avoid forbids pan advice', c.advice === false);
  check('near_avoid names the bench', /REM-14/.test(c.headline), c.headline);
  check('near_avoid carries the real encumbrance text', /MCO 549/.test(c.detail));
}

function t_avoid_beats_a_closer_clean(D) {
  // THE test. Inside AVOID_HARD_M an encumbrance out-votes a NEARER clean
  // bench, because closing orders are areal and the clean check was a point.
  // Stand on a clean bench with an avoid bench 200 m off.
  const clean = Object.assign({}, REM2, { profile: 'REM-CLOSE' });
  const near  = Object.assign({}, REM14, north(REM2, 200), { profile: 'REM-NEAR' });
  const c = D.contextForPoint(clean.lat, clean.lon, [clean, near]);
  check('an avoid bench 200 m out beats a clean bench 0 m away',
        c.tier === 'near_avoid' && c.advice === false, c.tier);
  check('  ...and the warning names the AVOID bench, not the clean one',
        /REM-NEAR/.test(c.headline), c.headline);
}

function t_nearest_checked_point_controls(D) {
  // Past AVOID_HARD_M an avoid bench still controls when it is the nearest
  // checked point at all — the only evidence you have says encumbered.
  const far = Object.assign({}, REM14, north(REM14, 1000), { profile: 'REM-SOLE' });
  const c = D.contextForPoint(REM14.lat, REM14.lon, [far]);
  check('a lone avoid bench 1000 m out still controls', c.tier === 'near_avoid', c.tier);
  check('  ...and refuses advice', c.advice === false);

  // ...but it stops controlling once a CLEAN bench is nearer and it is past
  // the hard radius. That is the change the real geometry forced: at a flat
  // 2000 m, seven of the eight clean benches read AVOID.
  const clean = Object.assign({}, REM2, { profile: 'REM-CLEAN' });
  const away  = Object.assign({}, REM14, north(REM2, 1200), { profile: 'REM-1200' });
  const c2 = D.contextForPoint(clean.lat, clean.lon, [clean, away]);
  check('an avoid bench 1200 m out does NOT control when a clean one is nearer',
        c2.tier === 'near_clean', c2.tier);
}

function t_mention_never_drops_a_warning(D) {
  // Not controlling is not the same as not mentioned. Every non-avoid tier
  // must still NAME encumbered ground inside AVOID_MENTION_M, with a distance.
  const clean = Object.assign({}, REM2, { profile: 'REM-CLEAN' });
  const away  = Object.assign({}, REM14, north(REM2, 1200), { profile: 'REM-1200' });
  const c = D.contextForPoint(clean.lat, clean.lon, [clean, away]);
  check('near_clean still names the nearby encumbered bench',
        /REM-1200/.test(c.detail), c.detail);
  const m = /(\d+) m away/.exec(c.detail);
  check('near_clean gives its distance, and it is the right one',
        !!m && Math.abs(Number(m[1]) - 1200) <= 5, m ? m[1] : 'no distance');
  check('near_clean carries the encumbrance label too',
        /MCO 549/.test(c.detail), c.detail);

  // unchecked tier: an avoid bench past CONTEXT_RADIUS_M but inside
  // AVOID_MENTION_M does not control, and must not vanish either.
  const out = Object.assign({}, REM14, { profile: 'REM-OUT' });
  const here = north(out, 1700);
  const c2 = D.contextForPoint(here.lat, here.lon, [out]);
  check('an avoid bench at 1700 m does not control', c2.tier === 'unchecked', c2.tier);
  check('  ...but the unchecked detail still names it', /REM-OUT/.test(c2.detail), c2.detail);

  // ...and past AVOID_MENTION_M it genuinely says nothing.
  const far = north(out, 2500);
  const c3 = D.contextForPoint(far.lat, far.lon, [out]);
  check('past the mention radius nothing is claimed either way',
        c3.tier === 'unchecked' && !/REM-OUT/.test(c3.detail), c3.detail);
}

function t_near_clean_is_not_clean(D) {
  const here = north(REM2, 100);
  const c = D.contextForPoint(here.lat, here.lon, [REM2]);
  check('100 m from a clean bench is near_clean, NOT clean',
        c.tier === 'near_clean', c.tier);
  check('no tier in this function is ever literally "clean"',
        TIERS.indexOf(c.tier) >= 0 && c.tier !== 'clean' && c.tier !== 'visitable');
  check('near_clean says out loud that the check does not reach here',
        /does not carry/i.test(c.detail), c.detail);
  check('near_clean headline leads with NOT CHECKED HERE',
        /^NOT CHECKED HERE/.test(c.headline), c.headline);
  check('near_clean and unchecked share a colour (no false distinction)',
        c.color === D.contextForPoint(0, 0, []).color, c.color);
}

function t_radii(D) {
  const justOut = north(REM2, D.CONTEXT_RADIUS_M + 50);
  check('a clean bench beyond the context radius says nothing',
        D.contextForPoint(justOut.lat, justOut.lon, [REM2]).tier === 'unchecked');
  const avoidOut = north(REM14, D.CONTEXT_RADIUS_M + 50);
  check('an avoid bench beyond the context radius does not control',
        D.contextForPoint(avoidOut.lat, avoidOut.lon, [REM14]).tier === 'unchecked');
  const avoidIn = north(REM14, D.CONTEXT_RADIUS_M - 50);
  check('an avoid bench just inside the context radius does fire',
        D.contextForPoint(avoidIn.lat, avoidIn.lon, [REM14]).tier === 'near_avoid');

  // The hard radius must beat a clean bench sitting exactly on the position.
  const clean = Object.assign({}, REM2, { profile: 'C' });
  const inHard  = Object.assign({}, REM14, north(REM2, D.AVOID_HARD_M - 50), { profile: 'A' });
  const outHard = Object.assign({}, REM14, north(REM2, D.AVOID_HARD_M + 50), { profile: 'A' });
  check('inside AVOID_HARD_M an avoid bench overrides a nearer clean one',
        D.contextForPoint(clean.lat, clean.lon, [clean, inHard]).tier === 'near_avoid');
  check('outside AVOID_HARD_M it does not (but is still mentioned)',
        D.contextForPoint(clean.lat, clean.lon, [clean, outHard]).tier === 'near_clean');

  check('the ordering of the three radii is hard < context < mention',
        D.AVOID_HARD_M < D.CONTEXT_RADIUS_M && D.CONTEXT_RADIUS_M < D.AVOID_MENTION_M,
        [D.AVOID_HARD_M, D.CONTEXT_RADIUS_M, D.AVOID_MENTION_M].join(' / '));

  // The reason these are the numbers they are. A flat 2 km avoid radius reads
  // 7 of the 8 real clean benches as encumbered; the hard radius must stay well
  // under the observed clean->avoid separations (min 151 m is the exception
  // that SHOULD fire).
  check('AVOID_HARD_M stays under the second-smallest real clean/avoid gap',
        D.AVOID_HARD_M < 739, String(D.AVOID_HARD_M));
}

function t_garbage_records(D) {
  const junk = [null, undefined, {}, { lat: 'x', lon: 'y' }, { lat: 61.72 },
                { lat: NaN, lon: NaN }];
  let threw = false, c = null;
  try { c = D.contextForPoint(REM2.lat, REM2.lon, junk); } catch (e) { threw = true; }
  check('junk bench records do not throw', !threw);
  check('junk bench records yield unchecked, not a verdict', c && c.tier === 'unchecked');
  check('an empty bench list yields unchecked',
        D.contextForPoint(REM2.lat, REM2.lon, []).tier === 'unchecked');
}

function t_typo_status_never_reassures(D) {
  const typo = Object.assign({}, REM2, { land_status: 'cleen' });
  const here = north(typo, 50);
  const c = D.contextForPoint(here.lat, here.lon, [typo]);
  check('a bench with a typo\'d status does not produce near_clean',
        c.tier === 'unchecked', c.tier);
  const nulled = Object.assign({}, REM2, { land_status: null });
  const c2 = D.contextForPoint(here.lat, here.lon, [nulled]);
  check('a bench with a null status does not produce near_clean',
        c2.tier === 'unchecked', c2.tier);
}

function t_brief(D) {
  const avoid = D.contextForPoint(REM14.lat, REM14.lon, [REM14]);
  const b = D.landBriefForPrompt(avoid);
  check('the avoid brief forbids WHERE TO START explicitly',
        /Do NOT output a WHERE TO START/.test(b), b.slice(0, 120));
  check('the avoid brief forbids naming a spot to dig',
        /do NOT name a[\s\S]*spot to put a pan/.test(b));
  check('the avoid brief forbids offering a workaround',
        /do not speculate that it might not apply/i.test(b));
  check('the avoid brief carries the encumbrance itself', /MCO 549/.test(b));

  const unk = D.contextForPoint(0, 0, []);
  const b2 = D.landBriefForPrompt(unk);
  check('the unknown brief says unknown is not clear',
        /UNKNOWN, not clear/.test(b2));
  check('the unknown brief still demands the CAUTION line',
        /CAUTION/.test(b2));
  check('the unknown brief does NOT carry the avoid refusal',
        !/Do NOT output a WHERE TO START/.test(b2));
  check('a null context yields an empty brief, not the word undefined',
        D.landBriefForPrompt(null) === '');
}

function t_distance_sanity(D) {
  // 0.01 deg of latitude is ~1113 m anywhere.
  const d = D.distanceM(61.72, -149.23, 61.73, -149.23);
  check('distanceM is right to within 1% on a known separation',
        Math.abs(d - 1113) < 12, String(Math.round(d)));
  check('distanceM is zero for a point on itself',
        D.distanceM(61.72, -149.23, 61.72, -149.23) < 0.001);
}

function t_fuzz_invariants(D) {
  // 3000 random arrangements. Four invariants must hold in every one of them:
  //   - if any avoid bench is inside AVOID_HARD_M, the tier is near_avoid and
  //     advice is refused;
  //   - if the NEAREST bench is an avoid bench inside CONTEXT_RADIUS_M, ditto;
  //   - if any avoid bench is inside AVOID_MENTION_M, it is named in the
  //     detail whatever the tier — a warning is never simply dropped;
  //   - the tier is never 'clean', whatever the arrangement.
  let seed = 20260725;
  const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
  let bad = 0, badNearest = 0, badTier = 0, badMention = 0, mentions = 0;
  let sawAvoid = 0, sawClean = 0, sawUn = 0;
  for (let i = 0; i < 3000; i++) {
    const n = 1 + Math.floor(rnd() * 6);
    const list = [];
    for (let j = 0; j < n; j++) {
      list.push({
        kind: 'bench', id: 'b' + j, profile: 'B' + j,
        lat: 61.70 + rnd() * 0.06, lon: -149.28 + rnd() * 0.08,
        land_status: ['clean', 'avoid', 'unchecked'][Math.floor(rnd() * 3)],
      });
    }
    const lat = 61.70 + rnd() * 0.06, lon = -149.28 + rnd() * 0.08;
    const c = D.contextForPoint(lat, lon, list);
    const withD = list.map(b => ({ b, d: D.distanceM(lat, lon, b.lat, b.lon) }))
                      .sort((x, y) => x.d - y.d);
    const avoids = withD.filter(x => x.b.land_status === 'avoid');

    if (avoids.length && avoids[0].d <= D.AVOID_HARD_M &&
        !(c.tier === 'near_avoid' && c.advice === false)) bad++;
    if (withD[0].b.land_status === 'avoid' && withD[0].d <= D.CONTEXT_RADIUS_M &&
        !(c.tier === 'near_avoid' && c.advice === false)) badNearest++;
    if (avoids.length && avoids[0].d <= D.AVOID_MENTION_M) {
      mentions++;
      const nm = avoids[0].b.profile;
      if (!(new RegExp(nm + '\\b').test(c.headline + ' ' + c.detail))) badMention++;
    }
    if (TIERS.indexOf(c.tier) < 0) badTier++;
    if (c.tier === 'near_avoid') sawAvoid++;
    else if (c.tier === 'near_clean') sawClean++;
    else sawUn++;
  }
  check('fuzz: an avoid bench inside the hard radius ALWAYS wins', bad === 0, bad + ' violations');
  check('fuzz: a nearest-and-inside-context avoid bench ALWAYS wins',
        badNearest === 0, badNearest + ' violations');
  check('fuzz: an avoid bench inside the mention radius is ALWAYS named',
        badMention === 0 && mentions > 0, badMention + '/' + mentions + ' dropped');
  check('fuzz: the tier is always one of the four', badTier === 0);
  check('fuzz: the run actually exercised all three outcomes',
        sawAvoid > 0 && sawClean > 0 && sawUn > 0,
        `avoid=${sawAvoid} clean=${sawClean} other=${sawUn}`);
}

const TESTS = [t_no_position, t_on_avoid_ground, t_avoid_beats_a_closer_clean,
               t_nearest_checked_point_controls, t_mention_never_drops_a_warning,
               t_near_clean_is_not_clean, t_radii, t_garbage_records,
               t_typo_status_never_reassures, t_brief, t_distance_sanity,
               t_fuzz_invariants];

console.log('photo land-context suite  src=' + SRC + (MUTATE ? '  MUTANT=' + MUTATE : ''));
for (const fn of TESTS) {
  try { fn(load()); }
  catch (exc) { FAILS.push(fn.name); console.log('  FAIL  ' + fn.name + ' threw ' + exc.message); }
}
console.log('');
console.log(PASS + ' passed, ' + FAILS.length + ' failed');
if (FAILS.length) { console.log('FAILED: ' + FAILS.join(', ')); process.exit(1); }
console.log('PHOTO LAND-CONTEXT SUITE PASSED');
