// js/tabs/operations_statement_of_account.js

(function() { // Start IIFE
    // Guard to prevent multiple executions of this IIFE unnecessarily
    if (window.operationsStatementOfAccountTabInitialized) {
        return;
    }
    window.operationsStatementOfAccountTabInitialized = true;

    // Variable to store the full SOA report data for filtering and persistence
    let soaReportData = [];

    // NEW: Sorting state for SOA table
    let soaCurrentSortKey = 'TRNDATE'; // Default sort key
    let soaCurrentSortDirection = 'asc'; // Default sort direction


    /**
     * Helper function to parse formatted currency to a number for sorting.
     * Handles commas and parentheses for negative numbers.
     * @param {string} value - The formatted currency string.
     * @returns {number} The numeric value.
     */
    function parseFormattedCurrency(value) {
        if (typeof value !== 'string') {
            return parseFloat(value) || 0;
        }
        let cleanValue = value.replace(/,/g, '');
        if (cleanValue.startsWith('(') && cleanValue.endsWith(')')) {
            return -parseFloat(cleanValue.substring(1, cleanValue.length - 1)) || 0;
        }
        return parseFloat(cleanValue) || 0;
    }

    /**
     * Validates a date string in MM/DD/YYYY format.
     * @param {string} dateString - The date string to validate.
     * @returns {boolean} True if the date is valid and in the correct format, false otherwise.
     */
    function isValidDate(dateString) {
        if (!/^\d{2}\/\d{2}\/\d{4}$/.test(dateString)) return false;
        const [month, day, year] = dateString.split('/').map(Number);
        const date = new Date(year, month - 1, day);
        return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day;
    }

    /**
     * Formats date input field to MM/DD/YYYY as user types.
     * Automatically adds slashes and restricts input to numbers.
     * @param {Event} event - The input event.
     */
    function formatDateInput(event) {
        let input = event.target;
        let value = input.value.replace(/\D/g, ''); // Remove all non-digit characters

        if (value.length > 8) { // MM/DD/YYYY
            value = value.substring(0, 8);
        }

        if (value.length > 4) {
            value = value.substring(0, 2) + '/' + value.substring(2, 4) + '/' + value.substring(4, 8);
        } else if (value.length > 2) {
            value = value.substring(0, 2) + '/' + value.substring(2, 4);
        }

        input.value = value;
        updateSoaUI(); // Trigger UI update on input change
    }


    /**
     * Renders the SOA Report table in the UI.
     * @param {Array<Object>} dataToDisplay - The array of row objects to display.
     */
    function renderSoaReportTable(dataToDisplay) {
        const tableContainer = document.getElementById('soaReportTableContainer');
        if (!tableContainer) {
            console.error('SOA Report table container not found!');
            return;
        }

        tableContainer.innerHTML = ''; // Clear previous content

        if (!dataToDisplay || dataToDisplay.length === 0) {
            tableContainer.innerHTML = '<p class="text-gray-600 text-center">No Statement of Account report data found for the specified criteria.</p>';
            return;
        }

        const table = document.createElement('table');
        table.className = 'min-w-full bg-white border border-gray-300 rounded-lg shadow-md';

        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        // Define headers with sorting capabilities
        const headers = [
            { key: 'TRN', label: 'TRN', align: 'left', sortable: true },
            { key: 'ACC', label: 'ACC', align: 'left', sortable: true },
            { key: 'TRNTYPE', label: 'TRNTYPE', align: 'center', sortable: true },
            { key: 'TLR', label: 'TLR', align: 'center', sortable: true },
            { key: 'LEVEL', label: 'LEVEL', align: 'center', sortable: true },
            { key: 'TRNDATE', label: 'TRNDATE', align: 'center', sortable: true },
            { key: 'TRNAMT', label: 'TRNAMT', align: 'right', sortable: true },
            { key: 'TRNNONC', label: 'TRNNONC', align: 'right', sortable: true },
            { key: 'TRNINT', label: 'TRNINT', align: 'right', sortable: true },
            { key: 'TRNTAXPEN', label: 'TRNTAXPEN', align: 'right', sortable: true },
            { key: 'BAL', label: 'BAL', align: 'right', sortable: true },
            { key: 'SEQ', label: 'SEQ', align: 'center', sortable: true },
            { key: 'TRNDESC', label: 'TRNDESC', align: 'left', sortable: true }
        ];

        headers.forEach(headerInfo => {
            const th = document.createElement('th');
            th.className = `py-3 px-4 bg-gray-100 text-${headerInfo.align} text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300`;
            
            // NEW: Assign unique IDs to headers for CSS targeting
            th.id = `soa${headerInfo.key}Header`;

            th.textContent = headerInfo.label;

            if (headerInfo.sortable) {
                th.classList.add('cursor-pointer', 'hover:bg-gray-200');
                th.setAttribute('data-sort-key', headerInfo.key);

                // Add sort icon
                const sortIcon = document.createElement('i');
                sortIcon.className = 'fas ml-2';
                if (soaCurrentSortKey === headerInfo.key) {
                    sortIcon.classList.add(soaCurrentSortDirection === 'asc' ? 'fa-sort-up' : 'fa-sort-down');
                } else {
                    sortIcon.classList.add('fa-sort'); // Neutral sort icon
                }
                th.appendChild(sortIcon);

                // Add event listener for sorting
                th.addEventListener('click', () => {
                    const clickedKey = headerInfo.key;
                    let newDirection = 'asc';
                    if (soaCurrentSortKey === clickedKey && soaCurrentSortDirection === 'asc') {
                        newDirection = 'desc';
                    }
                    sortSoaTable(clickedKey, newDirection);
                });
            }
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        let previousAcc = null;
        let currentColorClass = 'bg-blue-50'; // Start with blue for the first group

        dataToDisplay.forEach((rowData, rowIndex) => {
            const tr = document.createElement('tr');
            
            const currentAcc = rowData['ACC'];

            if (currentAcc !== previousAcc) {
                // If ACC changes, switch color
                currentColorClass = (currentColorClass === 'bg-blue-50') ? 'bg-yellow-50' : 'bg-blue-50';
                previousAcc = currentAcc;
            }
            // Apply current color class to the row, and retain hover effect
            tr.className = `${currentColorClass} hover:bg-gray-100`;


            headers.forEach(headerInfo => {
                const td = document.createElement('td');
                td.className = `py-2 px-4 text-sm text-gray-800 border-b border-gray-200 text-${headerInfo.align}`;
                
                td.textContent = rowData[headerInfo.key] !== undefined ? rowData[headerInfo.key] : '';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);

        tableContainer.appendChild(table);
    }

    /**
     * Sorts the SOA report data and re-renders the table.
     * @param {string} sortKey - The key (column) to sort by.
     * @param {string} sortDirection - 'asc' or 'desc'.
     */
    function sortSoaTable(sortKey, sortDirection) {
        soaCurrentSortKey = sortKey;
        soaCurrentSortDirection = sortDirection;

        const sortedData = [...soaReportData].sort((a, b) => {
            let valA = a[sortKey];
            let valB = b[sortKey];

            // Handle numeric/currency columns
            if (['TRNAMT', 'TRNNONC', 'TRNINT', 'TRNTAXPEN', 'BAL'].includes(sortKey)) {
                valA = parseFormattedCurrency(valA);
                valB = parseFormattedCurrency(valB);
            } else if (['TRNDATE'].includes(sortKey)) {
                // Parse date strings to Date objects for proper comparison
                valA = new Date(valA);
                valB = new Date(valB);
            } else if (['TLR', 'LEVEL', 'SEQ'].includes(sortKey)) {
                // Convert to number for proper numeric sort
                valA = parseFloat(valA) || 0;
                valB = parseFloat(valB) || 0;
            } else {
                // Default to string comparison for other columns (case-insensitive)
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

        renderSoaReportTable(sortedData);
    }

    /**
     * Copies the content of the SOA Report table to the clipboard in TSV format.
     */
    function copySoaReportTable() {
        const table = document.querySelector('#soaReportTableContainer table');
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
                // When copying, ensure negative numbers are represented with a minus sign, not parentheses.
                // Remove commas for raw number pasting.
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
     * Filters the SOA Report table based on search input.
     */
    function filterSoaReportTable() {
        const searchInput = document.getElementById('soaSearchInput');
        const filter = searchInput.value.toLowerCase();
        
        if (filter === '') {
            renderSoaReportTable(soaReportData); // Use the full data
        } else if (soaReportData.length > 0) {
            const filteredData = soaReportData.filter(row => {
                return Object.values(row).some(value => {
                    return String(value).toLowerCase().includes(filter);
                });
            });
            renderSoaReportTable(filteredData);
        }
    }

    /**
     * Updates the state of the "Generate Report" button and actions bar.
     */
    function updateSoaUI() {
        const branchInput = document.getElementById('soaBranch');
        const fromDateInput = document.getElementById('soaFromDate');
        const toDateInput = document.getElementById('soaToDate');
        const accountInput = document.getElementById('soaAccount');
        const codeInput = document.getElementById('soaCode');
        const descriptionInput = document.getElementById('soaDescription');
        const trnTypeInput = document.getElementById('soaTrnType');
        const matchTypeInput = document.getElementById('soaMatchType');
        const processButton = document.getElementById('processSoaButton');
        const reportActions = document.getElementById('soaReportActions');
        const tableExists = document.querySelector('#soaReportTableContainer table');
        const searchInput = document.getElementById('soaSearchInput');
        const copyButton = document.getElementById('copySoaTableButton');

        // --- DEBUG TRACE: Check individual validation conditions ---
        const isBranchSelected = branchInput.value.trim() !== '';
        const isValidFromDate = isValidDate(fromDateInput.value.trim());
        const isValidToDate = isValidDate(toDateInput.value.trim());
        const isAnyLookupFilled = accountInput.value.trim() !== '' ||
                                 codeInput.value.trim() !== '' ||
                                 descriptionInput.value.trim() !== '' ||
                                 trnTypeInput.value.trim() !== '';
        const isAccountOrDescFilled = accountInput.value.trim() !== '' || descriptionInput.value.trim() !== '';
        const isMatchTypeSelected = matchTypeInput.value.trim() !== ''; // Check if match type is selected

        console.log('--- updateSoaUI Debug Trace ---');
        console.log('isBranchSelected:', isBranchSelected, ' (Value:', branchInput.value.trim(), ')');
        console.log('isValidFromDate:', isValidFromDate, ' (Value:', fromDateInput.value.trim(), ')');
        console.log('isValidToDate:', isValidToDate, ' (Value:', toDateInput.value.trim(), ')');
        console.log('isAnyLookupFilled:', isAnyLookupFilled, ' (Account:', accountInput.value.trim(), ' Code:', codeInput.value.trim(), ' Desc:', descriptionInput.value.trim(), ' TRN Type:', trnTypeInput.value.trim(), ')');
        console.log('isAccountOrDescFilled:', isAccountOrDescFilled);
        console.log('isMatchTypeSelected (if Account/Desc filled):', isMatchTypeSelected, ' (Value:', matchTypeInput.value.trim(), ')');
        // --- END DEBUG TRACE ---


        if (processButton) {
            processButton.disabled = !(
                isBranchSelected &&
                isValidFromDate &&
                isValidToDate &&
                isAnyLookupFilled &&
                (!isAccountOrDescFilled || isMatchTypeSelected) // Match Type required IF Account or Description is filled
            );
            console.log('Process Button Disabled State:', processButton.disabled);
        }

        if (reportActions) {
            if (tableExists) {
                reportActions.classList.remove('hidden');
            } else {
                reportActions.classList.add('hidden');
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
     * Handles the processing request for Statement of Account data.
     */
    async function processSoaReport() {
        const branchInput = document.getElementById('soaBranch');
        const fromDateInput = document.getElementById('soaFromDate');
        const toDateInput = document.getElementById('soaToDate');
        const accountInput = document.getElementById('soaAccount');
        const codeInput = document.getElementById('soaCode');
        const descriptionInput = document.getElementById('soaDescription');
        const trnTypeInput = document.getElementById('soaTrnType');
        const matchTypeInput = document.getElementById('soaMatchType');
        const processButton = document.getElementById('processSoaButton');
        const reportContainer = document.getElementById('soaReportTableContainer');
        const reportActions = document.getElementById('soaReportActions');
        const searchInput = document.getElementById('soaSearchInput');
        const copyButton = document.getElementById('copySoaTableButton');

        const branch = branchInput.value.trim();
        const fromDate = fromDateInput.value.trim();
        const toDate = toDateInput.value.trim();
        const accountLookup = accountInput.value.trim();
        const codeLookup = codeInput.value.trim();
        const descriptionLookup = descriptionInput.value.trim();
        const trnTypeLookup = trnTypeInput.value.trim();
        const matchType = matchTypeInput.value.trim();

        const isAnyLookupFilled = accountLookup !== '' ||
                                  codeLookup !== '' ||
                                  descriptionLookup !== '' ||
                                  trnTypeLookup !== '';
        const isAccountOrDescFilled = accountLookup !== '' || descriptionLookup !== '';

        // --- DEBUG TRACE: Check validation conditions before sending request ---
        console.log('--- processSoaReport Validation Debug Trace ---');
        console.log('Branch:', branch, ' (Valid:', !!branch, ')');
        console.log('From Date:', fromDate, ' (Valid:', isValidDate(fromDate), ')');
        console.log('To Date:', toDate, ' (Valid:', isValidDate(toDate), ')');
        console.log('Any Lookup Filled:', isAnyLookupFilled);
        console.log('Account or Desc Filled:', isAccountOrDescFilled);
        console.log('Match Type Selected (if Account/Desc filled):', matchType, ' (Valid:', (!isAccountOrDescFilled || matchType !== ''), ')');
        // --- END DEBUG TRACE ---

        // FIX: Updated the error message to reflect current required fields
        if (!branch || !isValidDate(fromDate) || !isValidDate(toDate) || !isAnyLookupFilled ||
            (isAccountOrDescFilled && !matchType)) {
            showMessage('Please fill all required fields (Branch, From Date, To Date) and at least one lookup field (Account Number, Code, Description, or TRN Type). If Account Number or Description is used, Match Type must be selected. Ensure dates are in MM/DD/YYYY format.', 'error');
            return;
        }

        // Disable UI elements during processing
        if (processButton) processButton.disabled = true;
        if (searchInput) { searchInput.disabled = true; searchInput.value = ''; }
        if (copyButton) copyButton.disabled = true;
        if (reportActions) reportActions.classList.add('hidden');

        showMessage('Generating Statement of Account report... This may take a moment.', 'loading');
        reportContainer.innerHTML = ''; // Clear previous report
        soaReportData = []; // Clear stored data on new processing

        const formData = new FormData();
        formData.append('branch', branch);
        formData.append('from_date', fromDate);
        formData.append('to_date', toDate);
        formData.append('account_lookup', accountLookup);
        formData.append('code_lookup', codeLookup);
        formData.append('description_lookup', descriptionLookup);
        formData.append('trn_type_lookup', trnTypeLookup);
        formData.append('match_type', matchType);

        try {
            const response = await fetch(`${FLASK_API_BASE_URL}/process_statement_of_account`, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                if (result.data && result.data.length > 0) {
                    soaReportData = result.data; // Store the full data
                    // NEW: Apply initial sort after fetching data
                    sortSoaTable(soaCurrentSortKey, soaCurrentSortDirection); // Render with initial sort
                    showMessage(result.message, 'success');
                } else {
                    soaReportData = [];
                    renderSoaReportTable([]);
                    showMessage(result.message || 'No data found for the specified criteria.', 'info');
                }
            } else {
                showMessage(`Error: ${result.message}`, 'error');
                reportContainer.innerHTML = '';
                soaReportData = [];
            }
        } catch (error) {
            console.error('Fetch error:', error);
            showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
            reportContainer.innerHTML = '';
            soaReportData = [];
        } finally {
            if (processButton) processButton.disabled = false;
            updateSoaUI(); // This will show/hide actions and enable/disable buttons/search
        }
    }


    /**
     * Initializes the Statement of Account sub-tab: attaches event listeners and performs initial UI update.
     * This function is called by main.js when the sub-tab is activated.
     */
    function initOperationsStatementOfAccountTab() {
        console.log('Initializing Statement of Account Tab.');

        const branchInput = document.getElementById('soaBranch');
        const fromDateInput = document.getElementById('soaFromDate');
        const toDateInput = document.getElementById('soaToDate');
        const accountInput = document.getElementById('soaAccount');
        const codeInput = document.getElementById('soaCode');
        const descriptionInput = document.getElementById('soaDescription');
        const trnTypeInput = document.getElementById('soaTrnType');
        const matchTypeInput = document.getElementById('soaMatchType');
        const processButton = document.getElementById('processSoaButton');
        const reportContainer = document.getElementById('soaReportTableContainer');
        const searchInput = document.getElementById('soaSearchInput');
        const copyButton = document.getElementById('copySoaTableButton');

        // Clear report container on tab initialization IF there's no data to persist
        if (reportContainer && soaReportData.length === 0) {
            reportContainer.innerHTML = '<p class="text-gray-500 text-center">Statement of Account report will appear here after generation.</p>';
        }

        // If soaReportData already has data, re-render it instead of clearing
        if (soaReportData.length > 0) {
            renderSoaReportTable(soaReportData);
            // Also ensure input fields retain their values if data persists
            const lastBranch = localStorage.getItem('lastSoaBranch');
            const lastFromDate = localStorage.getItem('lastSoaFromDate');
            const lastToDate = localStorage.getItem('lastSoaToDate');
            const lastAccount = localStorage.getItem('lastSoaAccount');
            const lastCode = localStorage.getItem('lastSoaCode');
            const lastDescription = localStorage.getItem('lastSoaDescription');
            const lastTrnType = localStorage.getItem('lastSoaTrnType');
            const lastMatchType = localStorage.getItem('lastSoaMatchType');

            if (lastBranch) branchInput.value = lastBranch;
            if (lastFromDate) fromDateInput.value = lastFromDate;
            if (lastToDate) toDateInput.value = lastToDate;
            if (lastAccount) accountInput.value = lastAccount;
            if (lastCode) codeInput.value = lastCode;
            if (lastDescription) descriptionInput.value = lastDescription;
            if (lastTrnType) trnTypeInput.value = lastTrnType;
            if (lastMatchType) matchTypeInput.value = lastMatchType;
            
            updateSoaUI(); // Update UI after values are set
        } else {
            // Clear stored data if no data to persist
            soaReportData = [];
            // Clear local storage if no data to persist
            localStorage.removeItem('lastSoaBranch');
            localStorage.removeItem('lastSoaFromDate');
            localStorage.removeItem('lastSoaToDate');
            localStorage.removeItem('lastSoaAccount');
            localStorage.removeItem('lastSoaCode');
            localStorage.removeItem('lastSoaDescription');
            localStorage.removeItem('lastSoaTrnType');
            localStorage.removeItem('lastSoaMatchType');
        }

        // Attach event listeners (ensure they are attached only once)
        if (branchInput && !branchInput.dataset.listenerAttached) {
            branchInput.addEventListener('change', () => {
                updateSoaUI();
                localStorage.setItem('lastSoaBranch', branchInput.value.trim());
            });
            branchInput.dataset.listenerAttached = 'true';
        }
        if (fromDateInput && !fromDateInput.dataset.listenerAttached) {
            fromDateInput.addEventListener('input', (event) => {
                formatDateInput(event);
                updateSoaUI();
                localStorage.setItem('lastSoaFromDate', fromDateInput.value.trim());
            });
            fromDateInput.dataset.listenerAttached = 'true';
        }
        if (toDateInput && !toDateInput.dataset.listenerAttached) {
            toDateInput.addEventListener('input', (event) => {
                formatDateInput(event);
                updateSoaUI();
                localStorage.setItem('lastSoaToDate', toDateInput.value.trim());
            });
            toDateInput.dataset.listenerAttached = 'true';
        }
        if (accountInput && !accountInput.dataset.listenerAttached) {
            accountInput.addEventListener('input', () => {
                updateSoaUI();
                localStorage.setItem('lastSoaAccount', accountInput.value.trim());
            });
            accountInput.dataset.listenerAttached = 'true';
        }
        if (codeInput && !codeInput.dataset.listenerAttached) {
            codeInput.addEventListener('input', () => {
                updateSoaUI();
                localStorage.setItem('lastSoaCode', codeInput.value.trim());
            });
            codeInput.dataset.listenerAttached = 'true';
        }
        if (descriptionInput && !descriptionInput.dataset.listenerAttached) {
            descriptionInput.addEventListener('input', () => {
                updateSoaUI();
                localStorage.setItem('lastSoaDescription', descriptionInput.value.trim());
            });
            descriptionInput.dataset.listenerAttached = 'true';
        }
        if (trnTypeInput && !trnTypeInput.dataset.listenerAttached) {
            trnTypeInput.addEventListener('input', () => {
                updateSoaUI();
                localStorage.setItem('lastSoaTrnType', trnTypeInput.value.trim());
            });
            trnTypeInput.dataset.listenerAttached = 'true';
        }
        // NEW: Match Type input listener
        if (matchTypeInput && !matchTypeInput.dataset.listenerAttached) {
            matchTypeInput.addEventListener('change', () => {
                updateSoaUI();
                localStorage.setItem('lastSoaMatchType', matchTypeInput.value.trim());
            });
            matchTypeInput.dataset.listenerAttached = 'true';
        }
        if (processButton && !processButton.dataset.listenerAttached) {
            processButton.addEventListener('click', processSoaReport);
            processButton.dataset.listenerAttached = 'true';
        }
        if (searchInput && !searchInput.dataset.listenerAttached) {
            searchInput.addEventListener('input', filterSoaReportTable);
            searchInput.dataset.listenerAttached = 'true';
        }
        if (copyButton && !copyButton.dataset.listenerAttached) {
            copyButton.addEventListener('click', copySoaReportTable);
            copyButton.dataset.listenerAttached = 'true';
        }

        // Initial UI update
        updateSoaUI();
    }

    // Register this sub-tab's initializer with the main application logic
    registerTabInitializer('operationsStatementOfAccount', initOperationsStatementOfAccountTab);

})(); // End IIFE
