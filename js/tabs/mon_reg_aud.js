// js/tabs/mon_reg_aud.js

window.registerTabInitializer('monRegAud', function() {
    console.log("Initializing monRegAud tab...");
    setupMonRegAudEventListeners();
});

let statusChart; // Declare a global variable for the chart instance

function setupMonRegAudEventListeners() {
    const monRegAudArea = document.getElementById('monRegAudArea');
    const monRegAudBranch = document.getElementById('monRegAudBranch');
    const generateButton = document.getElementById('generateMonRegAudReport');
    const tableBody = document.getElementById('monRegAudTableBody');
    const summaryContainer = document.getElementById('monRegAudSummary');
    const complianceRateElement = document.getElementById('complianceRate');

    // A helper function to reset the report display
    const resetReportDisplay = (message, showSummary = false) => {
        // Clear the table body first
        while (tableBody.firstChild) {
            tableBody.removeChild(tableBody.firstChild);
        }
        // Add the new placeholder row
        const newRow = document.createElement('tr');
        newRow.innerHTML = `<td colspan="7" class="text-gray-500 text-center p-4">${message}</td>`;
        tableBody.appendChild(newRow);

        // Reset summary data but keep the section visible
        if (complianceRateElement) {
            complianceRateElement.textContent = '0.00%';
        }
        if (statusChart) {
            statusChart.destroy();
            statusChart = null; // Clear the chart instance
        }
        if (summaryContainer) {
            if (showSummary) {
                summaryContainer.classList.remove('hidden');
            } else {
                summaryContainer.classList.add('hidden');
            }
        }
    };

    // Event listener for Area change
    monRegAudArea.addEventListener('change', () => {
        const area = monRegAudArea.value;
        const branchSelect = monRegAudBranch;
        
        // Reset the report display and table
        resetReportDisplay("Select an area and branch, then click 'Generate Report'", false); // Explicitly hide summary on area change

        branchSelect.innerHTML = '<option value="">Select Branch</option>';
        if (area) {
            branchSelect.disabled = false;
            if (area === 'Consolidated') {
                branchSelect.disabled = true;
                generateButton.disabled = false;
            } else {
                fetchBranchesForArea(area, monRegAudBranch);
                generateButton.disabled = true;
            }
        } else {
            branchSelect.disabled = true;
            generateButton.disabled = true;
        }
    });

    // Event listener for Branch change
    monRegAudBranch.addEventListener('change', () => {
        const branch = monRegAudBranch.value;
        generateButton.disabled = !branch;
        
        // Reset the report display and table
        if (branch) {
            resetReportDisplay("Click 'Generate Report' to view data for this branch.", false); // Explicitly hide summary on branch change
        } else {
            resetReportDisplay("Please select a branch.", false); // Explicitly hide summary
        }
    });

    // Event listener for the Generate Report button
    generateButton.addEventListener('click', async (event) => {
        const area = monRegAudArea.value;
        const branch = monRegAudBranch.value;
        if (!area) {
            window.showMessage("Please select an Area.", 'error');
            return;
        }
        if (area !== 'Consolidated' && !branch) {
            window.showMessage("Please select a Branch.", 'error');
            return;
        }

        const button = event.currentTarget;
        const originalButtonText = button.innerHTML;
        
        const restoreButtonState = () => {
            button.disabled = false;
            button.innerHTML = originalButtonText;
        };

        button.disabled = true;
        button.innerHTML = '<i class="fa-solid fa-spinner fa-spin-pulse"></i> Loading...';
        
        // Clear the table body and add a loading row, but keep the summary visible
        resetReportDisplay("Loading report...", true); // Pass true to show the summary section while loading
        
        try {
            const response = await fetch(`${window.FLASK_API_BASE_URL}/monitoring/regular_audit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ area: area, branch: branch })
            });

            const result = await response.json();
            
            console.log("Received data from backend:", result);

            if (response.ok) {
                window.showMessage(result.message, 'success');
                populateTableData(result.data);
                populateSummaryData(result.summary);
            } else {
                window.showMessage(result.message, 'error');
                populateTableData(result.data || []);
                populateSummaryData({});
            }
        } catch (error) {
            console.error('Error fetching regular audit report:', error);
            window.showMessage('An error occurred while fetching the report.', 'error');
            populateTableData([]);
            populateSummaryData({});
        } finally {
            restoreButtonState();
        }
    });
}

function fetchBranchesForArea(area, selectElement) {
    const parentContainer = selectElement.closest('.input-group');
    if (parentContainer) {
        parentContainer.classList.add('loading');
    }
    
    fetch(`${window.FLASK_API_BASE_URL}/get_branches?area=${area}`)
        .then(response => response.json())
        .then(data => {
            if (data.branches) {
                selectElement.innerHTML = '<option value="">Select Branch</option>';
                data.branches.forEach(branch => {
                    const option = document.createElement('option');
                    option.value = branch;
                    option.textContent = branch;
                    selectElement.appendChild(option);
                });
            }
            if (parentContainer) {
                parentContainer.classList.remove('loading');
            }
        })
        .catch(error => {
            console.error('Error fetching branches:', error);
            window.showMessage('Failed to load branches.', 'error');
            if (parentContainer) {
                parentContainer.classList.remove('loading');
            }
        });
}

function populateTableData(data) {
    const tableBody = document.getElementById('monRegAudTableBody');
    if (!tableBody) return;

    console.log("Populating table with data:", data);

    // Clear the existing content of the table body
    while (tableBody.firstChild) {
        tableBody.removeChild(tableBody.firstChild);
    }

    if (!Array.isArray(data) || data.length === 0) {
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = `<td colspan="7" class="text-gray-500 text-center p-4">No data found for the selected criteria.</td>`;
        tableBody.appendChild(emptyRow);
        return;
    }

    try {
        data.forEach(row => {
            if (typeof row === 'object' && row !== null) {
                const newRow = document.createElement('tr');
                newRow.innerHTML = `
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${row.Year_Audited || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${row.Area_Audited || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${row.Finding_ID || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${row.Risk_No || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${row.Risk_Event || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${row.Status || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${row.Risk_Level || ''}</td>
                `;
                tableBody.appendChild(newRow);
            }
        });
    } catch (e) {
        console.error("Error populating table data:", e);
        const errorRow = document.createElement('tr');
        errorRow.innerHTML = `<td colspan="7" class="text-red-500 text-center p-4">An error occurred while rendering the report: ${e.message}</td>`;
        tableBody.appendChild(errorRow);
    }
}

function populateSummaryData(summary) {
    const summaryContainer = document.getElementById('monRegAudSummary');
    const complianceRateElement = document.getElementById('complianceRate');
    const chartContext = document.getElementById('statusChart');

    if (!summary || Object.keys(summary).length === 0) {
        if (summaryContainer) {
            summaryContainer.classList.add('hidden');
        }
        return;
    }

    console.log("Populating summary with data:", summary);

    complianceRateElement.textContent = summary.compliance_rate || '0.00%';

    if (statusChart) {
        statusChart.destroy();
    }
    
    if (chartContext) {
        statusChart = new Chart(chartContext, {
            type: 'line',
            data: {
                labels: ['Open', 'In Progress', 'Closed'],
                datasets: [{
                    label: 'Number of Audits',
                    data: [summary.status_counts.Open, summary.status_counts['In Progress'], summary.status_counts.Closed],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.2)',
                        'rgba(255, 206, 86, 0.2)',
                        'rgba(75, 192, 192, 0.2)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)'
                    ],
                    borderWidth: 1,
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    if (summaryContainer) {
        summaryContainer.classList.remove('hidden');
    }
}
