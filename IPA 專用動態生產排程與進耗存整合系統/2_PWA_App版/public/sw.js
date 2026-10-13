const CACHE_NAME = 'ipa-pwa-v3.6';
const urlsToCache = [
  './',
  './index.html',
  './manifest.json',
  './xlsx.full.min.js',
  './icons/icon-192.png',
  './icons/icon-512.png',
  'https://unpkg.com/react@18/umd/react.production.min.js',
  'https://unpkg.com/react-dom@18/umd/react-dom.production.min.js',
  'https://unpkg.com/@babel/standalone/babel.min.js',
  'https://cdn.tailwindcss.com'
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
      // 主動通知所有開啟的頁面有新版本
      return self.clients.matchAll().then(clients => {
        clients.forEach(client => client.postMessage({ type: 'VERSION_UPDATED' }));
      });
    })
  );
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  if (event.request.url.includes('/api/')) return; // API 請求絕不走快取
  
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
