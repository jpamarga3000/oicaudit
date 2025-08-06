// js/tabs/actg_desc.js

(function() { // Start IIFE
    let descReportData = []; // To store the full report data for persistence and filtering

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
        updateActgDescUI(); // Trigger UI update on input change
    }

    /**
     * Renders the Description Report table in the UI.
     * @param {Array<Object>} dataToDisplay - The array of row objects to display.
     */
    function renderDescReportTable(dataToDisplay) {
        const tableContainer = document.getElementById('actgDescReportContainer');
        if (!tableContainer) {
            console.error('Description Report table container not found!');
            return;
        }

        tableContainer.innerHTML = ''; // Clear previous content

        if (!dataToDisplay || dataToDisplay.length === 0) {
            tableContainer.innerHTML = '<p class="text-gray-600 text-center">No Description report data found for the specified criteria.</p>';
            return;
        }

        // Add overflow-y-auto and a max-height to the container for scrolling
        tableContainer.style.maxHeight = '500px'; // Adjust as needed
        tableContainer.style.overflowY = 'auto';
        tableContainer.style.position = 'relative'; // Needed for sticky positioning context

        const table = document.createElement('table');
        table.className = 'min-w-full bg-white border border-gray-300 rounded-lg shadow-md';

        const thead = document.createElement('thead');
        // Apply sticky positioning to the thead
        thead.style.position = 'sticky';
        thead.style.top = '0'; // Stick to the top of its scrolling container
        thead.style.zIndex = '10'; // Ensure it stays above other content
        thead.style.backgroundColor = '#f3f4f6'; // Ensure background is visible when sticky

        const headerRow = document.createElement('tr');
        const headers = ['DATE', 'GL CODE', 'GL NAME', 'TRN', 'DESCRIPTION', 'REF', 'DR', 'CR', 'BALANCE'];

        headers.forEach(headerText => {
            const th = document.createElement('th');
            th.className = 'py-3 px-4 bg-gray-100 text-center text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300'; // Centered
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

        tableContainer.appendChild(table);
    }

    /**
     * Copies the content of the Description Report table to the clipboard in TSV format.
     */
    function copyDescReportTable() {
        const table = document.querySelector('#actgDescReportContainer table');
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
     * Filters the Description Report table based on search input.
     */
    function filterDescReportTable() {
        const searchInput = document.getElementById('actgDescSearchInput');
        const filter = searchInput.value.toLowerCase();
        
        if (filter === '') {
            renderDescReportTable(descReportData); // Use the full data
        } else if (descReportData.length > 0) {
            const filteredData = descReportData.filter(row => {
                return Object.values(row).some(value => {
                    return String(value).toLowerCase().includes(filter);
                });
            });
            renderDescReportTable(filteredData);
        }
    }

    /**
     * Updates the state of the "Generate Report" button and actions bar.
     */
    function updateActgDescUI() {
        const branchInput = document.getElementById('actgDescBranch');
        const fromDateInput = document.getElementById('actgDescFromDate');
        const toDateInput = document.getElementById('actgDescToDate');
        const descInput = document.getElementById('actgDescInput');
        const matchTypeInput = document.getElementById('actgDescMatchType');
        const processButton = document.getElementById('processActgDescButton');
        const reportActions = document.getElementById('actgDescReportActions');
        const tableExists = document.querySelector('#actgDescReportContainer table');
        const searchInput = document.getElementById('actgDescSearchInput');
        const copyButton = document.getElementById('copyActgDescTableButton');

        if (processButton) {
            processButton.disabled = !(
                branchInput.value.trim() &&
                isValidDate(fromDateInput.value.trim()) &&
                isValidDate(toDateInput.value.trim()) &&
                descInput.value.trim() && // Description input is mandatory
                matchTypeInput.value.trim()
            );
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
     * Handles the processing request for Accounting Description data.
     */
    async function processDescReport() {
        const branchInput = document.getElementById('actgDescBranch');
        const fromDateInput = document.getElementById('actgDescFromDate');
        const toDateInput = document.getElementById('actgDescToDate');
        const descInput = document.getElementById('actgDescInput');
        const matchTypeInput = document.getElementById('actgDescMatchType');
        const processButton = document.getElementById('processActgDescButton');
        const reportContainer = document.getElementById('actgDescReportContainer');
        const reportActions = document.getElementById('actgDescReportActions');
        const searchInput = document.getElementById('actgDescSearchInput');
        const copyButton = document.getElementById('copyActgDescTableButton');

        const branch = branchInput.value.trim();
        const fromDate = fromDateInput.value.trim();
        const toDate = toDateInput.value.trim();
        const descriptionLookup = descInput.value.trim();
        const matchType = matchTypeInput.value.trim();

        if (!branch || !isValidDate(fromDate) || !isValidDate(toDate) || !descriptionLookup || !matchType) {
            showMessage('Please fill all required fields and ensure dates are in MM/DD/YYYY format.', 'error');
            return;
        }

        // Disable UI elements during processing
        if (processButton) processButton.disabled = true;
        if (searchInput) { searchInput.disabled = true; searchInput.value = ''; }
        if (copyButton) copyButton.disabled = true;
        if (reportActions) reportActions.classList.add('hidden');

        showMessage('Generating Description report... This may take a moment.', 'loading');
        reportContainer.innerHTML = ''; // Clear previous report
        descReportData = []; // Clear stored data on new processing

        const formData = new FormData();
        formData.append('branch', branch);
        formData.append('from_date', fromDate);
        formData.append('to_date', toDate);
        formData.append('description_lookup', descriptionLookup);
        formData.append('match_type', matchType);

        try {
            const response = await fetch(`${FLASK_API_BASE_URL}/process_accounting_desc`, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                if (result.data && result.data.length > 0) {
                    descReportData = result.data; // Store the full data
                    renderDescReportTable(descReportData); // Render with full data
                    showMessage(result.message, 'success');
                } else {
                    descReportData = [];
                    renderDescReportTable([]);
                    showMessage(result.message || 'No data found for the specified criteria.', 'info');
                }
            } else {
                showMessage(`Error: ${result.message}`, 'error');
                reportContainer.innerHTML = '';
                descReportData = [];
            }
        } catch (error) {
            console.error('Fetch error:', error);
            showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
            reportContainer.innerHTML = '';
            descReportData = [];
        } finally {
            if (processButton) processButton.disabled = false;
            updateActgDescUI(); // This will show/hide actions and enable/disable buttons/search
        }
    }

    /**
     * Initializes the Description sub-tab: attaches event listeners and performs initial UI update.
     * This function is called by main.js when the sub-tab is activated.
     */
    function initActgDescTab() {
        console.log('Initializing Description Tab...');

        const branchInput = document.getElementById('actgDescBranch');
        const fromDateInput = document.getElementById('actgDescFromDate');
        const toDateInput = document.getElementById('actgDescToDate');
        const descInput = document.getElementById('actgDescInput');
        const matchTypeInput = document.getElementById('actgDescMatchType');
        const processButton = document.getElementById('processActgDescButton');
        const reportContainer = document.getElementById('actgDescReportContainer');
        const searchInput = document.getElementById('actgDescSearchInput');
        const copyButton = document.getElementById('copyActgDescTableButton');
        const reportActions = document.getElementById('actgDescReportActions');

        // Clear report container on tab initialization IF there's no data to persist
        if (reportContainer && descReportData.length === 0) {
            reportContainer.innerHTML = '<p class="text-gray-500 text-center">Description report will appear here after generation.</p>';
        }

        // If descReportData already has data, re-render it instead of clearing
        if (descReportData.length > 0) {
            renderDescReportTable(descReportData);
            // Also ensure input fields retain their values if data persists
            const lastBranch = localStorage.getItem('lastDescBranch');
            const lastFromDate = localStorage.getItem('lastDescFromDate');
            const lastToDate = localStorage.getItem('lastDescToDate');
            const lastDescInput = localStorage.getItem('lastDescInput');
            const lastDescMatchType = localStorage.getItem('lastDescMatchType');

            if (lastBranch) branchInput.value = lastBranch;
            if (lastFromDate) fromDateInput.value = lastFromDate;
            if (lastToDate) toDateInput.value = lastToDate;
            if (lastDescInput) descInput.value = lastDescInput;
            if (lastDescMatchType) matchTypeInput.value = lastDescMatchType;
            
            updateActgDescUI(); // Update UI after values are set
        } else {
            // Clear stored data if no data to persist
            descReportData = [];
            // Clear local storage if no data to persist
            localStorage.removeItem('lastDescBranch');
            localStorage.removeItem('lastDescFromDate');
            localStorage.removeItem('lastDescToDate');
            localStorage.removeItem('lastDescInput');
            localStorage.removeItem('lastDescMatchType');
        }

        // Attach event listeners (ensure they are attached only once)
        if (branchInput && !branchInput.dataset.listenerAttached) {
            branchInput.addEventListener('change', () => {
                updateActgDescUI();
                localStorage.setItem('lastDescBranch', branchInput.value.trim());
            });
            branchInput.dataset.listenerAttached = 'true';
        }
        if (fromDateInput && !fromDateInput.dataset.listenerAttached) {
            fromDateInput.addEventListener('input', (event) => { // Added event parameter
                formatDateInput(event); // Call formatting
                updateActgDescUI();
                localStorage.setItem('lastDescFromDate', fromDateInput.value.trim());
            });
            fromDateInput.dataset.listenerAttached = 'true';
        }
        if (toDateInput && !toDateInput.dataset.listenerAttached) {
            toDateInput.addEventListener('input', (event) => { // Added event parameter
                formatDateInput(event); // Call formatting
                updateActgDescUI();
                localStorage.setItem('lastDescToDate', toDateInput.value.trim());
            });
            toDateInput.dataset.listenerAttached = 'true';
        }
        if (descInput && !descInput.dataset.listenerAttached) {
            descInput.addEventListener('input', () => {
                updateActgDescUI();
                localStorage.setItem('lastDescInput', descInput.value.trim());
            });
            descInput.dataset.listenerAttached = 'true';
        }
        if (matchTypeInput && !matchTypeInput.dataset.listenerAttached) {
            matchTypeInput.addEventListener('change', () => {
                updateActgDescUI();
                localStorage.setItem('lastDescMatchType', matchTypeInput.value.trim());
            });
            matchTypeInput.dataset.listenerAttached = 'true';
        }
        if (processButton && !processButton.dataset.listenerAttached) {
            processButton.addEventListener('click', processDescReport);
            processButton.dataset.listenerAttached = 'true';
        }
        if (searchInput && !searchInput.dataset.listenerAttached) {
            searchInput.addEventListener('input', filterDescReportTable);
            searchInput.dataset.listenerAttached = 'true';
        }
        if (copyButton && !copyButton.dataset.listenerAttached) {
            copyButton.addEventListener('click', copyDescReportTable);
            copyButton.dataset.listenerAttached = 'true';
        }

        // Initial UI update
        updateActgDescUI();
    }

    // Register this sub-tab's initializer with the main application logic
    registerTabInitializer('actgDesc', initActgDescTab);
})(); // End IIFE
