const CACHE_NAME = 'sales-planner-pwa-v1.0.1';
const CORE_ASSETS = [
  '/',
  '/index.html',
  '/styles.css',
  '/seed_data.js',
  '/calc_engine.js',
  '/excel_parser.js',
  '/excel_exporter.js',
  '/pwa_offline_sync.js',
  '/app.js',
  '/manifest.json',
  '/favicon.png',
  '/vendor/xlsx.full.min.js',
  '/vendor/exceljs.min.js',
  '/icons/icon-192.png',
  '/icons/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.map((k) => (k !== CACHE_NAME ? caches.delete(k) : Promise.resolve()))
      )
    ).then(async () => {
      await self.clients.claim();
      const clientsList = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
      for (const client of clientsList) {
        client.postMessage({ type: 'VERSION_UPDATED', version: CACHE_NAME });
      }
    })
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  // API always goes directly to network (handled by OfflineSyncManager on failure)
  if (url.pathname.startsWith('/api/')) {
    return;
  }

  // Network-First with cache fallback so updates arrive promptly while remaining offline-resilient
  event.respondWith(
    fetch(req)
      .then((res) => {
        if (res && res.status === 200 && res.type === 'basic') {
          const clone = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, clone));
        }
        return res;
      })
      .catch(() => caches.match(req).then((cached) => cached || caches.match('/index.html')))
  );
});
