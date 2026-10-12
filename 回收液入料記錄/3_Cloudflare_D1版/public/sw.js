const CACHE_NAME = 'recycle-gas-v11';
const urlsToCache = [
  './',
  './index.html',
  './manifest.json',
  './icon.jpg',
  './favicon.ico'
];

self.addEventListener('install', event => {
  self.skipWaiting(); // 強制立刻啟用新版
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(urlsToCache);
    })
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            return caches.delete(key); // 清除舊版本快取
          }
        })
      );
    }).then(() => self.clients.claim()).then(() => {
      // 主動通知所有開啟的畫面有更新
      return self.clients.matchAll().then(clients => {
        clients.forEach(client => client.postMessage({ type: 'VERSION_UPDATED' }));
      });
    })
  );
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  if (event.request.url.includes('script.google.com')) return;
  
  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).catch(() => {
        // 離線且網址是頁面導向時，回傳首頁快取
        if (event.request.mode === 'navigate') {
          return caches.match('./index.html') || caches.match('./');
        }
      });
    })
  );
});
