// Dashboard charts and functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts if the elements exist
    initCharts();
    
    // Set up date pickers for forms that need them
    initDatePickers();
});

function initCharts() {
    // Stock distribution chart
    const stockChartElement = document.getElementById('stockDistributionChart');
    if (stockChartElement) {
        const ctx = stockChartElement.getContext('2d');
        const chartData = JSON.parse(stockChartElement.dataset.chart);
        
        new Chart(ctx, {
            type: 'doughnut',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                    },
                    title: {
                        display: true,
                        text: 'Distribuição de Itens por Sub-estoque'
                    }
                }
            }
        });
    }
    
    // Recent movements chart if it exists
    const movementsChartElement = document.getElementById('recentMovementsChart');
    if (movementsChartElement && typeof movementsData !== 'undefined') {
        const ctx = movementsChartElement.getContext('2d');
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: movementsData.labels,
                datasets: [{
                    label: 'Movimentações Recentes',
                    data: movementsData.values,
                    backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
                        '#FF9F40', '#8C9EFF', '#AED581', '#FFD54F', '#4DD0E1'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

function initDatePickers() {
    // Initialize date pickers for forms that have date inputs
    const dateInputs = document.querySelectorAll('input[type="date"]');
    
    dateInputs.forEach(input => {
        // You can add date picker initialization code here if needed
        // For this implementation, we'll use the native date input
    });
}

// Item type selector for filtering
const itemTypeSelector = document.getElementById('item_type');
if (itemTypeSelector) {
    itemTypeSelector.addEventListener('change', function() {
        const form = this.closest('form');
        if (form) {
            form.submit();
        }
    });
}

// Status filter for projects and purchase orders
const statusFilter = document.getElementById('status-filter');
if (statusFilter) {
    statusFilter.addEventListener('change', function() {
        window.location.href = this.value;
    });
}

// Movement type filter
const movementTypeFilter = document.getElementById('movement-type-filter');
if (movementTypeFilter) {
    movementTypeFilter.addEventListener('change', function() {
        window.location.href = this.value;
    });
}

// Function to handle low stock alerts toast
function showLowStockAlerts(items) {
    if (items && items.length > 0) {
        const toastContainer = document.getElementById('toast-container');
        if (toastContainer) {
            const toast = document.createElement('div');
            toast.className = 'toast show';
            toast.setAttribute('role', 'alert');
            toast.setAttribute('aria-live', 'assertive');
            toast.setAttribute('aria-atomic', 'true');
            
            toast.innerHTML = `
                <div class="toast-header">
                    <strong class="me-auto">Alerta de Estoque Baixo</strong>
                    <small>${items.length} itens</small>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    Existem ${items.length} itens com estoque abaixo do mínimo.
                    <a href="/reports/low_stock" class="btn btn-sm btn-warning mt-2">Ver Relatório</a>
                </div>
            `;
            
            toastContainer.appendChild(toast);
            
            // Initialize the Bootstrap toast
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
        }
    }
}
