const CACHE_NAME = 'chemflow-pro-v2-' + new Date().getTime(); // 動態快取名稱強制更新
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json'
];

self.addEventListener('install', event => {
  // 強制立刻安裝新的 Service Worker，不要等待舊的關閉
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('activate', event => {
  // 啟動新的 Service Worker 時，刪除所有舊的快取
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    // 網路優先策略 (Network First)
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});