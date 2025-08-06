// js/tabs/actg_ref.js

(function() { // Start IIFE
    let refReportData = []; // To store the full report data for persistence and filtering

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
        updateActgRefUI(); // Trigger UI update on input change
    }

    /**
     * Renders the Reference Report table in the UI.
     * @param {Array<Object>} dataToDisplay - The array of row objects to display.
     */
    function renderRefReportTable(dataToDisplay) {
        const tableContainer = document.getElementById('actgRefReportContainer');
        if (!tableContainer) {
            console.error('Reference Report table container not found!');
            return;
        }

        tableContainer.innerHTML = ''; // Clear previous content

        if (!dataToDisplay || dataToDisplay.length === 0) {
            tableContainer.innerHTML = '<p class="text-gray-600 text-center">No Reference report data found for the specified criteria.</p>';
            return;
        }

        // Create a wrapper div for the table to enable scrolling and sticky header
        const scrollWrapper = document.createElement('div');
        scrollWrapper.className = 'overflow-y-auto max-h-[60vh] rounded-lg shadow-md border border-gray-300'; // Tailwind classes for scrollable div

        const table = document.createElement('table');
        table.className = 'min-w-full bg-white'; // Removed border/shadow from table itself, moved to wrapper

        const thead = document.createElement('thead');
        // Apply sticky header styles directly to thead
        thead.className = 'sticky top-0 z-10 bg-gray-100'; // Tailwind classes for sticky header

        const headerRow = document.createElement('tr');
        // Updated headers array to include 'GL CODE' and 'GL NAME'
        const headers = ['DATE', 'GL CODE', 'GL NAME', 'TRN', 'DESCRIPTION', 'REF', 'DR', 'CR', 'BALANCE'];

        headers.forEach(headerText => {
            const th = document.createElement('th');
            th.className = 'py-3 px-4 text-center text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300'; // Centered
            if (['DR', 'CR', 'BALANCE'].includes(headerText)) {
                th.classList.add('text-right'); // Right align DR, CR, BALANCE headers
            }
            th.textContent = headerText;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        dataToDisplay.forEach(rowData => {
            const tr = document.createElement('tr');
            tr.className = 'hover:bg-gray-50';

            headers.forEach(headerKey => {
                const td = document.createElement('td');
                td.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200';
                if (['DR', 'CR', 'BALANCE'].includes(headerKey)) {
                    td.classList.add('text-right'); // Right align DR, CR, BALANCE data
                }
                td.textContent = rowData[headerKey] !== undefined ? rowData[headerKey] : '';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);

        scrollWrapper.appendChild(table); // Append table to the scroll wrapper
        tableContainer.appendChild(scrollWrapper); // Append wrapper to the main container
    }

    /**
     * Copies the content of the Reference Report table to the clipboard in TSV format.
     */
    function copyRefReportTable() {
        const table = document.querySelector('#actgRefReportContainer table');
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
                // Handle negative currency format for copying
                if (text.startsWith('(') && text.endsWith(')')) {
                    text = '-' + text.substring(1, text.length - 1).replace(/,/g, '');
                } else {
                    text = text.replace(/,/g, ''); // Remove commas for numeric values
                }
                row.push(text);
            }
            csv.push(row.join('\t'));
        }

        const csvString = csv.join('\n');

        // Use a temporary textarea for copying to clipboard
        const textarea = document.createElement('textarea');
        textarea.value = csvString;
        textarea.style.position = 'fixed'; // Keep it off-screen
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
     * Filters the Reference Report table based on search input.
     */
    function filterRefReportTable() {
        const searchInput = document.getElementById('actgRefSearchInput');
        const filter = searchInput.value.toLowerCase();
        
        if (filter === '') {
            renderRefReportTable(refReportData); // Use the full data
        } else if (refReportData.length > 0) {
            const filteredData = refReportData.filter(row => {
                // Check if any value in the row contains the filter string
                return Object.values(row).some(value => {
                    return String(value).toLowerCase().includes(filter);
                });
            });
            renderRefReportTable(filteredData);
        }
    }

    /**
     * Updates the state of the "Generate Report" button and actions bar.
     */
    function updateActgRefUI() {
        const branchInput = document.getElementById('actgRefBranch');
        const fromDateInput = document.getElementById('actgRefFromDate');
        const toDateInput = document.getElementById('actgRefToDate');
        const refInput = document.getElementById('actgRefInput');
        const matchTypeInput = document.getElementById('actgRefMatchType');
        const processButton = document.getElementById('processActgRefButton');
        const reportActions = document.getElementById('actgRefReportActions');
        const tableExists = document.querySelector('#actgRefReportContainer table'); // Check for the actual table
        const searchInput = document.getElementById('actgRefSearchInput');
        const copyButton = document.getElementById('copyActgRefTableButton');

        if (processButton) {
            processButton.disabled = !(
                branchInput.value.trim() &&
                isValidDate(fromDateInput.value.trim()) &&
                isValidDate(toDateInput.value.trim()) &&
                refInput.value.trim() && // Reference input is mandatory
                matchTypeInput.value.trim()
            );
        }

        // Show/hide report actions bar based on whether a table is displayed
        if (reportActions) {
            if (tableExists) {
                reportActions.classList.remove('hidden');
            } else {
                reportActions.classList.add('hidden');
            }
        }
        
        // Enable/disable search and copy buttons based on table existence
        if (searchInput) {
            searchInput.disabled = !tableExists;
            if (!tableExists) searchInput.value = ''; // Clear search if no table
        }
        if (copyButton) {
            copyButton.disabled = !tableExists;
        }
    }

    /**
     * Handles the processing request for Accounting Reference data.
     */
    async function processRefReport() {
        const branchInput = document.getElementById('actgRefBranch');
        const fromDateInput = document.getElementById('actgRefFromDate');
        const toDateInput = document.getElementById('actgRefToDate');
        const refInput = document.getElementById('actgRefInput');
        const matchTypeInput = document.getElementById('actgRefMatchType');
        const processButton = document.getElementById('processActgRefButton');
        const reportContainer = document.getElementById('actgRefReportContainer');
        const reportActions = document.getElementById('actgRefReportActions');
        const searchInput = document.getElementById('actgRefSearchInput');
        const copyButton = document.getElementById('copyActgRefTableButton');

        const branch = branchInput.value.trim();
        const fromDate = fromDateInput.value.trim();
        const toDate = toDateInput.value.trim();
        const referenceLookup = refInput.value.trim();
        const matchType = matchTypeInput.value.trim();

        // Basic input validation
        if (!branch || !isValidDate(fromDate) || !isValidDate(toDate) || !referenceLookup || !matchType) {
            showMessage('Please fill all required fields and ensure dates are in MM/DD/YYYY format.', 'error');
            return;
        }

        // Disable UI elements during processing to prevent multiple submissions
        if (processButton) processButton.disabled = true;
        if (searchInput) { searchInput.disabled = true; searchInput.value = ''; }
        if (copyButton) copyButton.disabled = true;
        if (reportActions) reportActions.classList.add('hidden'); // Hide actions during processing

        showMessage('Generating Reference report... This may take a moment.', 'loading');
        reportContainer.innerHTML = ''; // Clear previous report content
        refReportData = []; // Clear stored data on new processing request

        // Prepare form data for the backend API call
        const formData = new FormData();
        formData.append('branch', branch);
        formData.append('from_date', fromDate);
        formData.append('to_date', toDate);
        formData.append('reference_lookup', referenceLookup);
        formData.append('match_type', matchType);

        try {
            // Make the API call to the Flask backend
            const response = await fetch(`${FLASK_API_BASE_URL}/process_accounting_ref`, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json(); // Parse the JSON response

            if (response.ok) { // Check if the HTTP status is 200-299
                if (result.data && result.data.length > 0) {
                    refReportData = result.data; // Store the full data for filtering/copying
                    renderRefReportTable(refReportData); // Render the table with fetched data
                    showMessage(result.message, 'success');
                } else {
                    refReportData = []; // No data, clear stored data
                    renderRefReportTable([]); // Render empty table or message
                    showMessage(result.message || 'No data found for the specified criteria.', 'info');
                }
            } else {
                // Handle API errors (e.g., 400, 500 status codes)
                showMessage(`Error: ${result.message}`, 'error');
                reportContainer.innerHTML = ''; // Clear report on error
                refReportData = []; // Clear stored data on error
            }
        } catch (error) {
            // Handle network errors (e.g., server unreachable)
            console.error('Fetch error:', error);
            showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
            reportContainer.innerHTML = ''; // Clear report on network error
            refReportData = []; // Clear stored data on network error
        } finally {
            // Re-enable the process button and update UI elements regardless of success or failure
            if (processButton) processButton.disabled = false;
            updateActgRefUI(); // This will show/hide actions and enable/disable buttons/search appropriately
        }
    }

    /**
     * Initializes the Reference sub-tab: attaches event listeners and performs initial UI update.
     * This function is called by main.js when the sub-tab is activated.
     */
    function initActgRefTab() {
        console.log('Initializing Reference Tab...');

        const branchInput = document.getElementById('actgRefBranch');
        const fromDateInput = document.getElementById('actgRefFromDate');
        const toDateInput = document.getElementById('actgRefToDate');
        const refInput = document.getElementById('actgRefInput');
        const matchTypeInput = document.getElementById('actgRefMatchType');
        const processButton = document.getElementById('processActgRefButton');
        const reportContainer = document.getElementById('actgRefReportContainer');
        const searchInput = document.getElementById('actgRefSearchInput');
        const copyButton = document.getElementById('copyActgRefTableButton');
        const reportActions = document.getElementById('actgRefReportActions');

        // Clear report container on tab initialization IF there's no data to persist
        // Also ensure input fields retain their values if data persists from previous session
        if (reportContainer) {
            if (refReportData.length === 0) {
                reportContainer.innerHTML = '<p class="text-gray-500 text-center">Reference report will appear here after generation.</p>';
            } else {
                renderRefReportTable(refReportData); // Re-render if data already exists
            }

            const lastBranch = localStorage.getItem('lastRefBranch');
            const lastFromDate = localStorage.getItem('lastRefFromDate');
            const lastToDate = localStorage.getItem('lastRefToDate');
            const lastRefInput = localStorage.getItem('lastRefInput');
            const lastRefMatchType = localStorage.getItem('lastRefMatchType');

            if (lastBranch) branchInput.value = lastBranch;
            if (lastFromDate) fromDateInput.value = lastFromDate;
            if (lastToDate) toDateInput.value = lastToDate;
            if (lastRefInput) refInput.value = lastRefInput;
            if (lastRefMatchType) matchTypeInput.value = lastRefMatchType;
        }


        // Attach event listeners (ensure they are attached only once using dataset attribute)
        if (branchInput && !branchInput.dataset.listenerAttached) {
            branchInput.addEventListener('change', () => {
                updateActgRefUI();
                localStorage.setItem('lastRefBranch', branchInput.value.trim());
            });
            branchInput.dataset.listenerAttached = 'true';
        }
        if (fromDateInput && !fromDateInput.dataset.listenerAttached) {
            fromDateInput.addEventListener('input', (event) => {
                formatDateInput(event);
                updateActgRefUI();
                localStorage.setItem('lastRefFromDate', fromDateInput.value.trim());
            });
            fromDateInput.dataset.listenerAttached = 'true';
        }
        if (toDateInput && !toDateInput.dataset.listenerAttached) {
            toDateInput.addEventListener('input', (event) => {
                formatDateInput(event);
                updateActgRefUI();
                localStorage.setItem('lastRefToDate', toDateInput.value.trim());
            });
            toDateInput.dataset.listenerAttached = 'true';
        }
        if (refInput && !refInput.dataset.listenerAttached) {
            refInput.addEventListener('input', () => {
                updateActgRefUI();
                localStorage.setItem('lastRefInput', refInput.value.trim());
            });
            refInput.dataset.listenerAttached = 'true';
        }
        if (matchTypeInput && !matchTypeInput.dataset.listenerAttached) {
            matchTypeInput.addEventListener('change', () => {
                updateActgRefUI();
                localStorage.setItem('lastRefMatchType', matchTypeInput.value.trim());
            });
            matchTypeInput.dataset.listenerAttached = 'true';
        }
        if (processButton && !processButton.dataset.listenerAttached) {
            processButton.addEventListener('click', processRefReport);
            processButton.dataset.listenerAttached = 'true';
        }
        if (searchInput && !searchInput.dataset.listenerAttached) {
            searchInput.addEventListener('input', filterRefReportTable);
            searchInput.dataset.listenerAttached = 'true';
        }
        if (copyButton && !copyButton.dataset.listenerAttached) {
            copyButton.addEventListener('click', copyRefReportTable);
            copyButton.dataset.listenerAttached = 'true';
        }

        // Initial UI update based on current state of inputs and data
        updateActgRefUI();
    }

    // Register this sub-tab's initializer with the main application logic
    // This allows main.js to call initActgRefTab when the tab is activated
    registerTabInitializer('actgRef', initActgRefTab);
})(); // End IIFE
