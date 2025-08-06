// js/tabs/operations_aging_report_provisions.js

// This file contains functions specific to the "Accounts Contribute to Provisions" report.
// It assumes global variables like FLASK_API_BASE_URL, provisionsReportData, etc., are defined in operations_aging_report_main.js.

/**
 * Populates the Year dropdown for the Provisions report.
 * Starts from 2022 and goes up to the current year.
 */
function populateProvisionsYearDropdown() {
    const yearDropdown = document.getElementById('provisionYear');
    if (!yearDropdown) return;

    const currentYear = new Date().getFullYear();
    let startYear = 2022; // As requested

    yearDropdown.innerHTML = '<option value="">Select Year</option>';
    for (let year = startYear; year <= currentYear; year++) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearDropdown.appendChild(option);
    }
}

/**
 * Updates the state of the "Generate Provisions Report" button and actions bar.
 */
function updateProvisionsReportUI() {
    const areaInput = document.getElementById('agingArea'); // Use the main area input
    const branchInput = document.getElementById('agingBranch'); // Use the main branch input
    const monthInput = document.getElementById('provisionMonth');
    const yearInput = document.getElementById('provisionYear');
    const agingInput = document.getElementById('provisionAging');
    const generateButton = document.getElementById('generateProvisionsReportButton');
    const provisionsReportActions = document.getElementById('provisionsReportActions');
    const perAccountsTableExists = document.querySelector('#perAccountsTableContainer table');
    const perMemberTableExists = document.querySelector('#perMemberTableContainer table');
    const searchInput = document.getElementById('provisionsSearchInput');
    const copyButton = document.getElementById('copyProvisionsReportTablesButton');

    // NEW: Disable inputs if Consolidated or ALL is selected for Branch
    const isConsolidatedOrAll = areaInput.value.trim() === 'Consolidated' || branchInput.value.trim() === 'ALL';
    monthInput.disabled = isConsolidatedOrAll;
    yearInput.disabled = isConsolidatedOrAll;
    agingInput.disabled = isConsolidatedOrAll;


    if (generateButton) {
        // Enable button if Area is selected, and Branch is selected (can be 'ALL' or specific)
        // and all other fields are filled.
        generateButton.disabled = !(
            areaInput.value.trim() &&
            branchInput.value.trim() && // Branch can be 'ALL' or specific
            (isConsolidatedOrAll || (monthInput.value.trim() && yearInput.value.trim() && agingInput.value.trim())) // If consolidated/all, no need for other fields
        );
    }

    // Define tableExists locally for this function
    const tableExists = perAccountsTableExists || perMemberTableExists;

    // Toggle visibility of the search/copy container for provisions
    if (provisionsReportActions) {
        if (tableExists) {
            provisionsReportActions.classList.remove('hidden');
        } else {
            provisionsReportActions.classList.add('hidden');
        }
    }
    
    if (searchInput) {
        searchInput.disabled = !tableExists;
        if (!tableExists) searchInput.value = '';
    }
    if (copyButton) {
        copyButton.disabled = !tableExists;
    }
}

/**
 * Handles the processing request for Accounts Contribute to Provisions data.
 */
const generateProvisionsReport = function() {
    const branchInput = document.getElementById('agingBranch'); // Use the main branch input
    const monthInput = document.getElementById('provisionMonth');
    const yearInput = document.getElementById('provisionYear');
    const agingInput = document.getElementById('provisionAging');
    const generateButton = document.getElementById('generateProvisionsReportButton');
    const perAccountsTableContainer = document.getElementById('perAccountsTableContainer');
    const perMemberTableContainer = document.getElementById('perMemberTableContainer');
    const areaInput = document.getElementById('agingArea'); // Get area input

    const area = areaInput.value.trim(); // Get area value
    const branch = branchInput.value.trim();
    const selectedMonth = parseInt(monthInput.value);
    const selectedYear = parseInt(yearInput.value);
    const selectedAgingCategory = agingInput.value.trim();

    // Check if Consolidated/ALL is selected, then month, year, aging are not required
    const isConsolidatedOrAll = area === 'Consolidated' || branch === 'ALL';

    if (!area || !branch || (!isConsolidatedOrAll && (isNaN(selectedMonth) || isNaN(selectedYear) || !selectedAgingCategory))) {
        showMessage('Please select Area, Branch, Month, Year, and Aging for Provisions Report (Month, Year, Aging are not required for Consolidated/ALL branches).', 'error');
        return;
    }

    if (generateButton) generateButton.disabled = true;
    showMessage('Generating Provisions Report... This may take a moment.', 'loading');
    
    perAccountsTableContainer.innerHTML = '<h5 class="text-lg font-semibold text-gray-700 mb-2 p-2">PER ACCOUNTS</h5><p class="text-gray-500 text-center">Per Accounts report will appear here.</p>';
    perMemberTableContainer.innerHTML = '<h5 class="text-lg font-semibold text-gray-700 mb-2 p-2">PER MEMBER</h5><p class="text-gray-500 text-center">Per Member report will appear here.</p>';
    provisionsReportData = { per_accounts_data: [], per_member_data: [] }; // Clear stored data


    const formData = new FormData();
    formData.append('area', area); // Send area to backend
    formData.append('branch', branch);
    // Only append month, year, aging if not Consolidated/ALL
    if (!isConsolidatedOrAll) {
        formData.append('selected_month', selectedMonth);
        formData.append('selected_year', selectedYear);
        formData.append('selected_aging_category', selectedAgingCategory);
    }

    fetch(`${FLASK_API_BASE_URL}/get_accounts_contribute_to_provisions_report`, {
        method: 'POST',
        body: formData,
    })
    .then(response => { // Capture response here
        if (!response.ok) {
            return response.json().then(errorData => { throw new Error(errorData.message || 'Unknown error'); });
        }
        return response.json();
    })
    .then(result => {
        // result is now the parsed JSON from a successful response
        if (result.data && (result.data.per_accounts_data.length > 0 || result.data.per_member_data.length > 0)) {
            provisionsReportData.per_accounts_data = result.data.per_accounts_data;
            provisionsReportData.per_member_data = result.data.per_member_data;
            renderPerAccountsTable(provisionsReportData.per_accounts_data, selectedMonth, selectedYear);
            renderPerMemberTable(provisionsReportData.per_member_data, selectedYear); // Pass selectedYear
            showMessage(result.message || 'Provisions Report generated successfully!', 'success');
        } else {
            renderPerAccountsTable([], selectedMonth, selectedYear); // Render empty
            renderPerMemberTable([], selectedYear); // Render empty
            showMessage(result.message || 'No data found for the specified provisions criteria.', 'info');
        }

    })
    .catch(error => {
        console.error('Fetch error:', error);
        showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
        provisionsReportData = { per_accounts_data: [], per_member_data: [] };
        renderPerAccountsTable([], selectedMonth, selectedYear);
        renderPerMemberTable([], selectedYear);
    })
    .finally(() => {
        if (generateButton) generateButton.disabled = false;
        updateProvisionsReportUI();
    });
};

/**
 * Renders the "PER ACCOUNTS" table.
 * @param {Array<Object>} data - The data for the table.
 * @param {number} selectedMonth - The selected month (1-12).
 * @param {number} selectedYear - The selected year.
 */
function renderPerAccountsTable(data, selectedMonth, selectedYear) {
    const tableContainer = document.getElementById('perAccountsTableContainer');
    if (!tableContainer) return;

    tableContainer.innerHTML = '<h5 class="text-lg font-semibold text-gray-700 mb-2 p-2">PER ACCOUNTS</h5>'; // Reset content

    if (!data || data.length === 0) {
        tableContainer.innerHTML += '<p class="text-gray-500 text-center">No Per Accounts data found for the specified criteria.</p>';
        return;
    }

    const table = document.createElement('table');
    table.className = 'min-w-full bg-white border border-gray-300 rounded-lg shadow-md';
    const thead = document.createElement('thead');
    const tbody = document.createElement('tbody');

    const monthName = new Date(selectedYear, selectedMonth - 1, 1).toLocaleString('en-US', { month: 'short' });
    
    // Updated headers array to include 'PROVISION'
    const headers = [
        'ACCOUNT', 'NAME', 'CID', 'BRANCH', 'DISBURSED', 'MATURITY', 'PRINCIPAL', // Added CID, BRANCH
        `BALANCE (DEC, ${selectedYear - 1})`, `AGING (DEC, ${selectedYear - 1})`,
        `BALANCE (${monthName} ${selectedYear})`, `AGING (${monthName} ${selectedYear})`,
        `PROVISION (Inc/Dec) ${selectedYear}` // Updated PROVISION header
    ];

    // DEBUG: Log the headers array to console
    console.log("renderPerAccountsTable: Headers being used:", headers);

    const headerRow = document.createElement('tr');
    headers.forEach(headerText => {
        const th = document.createElement('th');
        th.className = 'py-3 px-4 bg-gray-100 text-center align-middle text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300'; // Centered and middle aligned
        if (headerText.includes('BALANCE') || headerText.includes('PRINCIPAL') || headerText.includes('PROVISION')) { // Updated header check to include "PROVISION"
            th.classList.add('text-right');
        }
        th.textContent = headerText;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    data.forEach(rowData => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-50';
        headers.forEach(headerText => {
            const td = document.createElement('td');
            td.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200';
            let value;
            // FIX: Use direct keys from rowData for consistency with backend output
            if (headerText === 'ACCOUNT') value = rowData['ACCOUNT'];
            else if (headerText === 'NAME') value = rowData['NAME'];
            else if (headerText === 'CID') value = rowData['CID'];
            else if (headerText === 'BRANCH') value = rowData['BRANCH'];
            else if (headerText === 'DISBURSED') value = rowData['DISBURSED'];
            else if (headerText === 'MATURITY') value = rowData['MATURITY'];
            else if (headerText === 'PRINCIPAL') value = rowData['PRINCIPAL'];
            // Corrected access for previous year's balance and aging
            else if (headerText.includes(`BALANCE (DEC, ${selectedYear - 1})`)) value = rowData['BALANCE_DEC_PREV_YEAR'];
            else if (headerText.includes(`AGING (DEC, ${selectedYear - 1})`)) value = rowData['AGING_DEC_PREV_YEAR'];
            // Access for current year's balance and aging
            else if (headerText.includes(`BALANCE (${monthName} ${selectedYear})`)) value = rowData['BALANCE_INPUTTED_MMYYYY'];
            else if (headerText.includes(`AGING (${monthName} ${selectedYear})`)) value = rowData['AGING_INPUTTED_MMYYYY'];
            else if (headerText.includes('PROVISION')) {
                value = rowData['PROVISION'];
            }
            
            if (headerText.includes('BALANCE') || headerText.includes('PRINCIPAL') || headerText.includes('PROVISION')) { // Updated header check
                td.classList.add('text-right');
            }
            td.textContent = value !== undefined ? value : '';
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    tableContainer.appendChild(table);

    // Make header sticky (requires the table-scroll-wrapper to have overflow-y)
    const tableHeader = tableContainer.querySelector('thead');
    if (tableHeader) {
        tableHeader.style.position = 'sticky';
        tableHeader.style.top = '0';
        tableHeader.style.zIndex = '1';
    }
}

/**
 * Renders the "PER MEMBER" table.
 * @param {Array<Object>} data - The data for the table.
 * @param {number} selectedYear - The selected year.
 */
function renderPerMemberTable(data, selectedYear) { // Added selectedYear parameter
    const tableContainer = document.getElementById('perMemberTableContainer');
    if (!tableContainer) return;

    tableContainer.innerHTML = '<h5 class="text-lg font-semibold text-gray-700 mb-2 p-2">PER MEMBER</h5>'; // Reset content

    if (!data || data.length === 0) {
        tableContainer.innerHTML += '<p class="text-gray-500 text-center">No Per Member data found for the specified criteria.</p>';
        return;
    }

    const table = document.createElement('table');
    table.className = 'min-w-full bg-white border border-gray-300 rounded-lg shadow-md';
    const thead = document.createElement('thead');
    const tbody = document.createElement('tbody');

    const selectedMonth = document.getElementById('provisionMonth').value; // Get selected month for dynamic header
    const monthName = new Date(selectedYear, selectedMonth - 1, 1).toLocaleString('en-US', { month: 'short' });

    const headers = [
        'NAME', 'CID', 'BRANCHES INVOLVED', 'TOTAL PRINCIPAL', `TOTAL BALANCE (DEC, ${selectedYear - 1})`, `TOTAL BALANCE (${monthName} ${selectedYear})`, `TOTAL PROVISION (Inc/Dec) ${selectedYear}`, 'ACCOUNT COUNT' // Updated TOTAL BALANCE and TOTAL PROVISION header
    ];

    const headerRow = document.createElement('tr');
    headers.forEach(headerText => {
        const th = document.createElement('th');
        th.className = 'py-3 px-4 bg-gray-100 text-center align-middle text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300'; // Centered and middle aligned
        if (headerText.includes('TOTAL BALANCE') || headerText.includes('TOTAL PRINCIPAL') || headerText.includes('TOTAL PROVISION')) { // NEW: Added 'TOTAL PROVISION'
            th.classList.add('text-right');
        } else if (headerText === 'ACCOUNT COUNT') {
            th.classList.add('text-center');
        }
        th.textContent = headerText;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    data.forEach(rowData => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-50';
        headers.forEach(headerText => {
            const td = document.createElement('td');
            td.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200';
            let value;
            // FIX: Use direct keys from rowData for consistency with backend output
            if (headerText === 'NAME') value = rowData['NAME'];
            else if (headerText === 'CID') value = rowData['CID'];
            else if (headerText === 'BRANCHES INVOLVED') value = rowData['BRANCHES_INVOLVED'];
            else if (headerText === 'TOTAL PRINCIPAL') value = rowData['TOTAL_PRINCIPAL'];
            // Corrected access for previous year's total balance
            else if (headerText.includes(`TOTAL BALANCE (DEC, ${selectedYear - 1})`)) value = rowData['TOTAL_BALANCE_DEC_PREV_YEAR'];
            // Access for current year's total balance
            else if (headerText.includes(`TOTAL BALANCE (${monthName} ${selectedYear})`)) value = rowData['TOTAL_BALANCE_INPUTTED_MMYYYY'];
            else if (headerText.includes('TOTAL PROVISION')) {
                value = rowData['TOTAL_PROVISION'];
            }
            else if (headerText === 'ACCOUNT COUNT') value = rowData['ACCOUNT_COUNT'];
            
            if (headerText.includes('TOTAL BALANCE') || headerText.includes('TOTAL PRINCIPAL') || headerText.includes('TOTAL PROVISION')) { // NEW: Added 'TOTAL PROVISION'
                td.classList.add('text-right');
            } else if (headerText === 'ACCOUNT COUNT') {
                td.classList.add('text-center');
            }
            td.textContent = value !== undefined ? value : '';
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    tableContainer.appendChild(table);

    // Make header sticky (requires the table-scroll-wrapper to have overflow-y)
    const tableHeader = tableContainer.querySelector('thead');
    if (tableHeader) {
        tableHeader.style.position = 'sticky';
        tableHeader.style.top = '0';
        tableHeader.style.zIndex = '1';
    }
}


/**
 * Copies the content of both provisions tables to the clipboard.
 */
const copyProvisionsReportTables = function() {
    const perAccountsTable = document.querySelector('#perAccountsTableContainer table');
    const perMemberTable = document.querySelector('#perMemberTableContainer table');
    let combinedText = [];

    if (perAccountsTable) {
        combinedText.push("PER ACCOUNTS\n");
        let rows = perAccountsTable.querySelectorAll('tr');
        rows.forEach(row => {
            let rowData = Array.from(row.querySelectorAll('th, td')).map(cell => cell.innerText.trim().replace(/,/g, ''));
            combinedText.push(rowData.join('\t'));
        });
        combinedText.push("\n\n"); // Add spacing between tables
    }

    if (perMemberTable) {
        combinedText.push("PER MEMBER\n");
        let rows = perMemberTable.querySelectorAll('tr');
        rows.forEach(row => {
            let rowData = Array.from(row.querySelectorAll('th, td')).map(cell => cell.innerText.trim().replace(/,/g, ''));
            combinedText.push(rowData.join('\t'));
        });
    }

    const textToCopy = combinedText.join('\n');

    const textarea = document.createElement('textarea');
    textarea.value = textToCopy;
    textarea.style.position = 'fixed';
    textarea.style.opacity = 0;
    document.body.appendChild(textarea);
    textarea.select();

    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showMessage('Provisions tables data copied to clipboard!', 'success', '', 2000);
        } else {
            showMessage('Failed to copy provisions tables data.', 'error');
        }
    } catch (err) {
        console.error('Failed to copy:', err);
        showMessage('Error copying to clipboard. Please copy manually.', 'error');
    } finally {
        document.body.removeChild(textarea);
    }
};

/**
 * Filters both provisions tables based on search input.
 */
const filterProvisionsReportTables = function() {
    const searchInput = document.getElementById('provisionsSearchInput');
    const filter = searchInput.value.toLowerCase();
    
    if (provisionsReportData.per_accounts_data.length > 0) {
        const filteredAccounts = provisionsReportData.per_accounts_data.filter(row => {
            return Object.values(row).some(value => String(value).toLowerCase().includes(filter));
        });
        renderPerAccountsTable(filteredAccounts, document.getElementById('provisionMonth').value, document.getElementById('provisionYear').value);
    } else {
         renderPerAccountsTable([], document.getElementById('provisionMonth').value, document.getElementById('provisionYear').value);
    }

    if (provisionsReportData.per_member_data.length > 0) {
        const filteredMembers = provisionsReportData.per_member_data.filter(row => {
            return Object.values(row).some(value => String(value).toLowerCase().includes(filter));
        });
        renderPerMemberTable(filteredMembers, document.getElementById('provisionYear').value); // Pass selectedYear
    } else {
         renderPerMemberTable([], document.getElementById('provisionYear').value); // Pass selectedYear
    }
};
