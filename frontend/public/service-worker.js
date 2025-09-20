const CACHE_VERSION = "teski-static-v1";
const PRECACHE_URLS = [
  "/",
  "/index.html",
  "/favicon.svg",
  "/manifest.webmanifest",
];

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(PRECACHE_URLS))
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) =>
        Promise.all(
          cacheNames
            .filter((name) => name !== CACHE_VERSION)
            .map((name) => caches.delete(name))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }

  const requestURL = new URL(event.request.url);
  if (requestURL.origin !== self.location.origin) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        event.waitUntil(updateCache(event.request));
        return cachedResponse;
      }

      return fetch(event.request)
        .then((networkResponse) => {
          if (!isCacheableResponse(networkResponse)) {
            return networkResponse;
          }

          const responseClone = networkResponse.clone();
          caches.open(CACHE_VERSION).then((cache) => {
            cache.put(event.request, responseClone);
          });

          return networkResponse;
        })
        .catch(() => caches.match("/index.html"));
    })
  );
});

function updateCache(request) {
  return fetch(request)
    .then((networkResponse) => {
      if (!isCacheableResponse(networkResponse)) {
        return;
      }

      return caches.open(CACHE_VERSION).then((cache) => {
        return cache.put(request, networkResponse.clone());
      });
    })
    .catch(() => undefined);
}

function isCacheableResponse(response) {
  return (
    response &&
    response.status === 200 &&
    (response.type === "basic" || response.type === "default")
  );
}
