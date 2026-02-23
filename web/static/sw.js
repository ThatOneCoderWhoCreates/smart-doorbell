// Basic Service Worker to allow PWA Installation
const CACHE_NAME = 'doorbell-pwa-v1';

self.addEventListener('install', (event) => {
    console.log('[Service Worker] Install');
});

self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activate');
});

self.addEventListener('fetch', (event) => {
    // Required by Chrome for PWA installability.
    // We simply pass through the request.
});

self.addEventListener('push', (event) => {
    console.log('[Service Worker] Push Received.');
    const dataText = event.data ? event.data.text() : 'Activity Detected!';

    let title = 'Smart Doorbell Alert';
    let urgencyIcon = '/static/favicon.ico';

    const options = {
        body: dataText,
        icon: urgencyIcon,
        badge: urgencyIcon,
        vibrate: [200, 100, 200, 100, 200],
        requireInteraction: true,
        actions: [
            { action: 'view_camera', title: '👀 View Camera' },
            { action: 'call_security', title: '🚨 Call Security' }
        ]
    };

    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
    console.log('[Service Worker] Notification click Received.');
    event.notification.close();

    if (event.action === 'call_security') {
        // Open phone dialer
        event.waitUntil(clients.openWindow('tel:911'));
    } else {
        // 'view_camera' or normal tap just opens the PWA
        event.waitUntil(
            clients.matchAll({ type: 'window' }).then((windowClients) => {
                // If app is already open, focus it
                for (let i = 0; i < windowClients.length; i++) {
                    const client = windowClients[i];
                    if (client.url.indexOf('/') !== -1 && 'focus' in client) {
                        return client.focus();
                    }
                }
                // If app is closed, open it
                if (clients.openWindow) {
                    return clients.openWindow('/');
                }
            })
        );
    }
});
