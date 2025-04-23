const CACHE_NAME = 'estoque3d-v1';
const OFFLINE_URL = '/offline.html';

// Recursos para cache
const RESOURCES_TO_CACHE = [
    '/',
    '/offline.html',
    '/static/css/bootstrap.min.css',
    '/static/css/style.css',
    '/static/js/bootstrap.bundle.min.js',
    '/static/js/main.js',
    '/static/js/chart.js',
    '/static/js/websocket.js',
    '/static/favicon.ico',
    '/static/manifest.json',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png'
];

// Verifica se o navegador suporta Service Workers
if ('serviceWorker' in navigator) {
    // Instalação do Service Worker
    self.addEventListener('install', (event) => {
        event.waitUntil(
            caches.open(CACHE_NAME)
                .then((cache) => {
                    console.log('Cache aberto');
                    return cache.addAll(RESOURCES_TO_CACHE);
                })
                .then(() => {
                    console.log('Recursos em cache');
                    return self.skipWaiting();
                })
        );
    });

    // Ativação do Service Worker
    self.addEventListener('activate', (event) => {
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME) {
                            return caches.delete(cacheName);
                        }
                    })
                );
            }).then(() => {
                return self.clients.claim();
            })
        );
    });

    // Estratégia de cache: Network First, depois Cache
    self.addEventListener('fetch', (event) => {
        // Ignora requisições não-GET
        if (event.request.method !== 'GET') return;

        // Ignora requisições de chrome-extension
        if (event.request.url.startsWith('chrome-extension://')) return;

        event.respondWith(
            fetch(event.request)
                .then((response) => {
                    // Clona a resposta para poder usar no cache
                    const responseToCache = response.clone();

                    // Atualiza o cache
                    caches.open(CACHE_NAME)
                        .then((cache) => {
                            cache.put(event.request, responseToCache);
                        });

                    return response;
                })
                .catch(() => {
                    // Se offline, tenta buscar do cache
                    return caches.match(event.request)
                        .then((response) => {
                            // Se encontrou no cache, retorna
                            if (response) {
                                return response;
                            }

                            // Se não encontrou e é uma navegação, retorna página offline
                            if (event.request.mode === 'navigate') {
                                return caches.match(OFFLINE_URL);
                            }
                            return new Response('Offline', {
                                status: 503,
                                statusText: 'Service Unavailable',
                                headers: new Headers({
                                    'Content-Type': 'text/plain'
                                })
                            });
                        });
                })
        );
    });

    // Push Notifications
    self.addEventListener('push', (event) => {
        const options = {
            body: event.data.text(),
            icon: '/static/icons/icon-192x192.png',
            badge: '/static/icons/icon-192x192.png',
            vibrate: [100, 50, 100],
            data: {
                dateOfArrival: Date.now(),
                primaryKey: 1
            }
        };

        event.waitUntil(
            self.registration.showNotification('Estoque3D', options)
        );
    });

    // Background Sync
    self.addEventListener('sync', (event) => {
        if (event.tag === 'sync-data') {
            event.waitUntil(
                syncData()
                    .then(() => {
                        return self.registration.showNotification('Sincronização concluída', {
                            body: 'Os dados foram sincronizados com sucesso!',
                            icon: '/static/icons/icon-192x192.png'
                        });
                    })
                    .catch((error) => {
                        console.error('Erro na sincronização:', error);
                    })
            );
        }
    });

    async function syncData() {
        // Implementar lógica de sincronização aqui
        // Por exemplo, sincronizar dados offline com o servidor
        return Promise.resolve();
    }

    // Notificações push (apenas para navegadores que suportam)
    if ('PushManager' in window) {
        self.addEventListener('push', event => {
            const options = {
                body: event.data.text(),
                icon: '/static/icons/icon-192x192.png',
                badge: '/static/icons/icon-72x72.png',
                vibrate: [100, 50, 100],
                data: {
                    dateOfArrival: Date.now(),
                    primaryKey: 1
                }
            };

            // Adiciona ações apenas se suportado
            if ('actions' in Notification.prototype) {
                options.actions = [
                    {
                        action: 'explore',
                        title: 'Verificar',
                        icon: '/static/icons/check.png'
                    },
                    {
                        action: 'close',
                        title: 'Fechar',
                        icon: '/static/icons/close.png'
                    }
                ];
            }

            event.waitUntil(
                self.registration.showNotification('Estoque3D', options)
            );
        });

        // Ação ao clicar na notificação
        self.addEventListener('notificationclick', event => {
            event.notification.close();

            if (event.action === 'explore') {
                event.waitUntil(
                    clients.openWindow('/dashboard')
                );
            }
        });
    }
} 