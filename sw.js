const CACHE = 'fieldgold-v3';

const SHELL = [
  './',
  './index.html',
  './map.html',
  './bench_hunter.html',
  './creek_manual.html',
  './manifest.json',
  './fieldgold-data.js',
  'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js'
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
