// Reports functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts in reports
    initReportCharts();
    
    // Initialize date range pickers
    initDateRangePickers();
    
    // Initialize PDF generation
    setupPDFGeneration();
});

function initReportCharts() {
    // Load chart data via AJAX if the chart containers exist
    loadChartData('inventory-value-chart', '/api/chart/inventory_value');
    loadChartData('movements-by-type-chart', '/api/chart/movements_by_type');
    loadChartData('projects-by-status-chart', '/api/chart/projects_by_status');
}

function loadChartData(elementId, apiUrl) {
    const chartElement = document.getElementById(elementId);
    if (chartElement) {
        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                createChart(chartElement, data);
            })
            .catch(error => {
                console.error('Error loading chart data:', error);
                chartElement.innerHTML = '<div class="alert alert-danger">Erro ao carregar dados do gráfico</div>';
            });
    }
}

function createChart(element, data) {
    const ctx = element.getContext('2d');
    const chartType = element.dataset.chartType || 'doughnut';
    
    new Chart(ctx, {
        type: chartType,
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                },
                title: {
                    display: true,
                    text: element.dataset.title || ''
                }
            }
        }
    });
}

function initDateRangePickers() {
    // Set up date pickers for report filters
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    
    if (startDateInput && endDateInput) {
        // You can add date picker initialization code here if needed
        // For this implementation, we'll use the native date inputs
    }
    
    // Auto-submit form when date range changes
    const dateFilterForm = document.getElementById('date-filter-form');
    if (dateFilterForm) {
        const formInputs = dateFilterForm.querySelectorAll('input, select');
        formInputs.forEach(input => {
            input.addEventListener('change', function() {
                dateFilterForm.submit();
            });
        });
    }
}

function setupPDFGeneration() {
    const generatePdfButtons = document.querySelectorAll('.generate-pdf');
    
    generatePdfButtons.forEach(button => {
        button.addEventListener('click', function() {
            const reportType = this.dataset.reportType;
            const reportTitle = this.dataset.title || 'Relatório';
            
            // Get the report table
            const reportTable = document.querySelector(`.report-table-${reportType}`);
            if (!reportTable) return;
            
            // Create PDF using jsPDF
            const doc = new jspdf.jsPDF();
            
            // Add report title
            doc.setFontSize(16);
            doc.text(reportTitle, 14, 15);
            
            // Add date
            doc.setFontSize(10);
            doc.text(`Gerado em: ${new Date().toLocaleDateString('pt-BR')}`, 14, 22);
            
            // Add logo if available
            // (Assuming there's a hidden img element with id "company-logo")
            const logoImg = document.getElementById('company-logo');
            if (logoImg) {
                const imgData = logoImg.src;
                doc.addImage(imgData, 'PNG', 170, 10, 25, 15);
            }
            
            // Convert table to PDF
            const tableY = 30;
            doc.autoTable({ 
                html: reportTable,
                startY: tableY,
                theme: 'grid',
                headStyles: { fillColor: [52, 58, 64] },
                margin: { top: tableY }
            });
            
            // Save the PDF
            doc.save(`${reportType}_report.pdf`);
        });
    });
}

// Export to CSV
document.querySelectorAll('.export-csv').forEach(button => {
    button.addEventListener('click', function() {
        const url = this.dataset.url;
        if (url) {
            window.location.href = url;
        }
    });
});

// Filter toggle
document.querySelectorAll('.toggle-filters').forEach(button => {
    button.addEventListener('click', function() {
        const filterContainer = document.querySelector('.filter-container');
        if (filterContainer) {
            filterContainer.classList.toggle('d-none');
        }
    });
});
