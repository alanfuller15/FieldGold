// BUMP THIS ON EVERY CHANGE TO A CACHED FILE.
//
// AND BUMPING IT ONLY DELIVERS TO ONE OF THE TWO DISTRIBUTIONS. This file is
// the entire update path on GitHub Pages and is INERT in the iOS shell:
// `navigator.serviceWorker` does not exist under `capacitor://localhost`, so
// index.html's `in navigator` guard short-circuits and this worker never
// registers — silently, with no error and nothing on screen. Measured on the
// simulator and again on the physical iPhone 2026-07-28 (STATE.md). In the
// shell the web assets are already bundle-local, so offline works by
// construction and this cache is not needed; what changes is DELIVERY. A phone
// running the app gets a fix only via `npx cap sync` + rebuild + install.
// Green on one distribution is not evidence about the other, and a bumped
// version with no rebuild ships the fix to browsers and to nobody's phone.
//
// v9 (2026-07-29): warnings are visible without any user action. A v8 phone
// with no signal shows a black map with correct diamonds on it and NO word
// of explanation: every line map.html writes about what went wrong goes into
// #status, inside #panelbody, which is display:none while the panel is
// collapsed — and it auto-collapses at phone width. Twelve lines logged,
// four visible, and the four visible were exactly the four reporting nothing
// wrong. The no-signal warning, its explanation and a real "geochem markers
// failed" were all below the fold of a 64px scroller whose auto-scroll was
// itself disabled by the collapse that hid it — `S.scrollTop = S.scrollHeight`
// writes 0 to 0 with no layout box. Two defects each making the other
// permanent. Warn and err lines now surface in the bottom chrome bar, first
// line verbatim plus a count, one tap for the rest. `ok` lines are unchanged.
//
// v8 (2026-07-29): the three internal links navigate in the webview, and
// every page they reach carries a way back. A v7 phone taps the Gold map
// card and NOTHING happens — target="_blank" routes to Capacitor's popup
// delegate, which hands a capacitor:// URL to UIApplication.shared.open()
// and returns nil; iOS refuses the scheme. map.html is referenced exactly
// once in index.html, by that anchor, so the only field map screen is
// unreachable from the app UI. Adds fieldgold-chrome.css to SHELL: without
// it a cold-cache install has an unstyled back bar, which is the one
// control that must not fail. The nine https:// target="_blank" links are
// untouched and must stay that way — they work BECAUSE of the attribute.
//
// v7 (2026-07-29): safe-area insets. index.html, map.html, bench_hunter.html
// and creek_manual.html gain viewport-fit=cover; the four --sa-* variables read
// env() once so the CSS is testable; #panel, the Leaflet control containers,
// the launcher header and the two document pages carry the insets. A v6 phone
// paints the map's panel and Leaflet's zoom/layers controls UNDER the status
// bar: the collapse toggle measured [22,24,153,19] on an iPhone 14, spanning
// y=22..41 inside a 47px strip, and the panel auto-collapses at phone width, so
// the first sight of the map is a collapsed panel whose only control cannot be
// pressed. Confirmed by finger on two installs, one virgin. Note the ordering —
// viewport-fit=cover has to land first or every env() resolves to 0 and the
// padding is a no-op that looks correct in the diff.
//
// v6 (2026-07-28): map.html only — layers report from tile outcomes instead of
// from Leaflet's `load` event. A v5 phone shows a green ✓ for every tile layer
// that fetched NOTHING: measured on the device with the radios off as
// `basemap (Streets) ✓`, `claims ✓`, `ardf ✓`, `ngdbsed ✓` over zero loaded
// tiles, the basemap tick arriving three lines after its own "basemap tiles
// unavailable — no signal" warning, plus `terrain ✓` once toggled on. Leaflet's
// _tileReady gates `tileload` on !err but fires `load` whenever no tiles remain
// pending, including when every one failed. Rule 4 is "never soften a
// land-status warning" and a ✓ over a failed fetch is a softened warning — on
// the BLM claims layer, whose whole on-screen treatment exists to stop a blank
// being over-read as "no claims".
//
// v5 (2026-07-26): map.html only — the panel reachability fix.
//
// A phone still holding v4 has the DEFECT, and holds it permanently. The fetch
// handler below is cache-first with no revalidation: `caches.match` returns the
// stored copy and never asks the network. `./map.html` is in SHELL. So a v4
// device serves its own cached map.html forever, and publishing the fix to
// GitHub Pages changes NOTHING on the device that already installed. Bumping
// this line is not bookkeeping — it is the entire delivery mechanism.
//
// What a phone still holding v4 shows:
//
//   The land-status warnings in the map panel are partly unreadable and partly
//   unreachable. #panel was z-index:1000 and so are Leaflet's .leaflet-top /
//   .leaflet-bottom containers, so the tie broke by DOM order in Leaflet's
//   favour and the zoom and layers controls painted ON TOP of the warnings —
//   21 measured sample points at 390x664. Separately #panel had no max-height
//   and no scroller, and #map is a full-viewport absolute element so the body
//   never scrolls either: 102 of 256 warning sample points on a 390x664 phone
//   and 118 of 250 on a 375x553 one could not be brought on screen by any
//   gesture. Rules 4 and 5 say those notices are the point. A notice you
//   cannot reach has been removed, and close to half of them had been.
//
//   Both defects are desktop-clean — 0 of 256 unreachable at 1440x900 — which
//   is why they shipped. tests/test_panel_reachability.py is the tripwire.
//
// v4 (2026-07-26): one publication, seven changes. Everything below landed in
// a single release because the seven change sets it came from were developed
// against a repo state that never shipped, and were collapsed rather than
// stacked. An earlier draft of this file numbered each change set separately as
// v5 through v9 and described a v3 that contained land status. The v3 that
// actually reached a device contains none of it. That numbering is withdrawn so
// nobody goes looking for releases that were never published. READ THIS
// CAREFULLY IF YOU ARE DOING VERSION ARCHAEOLOGY: the v5 above is a real,
// published release and has nothing to do with the withdrawn v5. Versions are
// sequential from v4 onward and the withdrawn numbers are simply not reused.
//
// What a phone still holding v3 shows, change by change:
//
//   Land status is absent from the schema entirely. Every bench, site, GPX
//   waypoint and day plan is drawn and exported with nothing to say whether
//   the ground is open. This is the condition all seven changes exist to end.
//
//   The 20 REM candidates auto-seed with no land status at all and draw as
//   flat cyan diamonds. Twelve of the twenty sit on encumbered ground — one
//   inside MCO 549, six inside LLO 5, five inside pending ADL 229824 — and
//   the map says nothing. A v3 phone does not show these as unchecked; it
//   shows them as ordinary candidates, which reads as an invitation.
//
//   The photo screen has no land-status banner and sends no land status to the
//   model, so a photo taken on closed ground comes back assessed on its merits.
//
//   map.html colours logged sites by TERRAIN SCORE. A site scoring 72+ draws
//   in the same green the legend calls "DNR-checked, nothing found" — including
//   one sitting inside MCO 549. A green dot on closed ground, offline, with
//   nothing on screen to contradict it. Of everything here this is the failure
//   that most looks like a reassurance.
//
//   Leaflet is fetched from cdnjs at runtime and the two cdnjs URLs are in v3's
//   SHELL. That LOOKS like it works, because those entries were cached on a day
//   the phone had signal. It hides the fresh install and the cache eviction:
//   either one leaves a map page with no map library and no network to get one.
//   Leaflet is now vendored at vendor/leaflet/ and cached from disk.
//
//   map.html draws GREEN "PROVEN + OPEN" markers coloured by a query to BLM's
//   FEDERAL mining-claims service. This reach is STATE land, so that register
//   is nearly empty here — one polygon across the whole reach, against 143 in
//   a same-size box near Fairbanks — and its emptiness renders as a green
//   light. The map asks the wrong government and prints the answer as OPEN.
//
//   Nothing on a v3 screen names the STATE claim register. Removing the false
//   green is not the same as giving a true answer. The map now says it plainly:
//   22 active state claims sit in this reach, 0 pending, counted 2026-07-25
//   against DNR ME112 and ME13; none of them contains a bench; how near the
//   nearest one is was never measured; and the snapshot expires. Honest and
//   specific beats honest and silent at a trailhead.
//
// The five stage maps are NOT in SHELL, and that is a decision rather than an
// omission. They are archived build stages of map.html; every pixel they draw
// comes from the network (USGS WMS/WFS, OSM tiles, BLM export), so caching
// their HTML would produce a page that looks like FieldGold, carries no
// land-status layer, and shows nothing at all. A browser offline error is the
// more honest outcome. Each of them now says so on screen in red.
const CACHE = 'fieldgold-v9';

const SHELL = [
  './',
  './index.html',
  './map.html',
  './bench_hunter.html',
  './creek_manual.html',
  './load_rem_benches.html',
  './manifest.json',
  './fieldgold-data.js',
  './fieldgold-chrome.css',
  // Vendored Leaflet — see vendor/leaflet/PROVENANCE.md. The images are not
  // optional: leaflet.css references them by relative path, and without them
  // the default marker renders as a broken image. A marker you cannot see, on
  // ground you cannot dig.
  './vendor/leaflet/leaflet.css',
  './vendor/leaflet/leaflet.js',
  './vendor/leaflet/images/marker-icon.png',
  './vendor/leaflet/images/marker-icon-2x.png',
  './vendor/leaflet/images/marker-shadow.png',
  './vendor/leaflet/images/layers.png',
  './vendor/leaflet/images/layers-2x.png'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = e.request.url;

  const isLiveData =
    url.includes('mrdata.usgs.gov') ||
    url.includes('gis.blm.gov') ||
    url.includes('nationalmap.gov') ||
    url.includes('tile.openstreetmap.org') ||
    url.includes('api.anthropic.com');

  if (isLiveData) {
    e.respondWith(
      fetch(e.request).catch(() =>
        new Response('', { status: 503, statusText: 'offline' })
      )
    );
    return;
  }

  e.respondWith(
    caches.match(e.request).then(hit => {
      if (hit) return hit;
      return fetch(e.request)
        .then(resp => {
          if (resp && resp.status === 200 && e.request.method === 'GET') {
            const copy = resp.clone();
            caches.open(CACHE).then(c => c.put(e.request, copy));
          }
          return resp;
        })
        .catch(() => caches.match('./index.html'));
    })
  );
});
