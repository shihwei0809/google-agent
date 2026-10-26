const CACHE_NAME = 'recycle-d1-v16-auto-bidirectional-sync';
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
  if (event.request.url.includes('script.google.com') || event.request.url.includes('/api/')) return;
  
  // 網路優先策略 (Network First)：連線時抓取雲端最新檔案並背景更新快取，斷網時無縫切換本機快取
  event.respondWith(
    fetch(event.request).then(response => {
      if (response && response.status === 200 && event.request.url.startsWith('http')) {
        const responseClone = response.clone();
        caches.open(CACHE_NAME).then(cache => {
          cache.put(event.request, responseClone);
        });
      }
      return response;
    }).catch(() => {
      return caches.match(event.request).then(cachedResponse => {
        if (cachedResponse) return cachedResponse;
        if (event.request.mode === 'navigate') {
          return caches.match('./index.html') || caches.match('./');
        }
      });
    })
  );
});
