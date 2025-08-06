// js/tabs/operations_aging_report_aging_history.js

// This file contains functions specific to the "Aging History per Member's Loan" report.
// It assumes global variables like FLASK_API_BASE_URL, agingReportData, etc., are defined in operations_aging_report_main.js.

/**
 * Handles the processing request for Aging History per Member's Loan data.
 */
const processOperationsAgingReport = function() {
    const areaInput = document.getElementById('agingArea');
    const branchInput = document.getElementById('agingBranch');
    const nameInput = document.getElementById('agingName');
    const cidInput = document.getElementById('agingCid');
    const processButton = document.getElementById('processAgingReportButton');
    const reportContainer = document.getElementById('agingReportTableContainer');

    const area = areaInput.value.trim();
    const branch = branchInput.value.trim();
    const name = nameInput.value.trim();
    const cid = cidInput.value.trim();

    // For Aging History per Member's Loan, 'Consolidated' or 'ALL' branch is not applicable
    if (area === 'Consolidated' || branch === 'ALL' || branch === 'Consolidated') {
        showMessage('Please select a specific Branch for Aging History per Member\'s Loan. "Consolidated" or "ALL" is not applicable here.', 'error');
        return;
    }

    if (!branch || !name || !cid) {
        showMessage('Please select a Branch, Name, and ensure CID is autofilled.', 'error');
        return;
    }

    if (processButton) processButton.disabled = true;
    showMessage('Generating Aging History... This may take a moment.', 'loading');
    reportContainer.innerHTML = '<p class="text-gray-500 text-center">Aging history table will appear here after generation.</p>';
    agingReportData = {}; // Clear stored data on new processing

    const formData = new FormData();
    formData.append('branch', branch);
    formData.append('cid', cid); // Send CID to backend

    fetch(`${FLASK_API_BASE_URL}/get_aging_history_per_member_loan`, {
        method: 'POST',
        body: formData,
    })
    .then(response => { // Capture response here
        if (!response.ok) {
            // If response is not OK, throw an error to be caught by .catch()
            return response.json().then(errorData => { throw new Error(errorData.message || 'Unknown error'); });
        }
        return response.json();
    })
    .then(result => {
        // result is now the parsed JSON from a successful response
        if (result.data && result.data.data && result.data.data.length > 0) {
            agingReportData.fullResult = result.data; // Store the entire data object
            renderAgingHistoryTable(agingReportData.fullResult); // Pass the entire data object
            showMessage(result.message, 'success');
        } else {
            agingReportData = {}; // Ensure it's empty
            renderAgingHistoryTable({ headers: [], display_headers_mmm: [], full_month_years: [], data: [] }); // Render empty table
            showMessage(result.message || 'No aging history data found for the specified criteria.', 'info');
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
        reportContainer.innerHTML = '';
        agingReportData = {}; // Ensure it's empty on error
    })
    .finally(() => {
        if (processButton) processButton.disabled = false;
        updateOperationsAgingReportUI();
    });
};

/**
 * Updates the state of the "Generate Report" button and search/copy actions for Aging History.
 */
function updateOperationsAgingReportUI() {
    const areaInput = document.getElementById('agingArea'); // Get Area input
    const branchInput = document.getElementById('agingBranch');
    const nameInput = document.getElementById('agingName');
    const cidInput = document.getElementById('agingCid');
    const processButton = document.getElementById('processAgingReportButton');
    const agingReportSearchCopyDiv = document.getElementById('agingReportSearchCopy'); // Get the search/copy container
    const tableExists = document.querySelector('#agingReportTableContainer table');
    const searchInput = document.getElementById('agingSearchInput');
    const copyButton = document.getElementById('copyAgingReportTableButton');

    if (processButton) {
        // Enable button only if a specific branch is selected (not 'ALL' or 'Consolidated')
        // AND Name AND CID are filled.
        processButton.disabled = !(
            areaInput.value.trim() && // Area must be selected
            branchInput.value.trim() && // Branch must be selected
            branchInput.value.trim() !== 'ALL' && // Disable if 'ALL' is selected
            branchInput.value.trim() !== 'Consolidated' && // Disable if 'Consolidated' is selected
            nameInput.value.trim() &&
            cidInput.value.trim() // CID must be autofilled
        );
    }

    // Toggle visibility of the search/copy container
    if (agingReportSearchCopyDiv) {
        if (tableExists) {
            agingReportSearchCopyDiv.classList.remove('hidden');
        } else {
            agingReportSearchCopyDiv.classList.add('hidden');
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
 * Renders the Aging History per Member's Loan table in the UI.
 * @param {Object} data - Object containing 'headers' (unique internal keys), 'display_headers_mmm' (MMM format for display), 'full_month_years' (full month-year strings), and 'data' (row objects).
 */
function renderAgingHistoryTable(data) {
    const tableContainer = document.getElementById('agingReportTableContainer');
    if (!tableContainer) {
        console.error('Aging Report table container not found!');
        return;
    }

    tableContainer.innerHTML = ''; // Clear previous content

    const uniqueInternalHeaders = data.headers || []; // e.g., ['JAN21', 'FEB21'] - used for data access
    const displayHeadersMMM = data.display_headers_mmm || []; // e.g., ['Jan', 'Feb'] - used for display in second row
    const fullMonthYears = data.full_month_years || []; // e.g., ['Jan 2021', 'Feb 2021'] - used for year grouping in first row
    const tableData = data.data || [];
    const overallLatestDate = data.overall_latest_date || ''; // Get the overall latest date

    if (!tableData || tableData.length === 0) {
        tableContainer.innerHTML = '<p class="text-gray-600 text-center">No Aging History data found for the specified criteria.</p>';
        return;
    }

    const table = document.createElement('table');
    table.id = 'agingHistoryTable'; // Added ID for specific CSS targeting
    table.className = 'min-w-full bg-white border border-gray-300 rounded-lg shadow-md';

    const thead = document.createElement('thead');
    const tbody = document.createElement('tbody');

    // First header row: Account (merged), DISBURSED, PRINCIPAL, BALANCE, PRODUCT, and Years
    const headerRow1 = document.createElement('tr');
    
    // ACCOUNT header (sticky)
    const thAccount = document.createElement('th');
    thAccount.className = 'py-3 px-4 bg-gray-100 text-center align-middle text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300 sticky-col';
    thAccount.textContent = 'ACCOUNT';
    thAccount.rowSpan = 2; // Merge across two rows
    headerRow1.appendChild(thAccount);

    // DISBURSED header (sticky)
    const thDisbursed = document.createElement('th');
    thDisbursed.className = 'py-3 px-4 bg-gray-100 text-center align-middle text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300 sticky-col-2'; // New sticky class
    thDisbursed.textContent = 'DISBURSED';
    thDisbursed.rowSpan = 2;
    headerRow1.appendChild(thDisbursed);

    // PRINCIPAL header (sticky)
    const thPrincipal = document.createElement('th');
    thPrincipal.className = 'py-3 px-4 bg-gray-100 text-center align-middle text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300 sticky-col-3'; // New sticky class
    thPrincipal.textContent = 'PRINCIPAL';
    thPrincipal.rowSpan = 2;
    headerRow1.appendChild(thPrincipal);

    // BALANCE header (sticky)
    const thBalance = document.createElement('th');
    thBalance.className = 'py-3 px-4 bg-gray-100 text-center align-middle text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300 sticky-col-4'; // New sticky class
    thBalance.innerHTML = `<div>BALANCE</div><div class="text-xs font-normal text-gray-500 mt-1">${overallLatestDate}</div>`; // Removed "As of"
    thBalance.rowSpan = 2;
    headerRow1.appendChild(thBalance);

    // PRODUCT header (sticky)
    const thProduct = document.createElement('th');
    thProduct.className = 'py-3 px-4 bg-gray-100 text-center align-middle text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300 sticky-col-5'; // New sticky class
    thProduct.textContent = 'PRODUCT';
    thProduct.rowSpan = 2;
    headerRow1.appendChild(thProduct);


    // Group fullMonthYears by year to create year spans for the first header row
    const years = {};
    fullMonthYears.forEach(fullMonthYearStr => {
        const year = fullMonthYearStr.split(' ')[1]; // e.g., "Jan 2021" -> "2021"
        if (!years[year]) {
            years[year] = [];
        }
        years[year].push(fullMonthYearStr);
    });

    for (const year in years) {
        const thYear = document.createElement('th');
        thYear.className = 'py-3 px-4 bg-gray-100 text-center align-middle text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300';
        thYear.colSpan = years[year].length; // Span across months in that year
        thYear.textContent = year;
        headerRow1.appendChild(thYear);
    }
    thead.appendChild(headerRow1);

    // Second header row: Months (three-letter abbreviation)
    const headerRow2 = document.createElement('tr');
    // No need for thAccount, thDisbursed, thPrincipal, thBalance, thProduct here as they are rowSpan'd from the first row.
    // We just add the month headers for the second row.
    // Slice displayHeadersMMM to get only the month parts, skipping DISBURSED, PRINCIPAL, BALANCE, PRODUCT
    displayHeadersMMM.slice(4).forEach(monthMMMHeader => { // Use displayHeadersMMM for text content
        const thMonth = document.createElement('th');
        thMonth.className = 'py-3 px-4 bg-gray-100 text-center align-middle text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300';
        thMonth.textContent = monthMMMHeader; // Display "Jan", "Feb", etc.
        headerRow2.appendChild(thMonth);
    });
    thead.appendChild(headerRow2);
    table.appendChild(thead);

    // Table Body
    tableData.forEach(rowData => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-50';

        // ACCOUNT column (sticky)
        const tdAccount = document.createElement('td');
        tdAccount.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200 font-semibold whitespace-nowrap sticky-col';
        tdAccount.textContent = rowData['ACCOUNT'] || '';
        tr.appendChild(tdAccount);

        // DISBURSED column (sticky)
        const tdDisbursed = document.createElement('td');
        tdDisbursed.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200 whitespace-nowrap sticky-col-2';
        tdDisbursed.textContent = rowData['DISBURSED'] || '';
        tr.appendChild(tdDisbursed);

        // PRINCIPAL column (sticky)
        const tdPrincipal = document.createElement('td');
        tdPrincipal.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200 text-right whitespace-nowrap sticky-col-3';
        tdPrincipal.textContent = rowData['PRINCIPAL'] || '';
        tr.appendChild(tdPrincipal);

        // BALANCE column (sticky)
        const tdBalance = document.createElement('td');
        tdBalance.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200 text-right whitespace-nowrap sticky-col-4';
        tdBalance.textContent = rowData['BALANCE'] || '';
        tr.appendChild(tdBalance);

        // PRODUCT column (sticky)
        const tdProduct = document.createElement('td');
        tdProduct.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200 whitespace-nowrap sticky-col-5';
        tdProduct.textContent = rowData['PRODUCT'] || '';
        tr.appendChild(tdProduct);

        // Iterate over the unique internal headers for monthly aging data
        // Slice uniqueInternalHeaders to get only the month parts, skipping DISBURSED, PRINCIPAL, BALANCE, PRODUCT
        uniqueInternalHeaders.slice(5).forEach(internalHeaderKey => { // Use uniqueInternalHeaders for data access
            const tdAging = document.createElement('td');
            const agingValue = rowData[internalHeaderKey];
            
            tdAging.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200 text-center';
            
            if (agingValue !== null && agingValue !== undefined) {
                tdAging.classList.add(`aging-${agingValue}`);
                tdAging.textContent = agingValue;
            } else {
                tdAging.textContent = '';
            }
            tr.appendChild(tdAging);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    tableContainer.appendChild(table);
}

/**
 * Filters the Aging History table based on search input.
 */
const filterAgingReportTable = function() {
    const searchInput = document.getElementById('agingSearchInput');
    const filter = searchInput.value.toLowerCase();
    
    if (agingReportData.fullResult) { // Check if fullResult exists
        if (filter === '') {
            renderAgingHistoryTable(agingReportData.fullResult); // Render full data if filter is empty
        } else {
            const filteredRows = agingReportData.fullResult.data.filter(row => {
                // Filter based on the 'ACCOUNT' column
                return String(row['ACCOUNT']).toLowerCase().includes(filter);
            });
            // Pass the original headers and full_month_years, but filtered data rows
            renderAgingHistoryTable({ 
                headers: agingReportData.fullResult.headers, 
                display_headers_mmm: agingReportData.fullResult.display_headers_mmm,
                full_month_years: agingReportData.fullResult.full_month_years,
                overall_latest_date: agingReportData.fullResult.overall_latest_date, // Pass the overall_latest_date
                data: filteredRows 
            });
        }
    }
};

/**
 * Copies the content of the Aging History table to the clipboard in TSV format.
 */
const copyAgingReportTable = function() {
    const table = document.querySelector('#agingReportTableContainer table');
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
            // For aging values (0-7), we copy the number directly
            // For other text, clean up commas/parentheses if they exist
            if (cols[j].classList.contains('aging-0') || cols[j].classList.contains('aging-1') ||
                cols[j].classList.contains('aging-2') || cols[j].classList.contains('aging-3') ||
                cols[j].classList.contains('aging-4') || cols[j].classList.contains('aging-5') ||
                cols[j].classList.contains('aging-6') || cols[j].classList.contains('aging-7')) {
                // It's an aging value, copy the number as is
                row.push(text);
            } else if (text.startsWith('(') && text.endsWith(')')) {
                text = '-' + text.substring(1, text.length - 1).replace(/,/g, '');
                row.push(text);
            } else {
                text = text.replace(/,/g, '');
                row.push(text);
            }
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
 * Handles input on the Name field to autofill CID.
 */
function handleAgingNameInput() {
    const nameInput = document.getElementById('agingName');
    const cidInput = document.getElementById('agingCid');
    const selectedName = nameInput.value.trim();

    if (nameCidMap.has(selectedName)) {
        cidInput.value = nameCidMap.get(selectedName);
    } else {
        cidInput.value = '';
    }
    updateOperationsAgingReportUI();
}

/**
 * Updates the state of the "Generate Report" button and search/copy actions for Aging History.
 */
function updateOperationsAgingReportUI() {
    const areaInput = document.getElementById('agingArea'); // Get Area input
    const branchInput = document.getElementById('agingBranch');
    const nameInput = document.getElementById('agingName');
    const cidInput = document.getElementById('agingCid');
    const processButton = document.getElementById('processAgingReportButton');
    const agingReportSearchCopyDiv = document.getElementById('agingReportSearchCopy'); // Get the search/copy container
    const tableExists = document.querySelector('#agingReportTableContainer table');
    const searchInput = document.getElementById('agingSearchInput');
    const copyButton = document.getElementById('copyAgingReportTableButton');

    if (processButton) {
        // Enable button only if a specific branch is selected (not 'ALL' or 'Consolidated')
        // AND Name AND CID are filled.
        processButton.disabled = !(
            areaInput.value.trim() && // Area must be selected
            branchInput.value.trim() && // Branch must be selected
            branchInput.value.trim() !== 'ALL' && // Disable if 'ALL' is selected
            branchInput.value.trim() !== 'Consolidated' && // Disable if 'Consolidated' is selected
            nameInput.value.trim() &&
            cidInput.value.trim() // CID must be autofilled
        );
    }

    // Toggle visibility of the search/copy container
    if (agingReportSearchCopyDiv) {
        if (tableExists) {
            agingReportSearchCopyDiv.classList.remove('hidden');
        } else {
            agingReportSearchCopyDiv.classList.add('hidden');
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
