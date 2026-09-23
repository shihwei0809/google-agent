const CACHE_NAME = 'nitrogen-valve-training-v1';
const urlsToCache = [
  './',
  './index.html',
  './manifest.json',
  './quiz_data.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  // 不快取 /api/submit 請求
  if (event.request.url.includes('/api/submit') || event.request.method === 'POST') {
    return;
  }
  
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});
