// Verifica se o navegador suporta Service Worker
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/js/service-worker.js')
            .then(registration => {
                console.log('ServiceWorker registrado com sucesso:', registration.scope);
            })
            .catch(error => {
                console.log('Falha ao registrar ServiceWorker:', error);
            });
    });
}

// Monitoramento de conexão
let isOnline = navigator.onLine;
const onlineStatus = document.getElementById('online-status');

function updateOnlineStatus() {
    isOnline = navigator.onLine;
    if (onlineStatus) {
        onlineStatus.textContent = isOnline ? 'Online' : 'Offline';
        onlineStatus.className = isOnline ? 'badge bg-success' : 'badge bg-danger';
    }
    
    if (!isOnline) {
        // Redireciona para a página offline se não estiver nela
        if (window.location.pathname !== '/offline.html') {
            window.location.href = '/offline.html';
        }
    }
}

// Eventos de mudança de conexão
window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);

// Verifica status inicial
updateOnlineStatus();

// Função para verificar conexão periodicamente
setInterval(() => {
    if (!navigator.onLine && window.location.pathname !== '/offline.html') {
        window.location.href = '/offline.html';
    }
}, 5000);

// Função para tentar reconectar
function tryReconnect() {
    if (navigator.onLine) {
        window.location.reload();
    } else {
        setTimeout(tryReconnect, 5000);
    }
}

// Exporta funções para uso em outros arquivos
window.tryReconnect = tryReconnect; 