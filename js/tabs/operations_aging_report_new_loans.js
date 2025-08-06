// js/tabs/operations_aging_report_new_loans.js

// This file contains functions specific to the "New Loans with Past Due Credit History" report
// and its associated loan details modal.
// It assumes global variables like FLASK_API_BASE_URL, newLoansReportData,
// newLoansCurrentSortKey, newLoansCurrentSortDirection, and formatCurrency are defined in operations_aging_report_main.js.

// Declare and initialize sorting state variables for the details modal within this file's scope
let newLoansDetailsCurrentSortKey = 'DATE'; // Default sort key for details modal
let newLoansDetailsCurrentSortDirection = 'desc'; // Default sort direction for details modal


/**
 * Populates the Year dropdown for the New Loans with Past Due Credit History report.
 * Starts from 2022 and goes up to the current year.
 */
function populateNewLoansYearDropdown() {
    const yearDropdown = document.getElementById('newLoansYear');
    if (!yearDropdown) return;

    const currentYear = new Date().getFullYear();
    let startYear = 2022;
    for (let year = startYear; year <= currentYear; year++) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearDropdown.appendChild(option);
    }
}

/**
 * Updates the state of the "Generate New Loans Report" button and actions bar.
 */
function updateNewLoansReportUI() {
    const areaInput = document.getElementById('agingArea');
    const branchInput = document.getElementById('agingBranch');
    const yearInput = document.getElementById('newLoansYear');
    const generateButton = document.getElementById('generateNewLoansReportButton');
    const newLoansReportActions = document.getElementById('newLoansReportActions');
    const tableExists = document.querySelector('#newLoansTableContainer table');
    const searchInput = document.getElementById('newLoansSearchInput');
    const copyButton = document.getElementById('copyNewLoansTableButton');

    // NEW: Disable inputs if Consolidated or ALL is selected for Branch
    const isConsolidatedOrAll = areaInput.value.trim() === 'Consolidated' || branchInput.value.trim() === 'ALL';
    yearInput.disabled = isConsolidatedOrAll;

    if (generateButton) {
        generateButton.disabled = !(
            areaInput.value.trim() &&
            branchInput.value.trim() &&
            (isConsolidatedOrAll || yearInput.value.trim()) // If consolidated/all, no need for year
        );
    }

    if (newLoansReportActions) {
        if (tableExists) {
            newLoansReportActions.classList.remove('hidden');
        } else {
            newLoansReportActions.classList.add('hidden');
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
 * Handles the processing request for New Loans with Past Due Credit History data.
 */
const generateNewLoansReport = function() {
    const areaInput = document.getElementById('agingArea');
    const branchInput = document.getElementById('agingBranch');
    const yearInput = document.getElementById('newLoansYear');
    const generateButton = document.getElementById('generateNewLoansReportButton');
    const newLoansTableContainer = document.getElementById('newLoansTableContainer');

    const area = areaInput.value.trim();
    const branch = branchInput.value.trim();
    const selectedYear = parseInt(yearInput.value);

    // Check if Consolidated/ALL is selected, then year is not required
    const isConsolidatedOrAll = area === 'Consolidated' || branch === 'ALL';

    if (!area || !branch || (!isConsolidatedOrAll && isNaN(selectedYear))) {
        showMessage('Please select Area, Branch, and Year for New Loans Report (Year is not required for Consolidated/ALL branches).', 'error');
        return;
    }

    if (generateButton) generateButton.disabled = true;
    showMessage('Generating New Loans Report... This may take a moment.', 'loading');
    
    newLoansTableContainer.innerHTML = '<p class="text-gray-500 text-center">New Loans with Past Due Credit History report will appear here.</p>';
    newLoansReportData = []; // Clear stored data

    const formData = new FormData();
    formData.append('area', area);
    formData.append('branch', branch);
    if (!isConsolidatedOrAll) { // Only append year if not Consolidated/ALL
         formData.append('selected_year', selectedYear);
    }

    fetch(`${FLASK_API_BASE_URL}/get_new_loans_with_past_due_history_report`, {
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
            newLoansReportData = result.data;
            // Reset sort state to default (Principal descending) after new data is loaded
            newLoansCurrentSortKey = 'PRINCIPAL';
            newLoansCurrentSortDirection = 'desc';
            renderNewLoansTable(newLoansReportData); // Initial render with default sort
            showMessage(result.message || 'New Loans Report generated successfully!', 'success');
        } else {
            newLoansReportData = [];
            renderNewLoansTable([]);
            showMessage(result.message || 'No data found for the specified new loans criteria.', 'info');
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
        newLoansReportData = [];
        renderNewLoansTable([]);
    })
    .finally(() => {
        if (generateButton) generateButton.disabled = false;
        updateNewLoansReportUI();
    });
};

/**
 * Sorts the newLoansReportData and re-renders the table.
 * @param {string} sortKey - The key to sort by (e.g., 'NAME', 'PRINCIPAL').
 * @param {string} sortDirection - 'asc' or 'desc'.
 */
function sortNewLoansTable(sortKey, sortDirection) {
    // Store current sort state
    newLoansCurrentSortKey = sortKey;
    newLoansCurrentSortDirection = sortDirection;

    const sortedData = [...newLoansReportData].sort((a, b) => {
        let valA = a[sortKey];
        let valB = b[sortKey];

        // Handle numeric columns (remove currency formatting for sorting)
        if (['PRINCIPAL', 'BALANCE'].includes(sortKey)) {
            valA = parseFloat(String(valA).replace(/₱|,/g, ''));
            valB = parseFloat(String(valB).replace(/₱|,/g, ''));
        } else if (['ACCOUNTS', '30-365 DAYS', 'OVER 365 DAYS'].includes(sortKey)) {
            valA = parseInt(valA);
            valB = parseInt(valB);
        } else {
            // Default to string comparison for other columns
            valA = String(valA).toLowerCase();
            valB = String(valB).toLowerCase();
        }

        if (valA < valB) {
            return sortDirection === 'asc' ? -1 : 1;
        }
        if (valA > valB) {
            return sortDirection === 'asc' ? 1 : -1;
        }
        return 0;
    });

    renderNewLoansTable(sortedData);
}

/**
 * Renders the "New Loans with Past Due Credit History" table.
 * @param {Array<Object>} data - The data for the table.
 */
function renderNewLoansTable(data) {
    const tableContainer = document.getElementById('newLoansTableContainer');
    if (!tableContainer) return;

    tableContainer.innerHTML = '<h5 class="text-lg font-semibold text-gray-700 mb-2 p-2">NEW LOANS WITH PAST DUE CREDIT HISTORY</h5>';

    if (!data || data.length === 0) {
        tableContainer.innerHTML += '<p class="text-gray-500 text-center">No data found for the specified criteria.</p>';
        return;
    }

    const table = document.createElement('table');
    table.className = 'min-w-full bg-white border border-gray-300 rounded-lg shadow-md';
    const thead = document.createElement('thead');
    const tbody = document.createElement('tbody');

    const headers = [
        { key: 'NAME', label: 'NAME', align: 'left', sortable: true },
        { key: 'BRANCH', label: 'BRANCH', align: 'left', sortable: true },
        { key: 'ACCOUNTS', label: 'ACCOUNTS', align: 'center', sortable: true },
        { key: 'PRINCIPAL', label: 'PRINCIPAL', align: 'right', sortable: true, clickable: true }, // Made clickable
        { key: 'BALANCE', label: 'BALANCE', align: 'right', sortable: true },
        { key: '30-365 DAYS', label: '30-365 DAYS', align: 'center', sortable: true, clickable: true }, // Made clickable
        { key: 'OVER 365 DAYS', label: 'OVER 365 DAYS', align: 'center', sortable: true, clickable: true } // Made clickable
    ];

    const headerRow = document.createElement('tr');
    headers.forEach(headerInfo => {
        const th = document.createElement('th');
        th.className = `py-3 px-4 bg-gray-100 text-${headerInfo.align} align-middle text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300`;
        th.textContent = headerInfo.label;

        if (headerInfo.sortable) {
            th.classList.add('cursor-pointer', 'hover:bg-gray-200');
            th.setAttribute('data-sort-key', headerInfo.key);
            
            // Add sort icon
            const sortIcon = document.createElement('i');
            sortIcon.className = 'fas ml-2';
            if (newLoansCurrentSortKey === headerInfo.key) {
                sortIcon.classList.add(newLoansCurrentSortDirection === 'asc' ? 'fa-sort-up' : 'fa-sort-down');
            } else {
                sortIcon.classList.add('fa-sort'); // Neutral sort icon
            }
            th.appendChild(sortIcon);

            th.addEventListener('click', () => {
                const currentKey = headerInfo.key;
                let newDirection = 'asc';
                if (newLoansCurrentSortKey === currentKey && newLoansCurrentSortDirection === 'asc') {
                    newDirection = 'desc';
                }
                sortNewLoansTable(currentKey, newDirection);
            });
        }
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    data.forEach(rowData => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-50';

        headers.forEach(headerInfo => {
            const td = document.createElement('td');
            td.className = `py-2 px-4 text-sm text-gray-800 border-b border-gray-200 text-${headerInfo.align}`;
            let value = rowData[headerInfo.key] !== undefined ? rowData[headerInfo.key] : '';
            td.textContent = value;

            if (headerInfo.clickable) { // Make cell clickable if headerInfo.clickable is true
                td.classList.add('cursor-pointer', 'text-blue-600', 'hover:underline', 'font-semibold');
                td.addEventListener('click', () => {
                    const borrowerName = rowData['NAME'];
                    const selectedYear = document.getElementById('newLoansYear').value;
                    let categoryType;

                    if (headerInfo.key === 'PRINCIPAL') {
                        categoryType = 'new_loans';
                    } else if (headerInfo.key === '30-365 DAYS') {
                        categoryType = '30-365_history';
                    } else if (headerInfo.key === 'OVER 365 DAYS') {
                        categoryType = 'over_365_history';
                    }
                    showNewLoansDetailsModal(borrowerName, selectedYear, categoryType);
                });
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    tableContainer.appendChild(table);

    const tableHeader = tableContainer.querySelector('thead');
    if (tableHeader) {
        tableHeader.style.position = 'sticky';
        tableHeader.style.top = '0';
        tableHeader.style.zIndex = '1';
    }
}

/**
 * Copies the content of the New Loans with Past Due Credit History table to the clipboard in TSV format.
 */
const copyNewLoansTable = function() {
    const table = document.querySelector('#newLoansTableContainer table');
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
 * Filters the New Loans with Past Due Credit History table based on search input.
 */
const filterNewLoansTable = function() {
    const searchInput = document.getElementById('newLoansSearchInput');
    const filter = searchInput.value.toLowerCase();
    
    if (filter === '') {
        renderNewLoansTable(newLoansReportData);
    } else if (newLoansReportData.length > 0) {
        const filteredData = newLoansReportData.filter(row => {
            return Object.values(row).some(value => {
                return String(value).toLowerCase().includes(filter);
            });
        });
        renderNewLoansTable(filteredData);
    }
};

/**
 * Shows a modal with detailed loan information.
 * @param {string} borrowerName - The name of the borrower.
 * @param {number} selectedYear - The year selected for the main report.
 * @param {string} categoryType - 'new_loans', '30-365_history', or 'over_365_history'.
 */
async function showNewLoansDetailsModal(borrowerName, selectedYear, categoryType) {
    const modal = document.getElementById('newLoansDetailsModal');
    const modalTitle = document.getElementById('newLoansDetailsModalTitle');
    const modalTableContainer = document.getElementById('newLoansDetailsModalTableContainer');
    const modalSearchInput = document.getElementById('newLoansDetailsModalSearchInput');
    const modalCopyButton = document.getElementById('newLoansDetailsModalCopyButton');

    if (!modal || !modalTitle || !modalTableContainer) {
        console.error("New Loans Details Modal elements not found!");
        return;
    }

    modalTitle.textContent = `Details for ${borrowerName} (${categoryType.replace('_', ' ').toUpperCase()})`;
    modalTableContainer.innerHTML = '<p class="text-gray-500 text-center">Loading details...</p>';
    modalSearchInput.value = ''; // Clear previous search
    modalSearchInput.disabled = true;
    modalCopyButton.disabled = true;

    modal.classList.remove('hidden');
    modal.classList.add('flex'); // Use flex to center content

    // Fetch details from backend
    const area = document.getElementById('agingArea').value.trim();
    const branch = document.getElementById('agingBranch').value.trim();

    const formData = new FormData();
    formData.append('area', area);
    formData.append('branch', branch);
    formData.append('name', borrowerName);
    formData.append('selected_year', selectedYear);
    formData.append('category_type', categoryType);

    try {
        const response = await fetch(`${FLASK_API_BASE_URL}/get_new_loans_details`, {
            method: 'POST',
            body: formData,
        });
        const result = await response.json();

        if (response.ok && result.data && result.data.length > 0) {
            renderNewLoansDetailsTable(result.data);
            modalSearchInput.disabled = false;
            modalCopyButton.disabled = false;
        } else {
            modalTableContainer.innerHTML = `<p class="text-gray-500 text-center">${result.message || 'No details found.'}</p>`;
        }
    }
    catch (error) { // Corrected: Added opening curly brace for catch block
        console.error('Error fetching new loans details:', error);
        modalTableContainer.innerHTML = `<p class="text-red-500 text-center">Error loading details: ${error.message}</p>`;
    }
}

/**
 * Renders the detailed loan table inside the modal.
 * @param {Array<Object>} data - The detailed loan data.
 */
function renderNewLoansDetailsTable(data) {
    const tableContainer = document.getElementById('newLoansDetailsModalTableContainer');
    if (!tableContainer) return;

    tableContainer.innerHTML = ''; // Clear loading message

    const table = document.createElement('table');
    table.className = 'min-w-full bg-white border border-gray-300 rounded-lg shadow-md';
    const thead = document.createElement('thead');
    const tbody = document.createElement('tbody');

    const headers = [
        { key: 'DATE', label: 'DATE', align: 'center', sortable: true }, // Added DATE
        { key: 'NAME', label: 'NAME', align: 'left', sortable: true },
        { key: 'ACCOUNT', label: 'ACCOUNT', align: 'left', sortable: true },
        { key: 'PRINCIPAL', label: 'PRINCIPAL', align: 'right', sortable: true },
        { key: 'BALANCE', label: 'BALANCE', align: 'right', sortable: true },
        { key: 'PRODUCT', label: 'PRODUCT', align: 'left', sortable: true },
        { key: 'DISBURSED', label: 'DISBURSED', align: 'center', sortable: true },
        { key: 'MATURITY', label: 'MATURITY', align: 'center', sortable: true },
        { key: 'AGING', label: 'AGING', align: 'center', sortable: true }
    ];

    const headerRow = document.createElement('tr');
    headers.forEach(headerInfo => {
        const th = document.createElement('th');
        th.className = `py-3 px-4 bg-gray-100 text-${headerInfo.align} align-middle text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300`;
        th.textContent = headerInfo.label;

        if (headerInfo.sortable) {
            th.classList.add('cursor-pointer', 'hover:bg-gray-200');
            th.setAttribute('data-sort-key', headerInfo.key);
            
            // Add sort icon
            const sortIcon = document.createElement('i');
            sortIcon.className = 'fas ml-2';
            if (newLoansDetailsCurrentSortKey === headerInfo.key) {
                sortIcon.classList.add(newLoansDetailsCurrentSortDirection === 'asc' ? 'fa-sort-up' : 'fa-sort-down');
            } else {
                sortIcon.classList.add('fa-sort'); // Neutral sort icon
            }
            th.appendChild(sortIcon);

            th.addEventListener('click', () => {
                const currentKey = headerInfo.key;
                let newDirection = 'asc';
                if (newLoansDetailsCurrentSortKey === currentKey && newLoansDetailsCurrentSortDirection === 'asc') {
                    newDirection = 'desc';
                }
                sortNewLoansDetailsTable(data, currentKey, newDirection); // Pass data to sort
            });
        }
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    tbody.innerHTML = ''; // Clear existing rows if re-rendering
    data.forEach(rowData => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-50';
        headers.forEach(headerInfo => {
            const td = document.createElement('td');
            td.className = `py-2 px-4 text-sm text-gray-800 border-b border-gray-200 text-${headerInfo.align}`;
            let value = rowData[headerInfo.key] !== undefined ? rowData[headerInfo.key] : '';
            td.textContent = value;

            if (headerInfo.clickable) { // Make cell clickable if headerInfo.clickable is true
                td.classList.add('cursor-pointer', 'text-blue-600', 'hover:underline', 'font-semibold');
                td.addEventListener('click', () => {
                    const borrowerName = rowData['NAME'];
                    const selectedYear = document.getElementById('newLoansYear').value;
                    let categoryType;

                    if (headerInfo.key === 'PRINCIPAL') {
                        categoryType = 'new_loans';
                    } else if (headerInfo.key === '30-365 DAYS') {
                        categoryType = '30-365_history';
                    } else if (headerInfo.key === 'OVER 365 DAYS') {
                        categoryType = 'over_365_history';
                    }
                    showNewLoansDetailsModal(borrowerName, selectedYear, categoryType);
                });
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    tableContainer.appendChild(table);

    const tableHeader = tableContainer.querySelector('thead');
    if (tableHeader) {
        tableHeader.style.position = 'sticky';
        tableHeader.style.top = '0';
        tableHeader.style.zIndex = '1';
    }
}

/**
 * Sorts the data for the modal table and re-renders it.
 * @param {Array<Object>} data - The data to sort.
 * @param {string} sortKey - The key to sort by.
 * @param {string} sortDirection - 'asc' or 'desc'.
 */
function sortNewLoansDetailsTable(data, sortKey, sortDirection) {
    newLoansDetailsCurrentSortKey = sortKey;
    newLoansDetailsCurrentSortDirection = sortDirection;

    const sortedData = [...data].sort((a, b) => {
        let valA = a[sortKey];
        let valB = b[sortKey];

        // Handle numeric columns (remove currency formatting for sorting)
        if (['PRINCIPAL', 'BALANCE'].includes(sortKey)) {
            valA = parseFloat(String(valA).replace(/₱|,/g, ''));
            valB = parseFloat(String(valB).replace(/₱|,/g, ''));
        } else if (['ACCOUNTS'].includes(sortKey)) { // Add other numeric keys as needed
            valA = parseInt(valA);
            valB = parseInt(valB);
        } else if (['DISBURSED', 'MATURITY', 'DATE'].includes(sortKey)) { // Handle dates, including new DATE column
            valA = new Date(valA);
            valB = new Date(valB);
        } else {
            valA = String(valA).toLowerCase();
            valB = String(valB).toLowerCase();
        }

        if (valA < valB) {
            return sortDirection === 'asc' ? -1 : 1;
        }
        if (valA > valB) {
            return sortDirection === 'asc' ? 1 : -1;
        }
        return 0;
    });
    renderNewLoansDetailsTable(sortedData);
}

/**
 * Filters the detailed loan table within the modal.
 */
function filterNewLoansDetailsTable() {
    const searchInput = document.getElementById('newLoansDetailsModalSearchInput');
    const filter = searchInput.value.toLowerCase();
    
    // Re-fetch the original data for the current modal context
    const borrowerName = document.getElementById('newLoansDetailsModalTitle').textContent.split('(')[0].trim().replace('Details for ', '');
    const selectedYear = parseInt(document.getElementById('newLoansYear').value);
    const categoryType = document.getElementById('newLoansDetailsModalTitle').textContent.split('(')[1].split(')')[0].trim().toLowerCase().replace(/ /g, '_');

    // This requires re-fetching the original data or storing it globally for the modal
    // For simplicity, I'll assume `showNewLoansDetailsModal` re-fetches and re-renders
    // or we need a global variable to store the raw modal data after fetch.
    // For now, I'll make a simplified filter that operates on the currently rendered table rows.
    // A more robust solution would store the raw fetched data for the modal.

    const tableBody = document.querySelector('#newLoansDetailsModalTableContainer tbody');
    if (!tableBody) return;

    const rows = tableBody.querySelectorAll('tr');
    rows.forEach(row => {
        const textContent = row.textContent.toLowerCase();
        if (textContent.includes(filter)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

/**
 * Copies the content of the detailed loan table in the modal to the clipboard.
 */
function copyNewLoansDetailsTable() {
    const table = document.querySelector('#newLoansDetailsModalTableContainer table');
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
}

/**
 * Hides the loan details modal.
 */
function hideNewLoansDetailsModal() {
    const modal = document.getElementById('newLoansDetailsModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        document.getElementById('newLoansDetailsModalTableContainer').innerHTML = ''; // Clear content
    }
}
