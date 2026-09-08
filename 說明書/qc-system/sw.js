const CACHE_NAME = 'qc-kanban-v2.1.4';
const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker v2.1.3] å¿«å??¸å??œæ?è³‡ç”¢');
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[Service Worker] æ¸…é™¤?Šç??¬å¿«??', key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  // å°æ–¼ API è«‹æ??–è·¨?Ÿè?æ±‚ï??¡ç”¨ Network Only (ä¸å¿«??
  if (event.request.url.includes('script.google.com') || event.request.method !== 'GET') {
    return;
  }

  // å°æ–¼ HTML ?é¢å°èˆªï¼Œå¼·?¶ä½¿??Network First (ç¶²è·¯?ªå?ï¼Œä?è­‰æ?æ¬¡é??°æ•´?†éƒ½?½è??¥æ??°ç?å¼ç¢¼)
  if (event.request.mode === 'navigate' || (event.request.headers.get('accept') && event.request.headers.get('accept').includes('text/html'))) {
    event.respondWith(
      fetch(event.request).then((response) => {
        if (response && response.status === 200) {
          const respClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, respClone));
        }
        return response;
      }).catch(() => {
        return caches.match('./index.html') || caches.match(event.request);
      })
    );
    return;
  }

  // å°æ–¼?–ç??å?ç¤ºç??œæ?è³‡æ?ï¼Œæ¡??Cache First with Network Fallback
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).then((response) => {
        if (response && response.status === 200) {
          const respClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, respClone));
        }
        return response;
      });
    })
  );
});
