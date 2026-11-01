// INGENIA: permite instalar la plataforma como app y abrirla sin conexión con lo último visto.
const CACHE = 'ingenia-v1';
const BASE = ['./', 'index.html', 'ver.html', 'fb.js', 'firebase-config.js', 'manifest.webmanifest', 'icono-192.png', 'icono-512.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(BASE)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(k => Promise.all(k.filter(x => x !== CACHE).map(x => caches.delete(x)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin || u.pathname.endsWith('admin.html')) return;
  // Primero la red (para tener siempre la llave y las clases del momento); si no hay internet, lo guardado
  e.respondWith(fetch(e.request).then(r => {
    if (r.ok) { const copia = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copia)); }
    return r;
  }).catch(() => caches.match(e.request, { ignoreSearch: u.pathname.endsWith('ver.html') })));
});
