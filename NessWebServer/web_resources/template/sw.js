{% load static %}
const CACHE_NAME = 'ness-panel-v1';

// App shell — cached on install so the UI loads instantly even on a slow AP handoff
const PRECACHE = [
    '/',
    '{% static "ness/style.css" %}',
    '{% static "assets/favicons/android-chrome-192x192.png" %}',
    '{% static "assets/favicons/android-chrome-512x512.png" %}',
    '{% static "assets/favicons/apple-touch-icon.png" %}',
];

self.addEventListener('install', function (event) {
    event.waitUntil(
        caches.open(CACHE_NAME).then(function (cache) {
            return cache.addAll(PRECACHE);
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', function (event) {
    event.waitUntil(
        caches.keys().then(function (keys) {
            return Promise.all(
                keys.filter(function (k) { return k !== CACHE_NAME; })
                    .map(function (k) { return caches.delete(k); })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', function (event) {
    var url = new URL(event.request.url);

    // Never intercept API calls, WebSocket upgrades, or admin/auth pages
    if (url.pathname.startsWith('/api/') ||
        url.pathname.startsWith('/ws/') ||
        url.pathname.startsWith('/admin/') ||
        url.pathname.startsWith('/user/')) {
        return;
    }

    // CDN assets (Bootstrap, jQuery) — cache-first, they're versioned URLs
    if (url.origin !== self.location.origin) {
        event.respondWith(
            caches.match(event.request).then(function (cached) {
                if (cached) return cached;
                return fetch(event.request).then(function (response) {
                    if (response.ok) {
                        var clone = response.clone();
                        caches.open(CACHE_NAME).then(function (cache) {
                            cache.put(event.request, clone);
                        });
                    }
                    return response;
                });
            })
        );
        return;
    }

    // Local static assets — cache-first
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(event.request).then(function (cached) {
                if (cached) return cached;
                return fetch(event.request).then(function (response) {
                    if (response.ok) {
                        var clone = response.clone();
                        caches.open(CACHE_NAME).then(function (cache) {
                            cache.put(event.request, clone);
                        });
                    }
                    return response;
                });
            })
        );
        return;
    }

    // Page navigations — network-first so we always get the latest HTML,
    // fall back to cache if the server is unreachable (AP roaming, etc.)
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request).catch(function () {
                return caches.match('/');
            })
        );
        return;
    }
});
