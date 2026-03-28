const STATIC_CACHE = "secuexam-static-v1";
const APP_SHELL = [
  "/",
  "/manifest.webmanifest",
  "/secuexam_app/css/style.css",
  "/secuexam_app/js/app.js",
  "/secuexam_app/icons/icon-192.png",
  "/secuexam_app/icons/icon-512.png",
  "/secuexam_app/icons/apple-touch-icon.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== STATIC_CACHE)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);

  if (request.method !== "GET" || url.origin !== self.location.origin) {
    return;
  }

  if (url.pathname.startsWith("/api/")) {
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(() => caches.match("/") || caches.match("/manifest.webmanifest"))
    );
    return;
  }

  if (
    url.pathname.startsWith("/secuexam_app/") ||
    url.pathname === "/manifest.webmanifest" ||
    url.pathname === "/service-worker.js"
  ) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          const copy = response.clone();
          caches.open(STATIC_CACHE).then((cache) => cache.put(request, copy));
          return response;
        });
      })
    );
  }
});
