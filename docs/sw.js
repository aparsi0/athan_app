/**
 * Service worker — caches the app shell for fast loads and offline use,
 * and caches audio files the first time they play.
 * Bump CACHE_VERSION when deploying changes to force clients to update.
 */
const CACHE_VERSION = 'athan-web-v24';
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
  'js/audio-players.js',
  'js/scheduler.js',
  'js/app.js',
  'manifest.webmanifest',
  'assets/icons/icon.svg'
];

self.addEventListener('install', (event) => {
  // Precache file-by-file rather than with cache.addAll(): addAll() is
  // all-or-nothing, so a single 404 (or one asset briefly unavailable on a
  // fresh deploy) would reject, abort the install and leave the site with no
  // service worker at all. allSettled() keeps whatever succeeded.
  // {cache: 'reload'} bypasses the browser's own HTTP cache — GitHub Pages
  // serves max-age=600, so without it a bump can precache the OLD files under
  // the NEW cache name, and activate() then deletes the only other copy.
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => Promise.allSettled(
      APP_SHELL.map((url) => cache.add(new Request(url, { cache: 'reload' }))
        .catch((e) => { console.warn('[sw] precache miss:', url, e.message); }))
    )).then(() => self.skipWaiting())
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

  // Assets (audio, theme terrains, skyline data): cache-first with runtime
  // fill — large, immutable files cached only once actually used, so
  // visitors don't pre-download all five theme photos.
  if (url.pathname.includes('/assets/')) {
    event.respondWith(
      caches.match(event.request, { ignoreSearch: true }).then(
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
      .catch(() => caches.match(event.request, { ignoreSearch: true })
        // A navigation that misses (e.g. the URL carried ?utm_source=…) must
        // still get the shell. Resolving undefined here would hand the user
        // the browser's offline error page while the shell sits in the cache.
        .then((hit) => hit || (event.request.mode === 'navigate'
          ? caches.match('index.html', { ignoreSearch: true })
          : undefined)))
  );
});
