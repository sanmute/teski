const CACHE_VERSION = "teski-static-v3"; // bump to force update
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
  // Always pass through non-GET requests
  if (event.request.method !== "GET") return;

  const url = new URL(event.request.url);
  const hasAuthHeader = event.request.headers.has("authorization");

  // Passthrough for cross-origin, API-like paths, fly.dev, or any request with Authorization
  const isApiLike =
    url.origin !== self.location.origin ||
    url.hostname.includes("fly.dev") ||
    url.pathname.startsWith("/api/") ||
    url.pathname.startsWith("/onboarding/") ||
    url.pathname.startsWith("/analytics/") ||
    url.pathname.startsWith("/ex") ||
    url.pathname.startsWith("/tasks") ||
    url.pathname.startsWith("/integrations/") ||
    url.pathname.startsWith("/memory") ||
    url.pathname.startsWith("/study") ||
    url.pathname.startsWith("/push") ||
    url.pathname.includes("/onboarding/") ||
    url.pathname.includes("/analytics/") ||
    url.pathname.includes("/auth") ||
    url.pathname.includes("/persona") ||
    url.pathname.includes("/feedback") ||
    url.pathname.includes("/exercises") ||
    url.pathname.includes("/estimates") ||
    url.pathname.includes("/reminders") ||
    url.pathname.includes("/leaderboards") ||
    url.pathname.includes("/memory");

  if (isApiLike || hasAuthHeader) {
    if (DEBUG_SW) {
      console.debug("[SW] passthrough", event.request.method, event.request.url, { hasAuthHeader });
    }
    event.respondWith(fetch(event.request));
    return;
  }

  // Static asset caching for same-origin GET requests only
  if (url.origin !== self.location.origin) return;

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

// Simple toggle for dev logging in SW (set via replace at build if needed)
const DEBUG_SW = false;

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
