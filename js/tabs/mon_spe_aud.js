// js/tabs/mon_spe_aud.js

window.registerTabInitializer('monSpeAud', function() {
    console.log("Initializing monSpeAud tab...");
    setupMonSpeAudEventListeners();
});

function setupMonSpeAudEventListeners() {
    const monSpeAudArea = document.getElementById('monSpeAudArea');
    const monSpeAudBranch = document.getElementById('monSpeAudBranch');
    const generateButton = document.getElementById('generateMonSpeAudReport');

    monSpeAudArea.addEventListener('change', () => {
        const area = monSpeAudArea.value;
        const branchSelect = monSpeAudBranch;

        branchSelect.innerHTML = '<option value="">Select Branch</option>';
        if (area) {
            branchSelect.disabled = false;
            if (area === 'Consolidated') {
                branchSelect.disabled = true;
                generateButton.disabled = false;
            } else {
                fetchBranchesForArea(area, monSpeAudBranch);
            }
        } else {
            branchSelect.disabled = true;
            generateButton.disabled = true;
        }
    });

    monSpeAudBranch.addEventListener('change', () => {
        const branch = monSpeAudBranch.value;
        generateButton.disabled = !branch;
    });

    generateButton.addEventListener('click', async () => {
        const area = monSpeAudArea.value;
        const branch = monSpeAudArea.value === 'Consolidated' ? '' : monSpeAudBranch.value;

        if (!area) {
            window.showMessage("Please select an Area.", 'error');
            return;
        }

        const button = event.currentTarget;
        const originalButtonText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = 'Loading...';

        try {
            const response = await fetch(`${window.FLASK_API_BASE_URL || 'http://127.0.0.1:5000'}/monitoring/special_audit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ area: area, branch: branch })
            });

            const result = await response.json();

            if (response.ok) {
                window.showMessage(result.message, 'success');
                renderReportTable(result.data);
            } else {
                window.showMessage(result.message, 'error');
                renderReportTable([]);
            }
        } catch (error) {
            console.error('Error fetching special audit report:', error);
            window.showMessage('An error occurred while fetching the report.', 'error');
            renderReportTable([]);
        } finally {
            button.disabled = false;
            button.innerHTML = originalButtonText;
        }
    });
}

function fetchBranchesForArea(area, selectElement) {
    window.showLoading(selectElement.closest('.input-group'), 'Fetching branches...');
    fetch(`${window.FLASK_API_BASE_URL || 'http://127.0.0.1:5000'}/get_branches?area=${area}`)
        .then(response => response.json())
        .then(data => {
            if (data.branches) {
                data.branches.forEach(branch => {
                    const option = document.createElement('option');
                    option.value = branch;
                    option.textContent = branch;
                    selectElement.appendChild(option);
                });
            }
            window.hideLoading();
        })
        .catch(error => {
            console.error('Error fetching branches:', error);
            window.showMessage('Failed to load branches.', 'error');
            window.hideLoading();
        });
}

function renderReportTable(data) {
    const tableContainer = document.getElementById('monSpeAudReportContainer');
    if (!tableContainer) return;

    if (!data || data.length === 0) {
        tableContainer.innerHTML = '<p class="text-gray-500 text-center p-4">No data found for the selected criteria.</p>';
        return;
    }

    let tableHTML = `
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Column 1</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Column 2</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Column 3</th>
                    <!-- Add more headers as needed -->
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
    `;

    data.forEach(row => {
        tableHTML += `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${row.column1}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${row.column2}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${row.column3}</td>
                <!-- Add more cells as needed -->
            </tr>
        `;
    });

    tableHTML += `
            </tbody>
        </table>
    `;

    tableContainer.innerHTML = tableHTML;
}
