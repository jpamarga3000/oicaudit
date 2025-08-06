// js/tabs/operations_aging_report_top_borrowers.js

// This file contains functions specific to the "Top Borrowers" report.
// It assumes global variables like FLASK_API_BASE_URL, topBorrowersReportData, etc., are defined in operations_aging_report_main.js.

/**
 * Handles the processing request for Top Borrowers data.
 */
const generateTopBorrowersReport = function() {
    const branchInput = document.getElementById('agingBranch'); // Use the main branch input
    const statusInput = document.getElementById('topBorrowersStatus');
    const generateButton = document.getElementById('generateTopBorrowersReportButton');
    const topBorrowersTableContainer = document.getElementById('topBorrowersTableContainer');
    const areaInput = document.getElementById('agingArea');
    const dateInput = document.getElementById('agingDate'); // NEW: Get the main date input

    const area = areaInput.value.trim();
    const branch = branchInput.value.trim();
    const statusFilter = statusInput.value.trim();
    const selectedDate = dateInput.value.trim(); // NEW: Get the selected date

    // Check if Consolidated/ALL is selected, then status filter is not required
    const isConsolidatedOrAll = area === 'Consolidated' || branch === 'ALL';

    // NEW: selectedDate is now required for all cases unless it's a consolidated/all report where date might be latest
    if (!area || !branch || !selectedDate || (!isConsolidatedOrAll && !statusFilter)) {
        showMessage('Please select Area, Branch, Date, and Status for Top Borrowers Report (Status is not required for Consolidated/ALL branches).', 'error');
        return;
    }

    if (generateButton) generateButton.disabled = true;
    showMessage('Generating Top Borrowers Report... This may take a moment.', 'loading');
    
    topBorrowersTableContainer.innerHTML = '<h5 class="text-lg font-semibold text-gray-700 mb-2 p-2">TOP BORROWERS</h5><p class="text-gray-500 text-center">Top Borrowers report will appear here.</p>';
    topBorrowersReportData = []; // Clear stored data

    const formData = new FormData();
    formData.append('area', area);
    formData.append('branch', branch);
    formData.append('selected_date', selectedDate); // NEW: Send the selected date
    // Only append status filter if not Consolidated/ALL
    if (!isConsolidatedOrAll) {
        formData.append('status_filter', statusFilter);
    }


    fetch(`${FLASK_API_BASE_URL}/get_top_borrowers_report`, {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errorData => { throw new Error(errorData.message || 'Unknown error'); });
        }
        return response.json();
    })
    .then(result => {
        if (result.data && result.data.length > 0) {
            topBorrowersReportData = result.data;
            renderTopBorrowersTable(topBorrowersReportData);
            showMessage(result.message || 'Top Borrowers Report generated successfully!', 'success');
        } else {
            topBorrowersReportData = [];
            renderTopBorrowersTable([]);
            showMessage(result.message || 'No data found for the specified top borrowers criteria.', 'info');
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
        topBorrowersReportData = [];
        renderTopBorrowersTable([]);
    })
    .finally(() => {
        if (generateButton) generateButton.disabled = false;
        updateTopBorrowersReportUI();
    });
};

/**
 * Renders the "TOP BORROWERS" table.
 * @param {Array<Object>} data - The data for the table.
 */
function renderTopBorrowersTable(data) {
    const tableContainer = document.getElementById('topBorrowersTableContainer');
    if (!tableContainer) return;

    tableContainer.innerHTML = '<h5 class="text-lg font-semibold text-gray-700 mb-2 p-2">TOP BORROWERS</h5>';

    if (!data || data.length === 0) {
        tableContainer.innerHTML += '<p class="text-gray-500 text-center">No Top Borrowers data found for the specified criteria.</p>';
        return;
    }

    const table = document.createElement('table');
    table.className = 'min-w-full bg-white border border-gray-300 rounded-lg shadow-md';
    const thead = document.createElement('thead');
    const tbody = document.createElement('tbody');

    // First header row for merged headers
    const headerRow1 = document.createElement('tr');

    // NAME header (merged vertically)
    const thName = document.createElement('th');
    thName.className = 'py-3 px-4 bg-gray-100 text-center align-middle text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300';
    thName.textContent = 'NAME';
    thName.rowSpan = 2; // Merged across 2 rows
    headerRow1.appendChild(thName);

    // CID header (merged vertically)
    const thCid = document.createElement('th');
    thCid.className = 'py-3 px-4 bg-gray-100 text-center align-middle text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300';
    thCid.textContent = 'CID';
    thCid.rowSpan = 2; // Merged across 2 rows
    headerRow1.appendChild(thCid);

    // BRANCH header (merged vertically)
    const thBranch = document.createElement('th');
    thBranch.className = 'py-3 px-4 bg-gray-100 text-center align-middle text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300';
    thBranch.textContent = 'BRANCH';
    thBranch.rowSpan = 2; // Merged across 2 rows
    headerRow1.appendChild(thBranch);

    // CURRENT header (merged horizontally)
    const thCurrent = document.createElement('th');
    thCurrent.className = 'py-3 px-4 bg-gray-100 text-center align-middle text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300';
    thCurrent.textContent = 'CURRENT';
    thCurrent.colSpan = 2; // Merged across 2 columns
    headerRow1.appendChild(thCurrent);

    // PAST DUE header (merged horizontally)
    const thPastDue = document.createElement('th');
    thPastDue.className = 'py-3 px-4 bg-gray-100 text-center align-middle text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300';
    thPastDue.textContent = 'PAST DUE';
    thPastDue.colSpan = 2; // Merged across 2 columns
    headerRow1.appendChild(thPastDue);

    // TOTAL header (merged horizontally)
    const thTotal = document.createElement('th');
    thTotal.className = 'py-3 px-4 bg-gray-100 text-center align-middle text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300';
    thTotal.textContent = 'TOTAL';
    thTotal.colSpan = 2; // Merged across 2 columns
    headerRow1.appendChild(thTotal);

    thead.appendChild(headerRow1);

    // Second header row for sub-columns
    const headerRow2 = document.createElement('tr');
    // No need for NAME, CID, BRANCH here as they are rowSpan'd
    const subHeaders = ['ACCOUNT', 'BALANCE', 'ACCOUNT', 'BALANCE', 'ACCOUNT', 'BALANCE'];
    subHeaders.forEach(subHeaderText => {
        const th = document.createElement('th');
        th.className = 'py-3 px-4 bg-gray-100 text-center align-middle text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300';
        if (subHeaderText === 'BALANCE') { // Align BALANCE sub-headers right
            th.classList.add('text-right');
        }
        th.textContent = subHeaderText;
        headerRow2.appendChild(th);
    });
    thead.appendChild(headerRow2);
    table.appendChild(thead);

    // Table Body
    data.forEach(rowData => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-50';

        const tdName = document.createElement('td');
        tdName.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200 font-semibold whitespace-nowrap';
        tdName.textContent = rowData['NAME'] || '';
        tr.appendChild(tdName);

        const tdCid = document.createElement('td');
        tdCid.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200 text-center'; // CID can be centered
        tdCid.textContent = rowData['CID'] || '';
        tr.appendChild(tdCid);

        const tdBranch = document.createElement('td');
        tdBranch.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200 text-center'; // BRANCH can be centered
        tdBranch.textContent = rowData['BRANCH'] || '';
        tr.appendChild(tdBranch);

        const tdCurrentAccount = document.createElement('td');
        tdCurrentAccount.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200 text-center';
        tdCurrentAccount.textContent = rowData['CURRENT_ACCOUNT'] || 0;
        tr.appendChild(tdCurrentAccount);

        const tdCurrentBalance = document.createElement('td');
        tdCurrentBalance.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200 text-right';
        tdCurrentBalance.textContent = rowData['CURRENT_BALANCE'] || formatCurrency(0);
        tr.appendChild(tdCurrentBalance);

        const tdPastDueAccount = document.createElement('td');
        tdPastDueAccount.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200 text-center';
        tdPastDueAccount.textContent = rowData['PAST_DUE_ACCOUNT'] || 0;
        tr.appendChild(tdPastDueAccount);

        const tdPastDueBalance = document.createElement('td');
        tdPastDueBalance.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200 text-right';
        tdPastDueBalance.textContent = rowData['PAST_DUE_BALANCE'] || formatCurrency(0);
        tr.appendChild(tdPastDueBalance);

        const tdTotalAccount = document.createElement('td');
        tdTotalAccount.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200 text-center';
        tdTotalAccount.textContent = rowData['TOTAL_ACCOUNT'] || 0;
        tr.appendChild(tdTotalAccount);

        const tdTotalBalance = document.createElement('td');
        tdTotalBalance.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200 text-right';
        tdTotalBalance.textContent = rowData['TOTAL_BALANCE'] || formatCurrency(0);
        tr.appendChild(tdTotalBalance);

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
 * Updates the state of the "Generate Top Borrowers Report" button.
 */
function updateTopBorrowersReportUI() {
    const areaInput = document.getElementById('agingArea'); // Use the main area input
    const branchInput = document.getElementById('agingBranch'); // Use the main branch input
    const statusInput = document.getElementById('topBorrowersStatus');
    const generateButton = document.getElementById('generateTopBorrowersReportButton');
    const topBorrowersTableExists = document.querySelector('#topBorrowersTableContainer table');
    const topBorrowersReportActions = document.getElementById('topBorrowersReportActions');
    const searchInput = document.getElementById('topBorrowersSearchInput');
    const copyButton = document.getElementById('copyTopBorrowersTableButton');
    const dateInput = document.getElementById('agingDate'); // NEW: Get date input

    // NEW: Disable inputs if Consolidated or ALL is selected for Branch
    const isConsolidatedOrAll = areaInput.value.trim() === 'Consolidated' || branchInput.value.trim() === 'ALL';
    statusInput.disabled = isConsolidatedOrAll;


    if (generateButton) {
        // Enable button if Area is selected, and Branch is selected (can be 'ALL' or specific)
        // and Status is selected.
        // NEW: Also require a selected date
        generateButton.disabled = !(
            areaInput.value.trim() &&
            branchInput.value.trim() && // Branch can be 'ALL' or specific
            dateInput.value.trim() && // NEW: Require date selection
            (isConsolidatedOrAll || statusInput.value.trim()) // If consolidated/all, no need for status filter
        );
    }

    if (topBorrowersReportActions) {
        if (topBorrowersTableExists) {
            topBorrowersReportActions.classList.remove('hidden');
        } else {
            topBorrowersReportActions.classList.add('hidden');
        }
    }
    
    if (searchInput) {
        searchInput.disabled = !topBorrowersTableExists;
        if (!topBorrowersTableExists) searchInput.value = '';
    }
    if (copyButton) {
        copyButton.disabled = !topBorrowersTableExists;
    }
}

/**
 * Copies the content of the Top Borrowers table to the clipboard in TSV format.
 */
const copyTopBorrowersTable = function() {
    const table = document.querySelector('#topBorrowersTableContainer table');
    if (!table) {
        showMessage('No table data to copy.', 'info');
        return;
    }

    let csv = [];
    const rows = table.querySelectorAll('tr');

    for (let i = 0; i < rows.length; i++) {
        const row = [], cols = rows[i].querySelectorAll('td, th');
        for (let j = 0; j < cols.length; j++) {
            let text = cols[j].innerText.trim();
            if (text.startsWith('(') && text.endsWith(')')) {
                text = '-' + text.substring(1, text.length - 1).replace(/,/g, '');
            } else {
                text = text.replace(/,/g, '');
            }
            row.push(text);
        }
        csv.push(row.join('\t'));
    }

    const csvString = csv.join('\n');

    const textarea = document.createElement('textarea');
    textarea.value = csvString;
    textarea.style.position = 'fixed';
    textarea.style.opacity = 0;
    document.body.appendChild(textarea);
    textarea.select();

    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showMessage('Table data copied to clipboard!', 'success', '', 2000);
        } else {
            showMessage('Failed to copy table data.', 'error');
        }
    } catch (err) {
        console.error('Failed to copy:', err);
        showMessage('Error copying to clipboard. Please copy manually.', 'error');
    } finally {
        document.body.removeChild(textarea);
    }
};

/**
 * Filters the Top Borrowers table based on search input.
 */
const filterTopBorrowersTable = function() {
    const searchInput = document.getElementById('topBorrowersSearchInput');
    const filter = searchInput.value.toLowerCase();
    
    if (filter === '') {
        renderTopBorrowersTable(topBorrowersReportData);
    } else if (topBorrowersReportData.length > 0) {
        const filteredData = topBorrowersReportData.filter(row => {
            return Object.values(row).some(value => {
                return String(value).toLowerCase().includes(filter);
            });
        });
        renderTopBorrowersTable(filteredData);
    }
};
