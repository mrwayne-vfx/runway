const CACHE = "runway-v23";
const ASSETS = ["./", "./index.html", "./sw.js", "./follow.html"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE && k !== "runway-tiles").map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (url.origin === location.origin) {
    // the app pages: network first so a refresh always shows the newest build, cache when there is no signal
    e.respondWith(fetch(e.request).then(res => { const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return res; }).catch(() => caches.match(e.request)));
  } else if (url.hostname.endsWith("arcgisonline.com")) {
    // map tiles: saved tiles first, else network (and keep what we fetch)
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).then(res => { const copy = res.clone(); caches.open("runway-tiles").then(c => c.put(e.request, copy)); return res; })));
  } else {
    // fonts: network first, fall back to cache, fail quietly
    e.respondWith(fetch(e.request).then(res => { const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return res; }).catch(() => caches.match(e.request)));
  }
});
