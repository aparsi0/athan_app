/**
 * Service worker — caches the app shell for fast loads and offline use,
 * and caches audio files the first time they play.
 * Bump CACHE_VERSION when deploying changes to force clients to update.
 */
const CACHE_VERSION = 'athan-web-v7';
const APP_SHELL = [
  '.',
  'index.html',
  'css/style.css',
  'js/config.js',
  'js/location.js',
  'js/prayer-times.js',
  'js/audio.js',
  'js/scene.js',
  'js/podcast.js',
  'js/scheduler.js',
  'js/app.js',
  'manifest.webmanifest',
  'assets/icons/icon.svg',
  'assets/ridge.json',
  'assets/terrain.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Never cache API calls — prayer times and location must stay fresh.
  if (url.origin !== self.location.origin) return;

  // Audio: cache-first with runtime fill (files are large and immutable).
  if (url.pathname.includes('/assets/audio/')) {
    event.respondWith(
      caches.match(event.request).then(
        (hit) => hit || fetch(event.request).then((res) => {
          if (res.ok && res.status !== 206) {
            const copy = res.clone();
            caches.open(CACHE_VERSION).then((cache) => cache.put(event.request, copy));
          }
          return res;
        })
      )
    );
    return;
  }

  // App shell: network-first so deployed updates show up immediately,
  // falling back to cache when offline.
  event.respondWith(
    fetch(event.request)
      .then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE_VERSION).then((cache) => cache.put(event.request, copy));
        }
        return res;
      })
      .catch(() => caches.match(event.request))
  );
});
