const CACHE = 'astrofin-v1';
const SHELL = ['/', '/index.html'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((r) => {
      return r || fetch(e.request).catch(() => {
        if (e.request.mode === 'navigate') return caches.match('/');
        return new Response('Offline', { status: 503 });
      });
    }),
  );
});
