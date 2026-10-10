const CACHE_NAME = 'recycle-gas-v4';
const urlsToCache = [
  './',
  './index.html',
  './manifest.json',
  './icon.jpg',
  './favicon.ico'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  // 只快取 GET 請求，並排除 API 與外部服務
  if (event.request.method !== 'GET') return;
  if (event.request.url.includes('script.google.com')) return;
  
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
