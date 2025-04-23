// Verifica suporte a PWA
function checkPwaSupport() {
    const pwaSupport = {
        serviceWorker: 'serviceWorker' in navigator,
        pushManager: 'PushManager' in window,
        notifications: 'Notification' in window,
        installPrompt: 'onbeforeinstallprompt' in window,
        fetch: 'fetch' in window,
        cache: 'caches' in window
    };

    return pwaSupport;
}

// Registra o Service Worker
async function registerServiceWorker() {
    const pwaSupport = checkPwaSupport();
    
    if (!pwaSupport.serviceWorker) {
        console.warn('Service Worker não suportado neste navegador');
        return;
    }

    try {
        const registration = await navigator.serviceWorker.register('/static/js/service-worker.js');
        console.log('Service Worker registrado com sucesso:', registration);

        // Verifica atualizações
        registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                    // Nova versão disponível
                    showUpdateNotification();
                }
            });
        });

        // Verifica por atualizações periodicamente
        setInterval(() => {
            registration.update();
        }, 60 * 60 * 1000); // A cada hora

    } catch (error) {
        console.error('Falha ao registrar Service Worker:', error);
    }
}

// Mostra notificação de atualização
function showUpdateNotification() {
    if (!('Notification' in window)) return;

    if (Notification.permission === 'granted') {
        new Notification('Nova versão disponível', {
            body: 'Clique para atualizar o aplicativo',
            icon: '/static/icons/icon-192x192.png',
            tag: 'update-notification'
        });
    } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                showUpdateNotification();
            }
        });
    }
}

// Instalação do PWA
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    showInstallButton();
});

function showInstallButton() {
    const installButton = document.getElementById('install-button');
    if (installButton) {
        installButton.style.display = 'block';
        installButton.addEventListener('click', installPWA);
    }
}

async function installPWA() {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
        console.log('Usuário aceitou a instalação');
    } else {
        console.log('Usuário recusou a instalação');
    }
    
    deferredPrompt = null;
}

// Inicializa o PWA
document.addEventListener('DOMContentLoaded', () => {
    const pwaSupport = checkPwaSupport();
    
    // Registra Service Worker
    if (pwaSupport.serviceWorker) {
        registerServiceWorker();
    }

    // Configura atalhos
    if ('shortcuts' in navigator) {
        navigator.shortcuts.add([
            {
                name: 'Dashboard',
                url: '/dashboard',
                description: 'Acessar o painel principal'
            },
            {
                name: 'Estoque',
                url: '/items',
                description: 'Gerenciar itens do estoque'
            }
        ]);
    }
}); 