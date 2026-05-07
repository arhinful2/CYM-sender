// Service Worker for Church Youth Management System
// Handles caching, offline support, and app installation

const CACHE_NAME = 'youth-church-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/portal/',
  '/accounts/login/',
  '/static/css/custom.css',
  '/static/js/custom.js',
  '/offline.html'  // Fallback page for offline
];

// Install event - cache essential assets
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('Service Worker: Caching essential assets');
      // Try to cache files, but don't fail if some don't exist
      return Promise.allSettled(
        ASSETS_TO_CACHE.map(url =>
          cache.add(url).catch(err =>
            console.log(`Could not cache ${url}:`, err)
          )
        )
      );
    })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Service Worker: Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip external URLs
  if (!request.url.startsWith(self.location.origin)) {
    return;
  }

  // Handle API calls with network-first strategy
  if (request.url.includes('/ajax/') || request.url.includes('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone the response
          const clonedResponse = response.clone();

          // Cache successful responses
          if (response.status === 200) {
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, clonedResponse);
            });
          }

          return response;
        })
        .catch(() => {
          // Try to return cached version
          return caches.match(request).then((response) => {
            return response || new Response(
              'Network request failed and no cache available',
              { status: 503, statusText: 'Service Unavailable' }
            );
          });
        })
    );
    return;
  }

  // Handle static assets with cache-first strategy
  event.respondWith(
    caches.match(request).then((response) => {
      if (response) {
        return response;
      }

      return fetch(request)
        .then((response) => {
          // Don't cache if not a successful response
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // Clone the response
          const clonedResponse = response.clone();

          // Cache the response
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, clonedResponse);
          });

          return response;
        })
        .catch(() => {
          // Return offline page if available
          return caches.match('/offline.html').then((response) => {
            return response || new Response(
              'Network unavailable',
              { status: 503, statusText: 'Service Unavailable' }
            );
          });
        });
    })
  );
});

// Background sync for offline messages (future enhancement)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-messages') {
    event.waitUntil(
      // Sync pending messages when connection is restored
      self.clients.matchAll().then((clients) => {
        clients.forEach((client) => {
          client.postMessage({
            type: 'SYNC_MESSAGES',
            message: 'Syncing messages from offline queue'
          });
        });
      })
    );
  }
});

// Handle messages from clients
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CLIENTS_CLAIM') {
    self.clients.claim();
  }
});

// Log service worker status
console.log('Service Worker: Script loaded');
