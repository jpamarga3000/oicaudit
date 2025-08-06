// js/tabs/actg_tb.js

(function() { // Start IIFE
    // Variable to store the full TB report data for filtering and persistence
    let tbReportData = [];

    /**
     * Renders the Trial Balance Report table in the UI.
     * @param {Array<Object>} dataToDisplay - The array of row objects to display.
     */
    function renderTbReportTable(dataToDisplay) {
        const tableContainer = document.getElementById('actgTbReportContainer');
        if (!tableContainer) {
            console.error('TB Report table container not found!');
            return;
        }

        tableContainer.innerHTML = ''; // Clear previous content

        if (!dataToDisplay || dataToDisplay.length === 0) {
            tableContainer.innerHTML = '<p class="text-gray-600 text-center">No Trial Balance report data found for the specified criteria.</p>';
            return;
        }

        // Create table element
        const table = document.createElement('table');
        table.className = 'min-w-full bg-white border border-gray-300 rounded-lg shadow-md'; // Tailwind classes for styling

        // Create table header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        // UPDATED Headers for TB Report - Changed 'GL CODE' to 'GL ACCOUNT' to match backend output
        const headers = ['GL ACCOUNT', 'GL NAME', 'DR', 'CR']; // Define headers explicitly

        headers.forEach(headerText => {
            const th = document.createElement('th');
            th.className = 'py-3 px-4 bg-gray-100 text-center text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300';
            
            // Apply text-right class to DR, CR headers
            if (['DR', 'CR'].includes(headerText)) {
                th.classList.add('text-right');
            } else {
                th.classList.add('text-left'); // Ensure GL ACCOUNT and GL NAME are left-aligned
            }
            
            th.textContent = headerText;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Create table body
        const tbody = document.createElement('tbody');
        dataToDisplay.forEach(rowData => {
            const tr = document.createElement('tr');
            tr.className = 'hover:bg-gray-50'; // Hover effect

            headers.forEach(headerKey => {
                const td = document.createElement('td');
                td.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200';

                // Apply text-right class to DR, CR data cells
                if (['DR', 'CR'].includes(headerKey)) {
                    td.classList.add('text-right');
                } else {
                    td.classList.add('text-left'); // Ensure GL ACCOUNT and GL NAME are left-aligned
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
     * Copies the content of the TB Report table to the clipboard in TSV format.
     */
    function copyTbReportTable() {
        const table = document.querySelector('#actgTbReportContainer table');
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
            csv.push(row.join('\t')); // Join columns with a tab for TSV
        }

        const csvString = csv.join('\n');

        // Use a temporary textarea to copy to clipboard
        const textarea = document.createElement('textarea');
        textarea.value = csvString;
        textarea.style.position = 'fixed'; // Prevent scrolling to bottom
        textarea.style.opacity = 0;        // Hide it
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
     * Filters the TB Report table based on search input.
     */
    function filterTbReportTable() {
        const searchInput = document.getElementById('actgTbSearchInput');
        const filter = searchInput.value.toLowerCase();
        
        if (filter === '') {
            renderTbReportTable(tbReportData); // Always use the full tbReportData here
        } else if (tbReportData.length > 0) {
            const filteredData = tbReportData.filter(row => {
                return Object.values(row).some(value => {
                    return String(value).toLowerCase().includes(filter);
                });
            });
            renderTbReportTable(filteredData);
        }
    }

    /**
     * Loads "As Of Dates" (CSV/Excel filenames) for the selected branch from the backend.
     * Populates the actgTbAsOfDate dropdown.
     * @param {string} branch - The selected branch name.
     */
    async function loadTbAsOfDates(branch) {
        const asOfDateDropdown = document.getElementById('actgTbAsOfDate');
        asOfDateDropdown.innerHTML = '<option value="">Loading Dates...</option>';
        asOfDateDropdown.disabled = true;

        if (!branch) {
            asOfDateDropdown.innerHTML = '<option value="">Select Date</option>';
            console.log('No branch selected, skipping TB As Of Dates load.');
            updateActgTbUI();
            return;
        }

        try {
            const response = await fetch(`${FLASK_API_BASE_URL}/get_tb_as_of_dates?branch=${encodeURIComponent(branch)}`);
            const result = await response.json();

            if (response.ok) {
                if (result.data && Array.isArray(result.data) && result.data.length > 0) {
                    asOfDateDropdown.innerHTML = '<option value="">Select Date</option>'; // Clear "Loading..."
                    result.data.forEach(dateFilename => {
                        const option = document.createElement('option');
                        option.value = dateFilename;
                        option.textContent = dateFilename; // Display filename as is
                        asOfDateDropdown.appendChild(option);
                    });
                    asOfDateDropdown.disabled = false;
                    showMessage('As Of Dates loaded successfully.', 'success', '', 1500);
                } else {
                    asOfDateDropdown.innerHTML = '<option value="">No Dates Found</option>';
                    showMessage('No "As Of Dates" files found for this branch.', 'info', '', 2000);
                }
            } else {
                showMessage(`Error loading As Of Dates: ${result.message || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            asOfDateDropdown.innerHTML = '<option value="">Error Loading Dates</option>';
            console.error('Fetch error:', error);
            showMessage(`An unexpected error occurred while loading As Of Dates: ${error.message}`, 'error');
        } finally {
            updateActgTbUI();
        }
    }

    /**
     * Updates the state of the "Generate Report" button and actions bar.
     */
    function updateActgTbUI() {
        const branchInput = document.getElementById('actgTbBranch');
        const asOfDateInput = document.getElementById('actgTbAsOfDate');
        const processButton = document.getElementById('processActgTbButton');
        const reportActions = document.getElementById('actgTbReportActions');
        const tableExists = document.querySelector('#actgTbReportContainer table');

        if (processButton) {
            processButton.disabled = !(branchInput.value.trim() && asOfDateInput.value.trim());
        }

        if (reportActions) {
            if (tableExists) {
                reportActions.classList.remove('hidden');
            } else {
                reportActions.classList.add('hidden');
            }
        }
        
        // Also enable/disable search and copy buttons based on table existence
        const searchInput = document.getElementById('actgTbSearchInput');
        const copyButton = document.getElementById('copyActgTbTableButton');
        if (searchInput) {
            searchInput.disabled = !tableExists;
            if (!tableExists) searchInput.value = ''; // Clear search if table disappears
        }
        if (copyButton) {
            copyButton.disabled = !tableExists;
        }
    }

    /**
     * Handles the processing request for Trial Balance data.
     */
    async function processTrialBalance() {
        const branchInput = document.getElementById('actgTbBranch');
        const asOfDateInput = document.getElementById('actgTbAsOfDate');
        const processButton = document.getElementById('processActgTbButton');
        const reportContainer = document.getElementById('actgTbReportContainer');
        const reportActions = document.getElementById('actgTbReportActions');
        const searchInput = document.getElementById('actgTbSearchInput');
        const copyButton = document.getElementById('copyActgTbTableButton');

        const branch = branchInput.value.trim();
        const asOfDate = asOfDateInput.value.trim();

        if (!branch || !asOfDate) {
            showMessage('Please select both Branch and As Of Date.', 'error');
            return;
        }

        // Disable UI elements during processing
        if (processButton) processButton.disabled = true;
        if (searchInput) { searchInput.disabled = true; searchInput.value = ''; }
        if (copyButton) copyButton.disabled = true;
        if (reportActions) reportActions.classList.add('hidden'); // Hide actions during loading

        showMessage('Generating Trial Balance report... This may take a moment.', 'loading');
        reportContainer.innerHTML = ''; // Clear previous report

        // Clear stored data on new processing
        tbReportData = [];

        const formData = new FormData();
        formData.append('branch', branch);
        formData.append('as_of_date', asOfDate);

        try {
            const response = await fetch(`${FLASK_API_BASE_URL}/process_trial_balance`, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                if (result.data && result.data.length > 0) {
                    tbReportData = result.data; // Store the full data
                    renderTbReportTable(tbReportData); // Render with full data
                    showMessage(result.message, 'success');
                } else {
                    tbReportData = [];
                    renderTbReportTable([]); // Render empty table
                    showMessage(result.message || 'No data found for the specified criteria.', 'info');
                }
            } else {
                showMessage(`Error: ${result.message}`, 'error');
                reportContainer.innerHTML = ''; // Clear on error
                tbReportData = [];
            }
        } catch (error) {
            console.error('Fetch error:', error);
            showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
            reportContainer.innerHTML = ''; // Clear on error
            tbReportData = [];
        } finally {
            // Re-enable UI elements and update state
            if (processButton) processButton.disabled = false;
            updateActgTbUI(); // This will show/hide actions and enable/disable buttons/search
        }
    }

    /**
     * Initializes the Trial Balance sub-tab: attaches event listeners and performs initial UI update.
     * This function is called by main.js when the sub-tab is activated.
     */
    function initActgTbTab() {
        console.log('Initializing Trial Balance Tab...');

        const branchInput = document.getElementById('actgTbBranch');
        const asOfDateInput = document.getElementById('actgTbAsOfDate');
        const processButton = document.getElementById('processActgTbButton');
        const searchInput = document.getElementById('actgTbSearchInput');
        const copyButton = document.getElementById('copyActgTbTableButton');
        const reportContainer = document.getElementById('actgTbReportContainer');

        // Clear report container on tab initialization IF there's no data to persist
        if (reportContainer && tbReportData.length === 0) {
            reportContainer.innerHTML = '<p class="text-gray-500 text-center">Trial Balance report will appear here after generation.</p>';
        }

        // If tbReportData already has data, re-render it instead of clearing
        if (tbReportData.length > 0) {
            renderTbReportTable(tbReportData);
            // Also ensure input fields retain their values if data persists
            const lastBranch = localStorage.getItem('lastTbBranch');
            const lastAsOfDate = localStorage.getItem('lastTbAsOfDate');
            if (lastBranch) branchInput.value = lastBranch;
            // AsOfDate dropdown needs to be loaded dynamically first before setting its value
            if (lastBranch) loadTbAsOfDates(lastBranch).then(() => {
                if (lastAsOfDate) asOfDateInput.value = lastAsOfDate;
                updateActgTbUI(); // Update UI after values are set
            });
        } else {
            // Clear stored data if no data to persist
            tbReportData = [];
            // Clear local storage if no data to persist
            localStorage.removeItem('lastTbBranch');
            localStorage.removeItem('lastTbAsOfDate');
            // Ensure As Of Date dropdown is reset if no data to persist
            if (asOfDateInput) {
                asOfDateInput.innerHTML = '<option value="">Select Date</option>';
                asOfDateInput.disabled = true;
            }
        }

        // Attach event listeners (ensure they are attached only once)
        if (branchInput && !branchInput.dataset.listenerAttached) {
            branchInput.addEventListener('change', () => {
                updateActgTbUI();
                loadTbAsOfDates(branchInput.value.trim());
                // Store selected branch in local storage
                localStorage.setItem('lastTbBranch', branchInput.value.trim());
            });
            branchInput.dataset.listenerAttached = 'true';
        }
        if (asOfDateInput && !asOfDateInput.dataset.listenerAttached) {
            asOfDateInput.addEventListener('change', () => {
                updateActgTbUI();
                // Store selected as of date in local storage
                localStorage.setItem('lastTbAsOfDate', asOfDateInput.value.trim());
            });
            asOfDateInput.dataset.listenerAttached = 'true';
        }
        if (processButton && !processButton.dataset.listenerAttached) {
            processButton.addEventListener('click', processTrialBalance);
            processButton.dataset.listenerAttached = 'true';
        }
        if (searchInput && !searchInput.dataset.listenerAttached) {
            searchInput.addEventListener('input', filterTbReportTable);
            searchInput.dataset.listenerAttached = 'true';
        }
        if (copyButton && !copyButton.dataset.listenerAttached) {
            copyButton.addEventListener('click', copyTbReportTable);
            copyButton.dataset.listenerAttached = 'true';
        }

        // Initial UI update
        updateActgTbUI();
        // Load dates for initially selected branch if any
        if (branchInput.value.trim() && tbReportData.length === 0) { // Only load if not persisting data
            loadTbAsOfDates(branchInput.value.trim());
        }
    }

    // Register this sub-tab's initializer with the main application logic
    registerTabInitializer('actgTb', initActgTbTab);
})(); // End IIFE