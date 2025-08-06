// js/tabs/journal_voucher.js

(function() {
    let journalVoucherSelectedFiles = [];
    let journalVoucherReportData = []; // To store the full report data for filtering

    /**
     * Removes a file from the journalVoucherSelectedFiles array and updates the UI.
     * @param {number} indexToRemove - The index of the file to remove.
     */
    function removeJournalVoucherFile(indexToRemove) {
        journalVoucherSelectedFiles.splice(indexToRemove, 1);
        renderSelectedFiles(journalVoucherSelectedFiles, 'journalVoucherFilesDisplay', removeJournalVoucherFile);
        updateJournalVoucherUI();
    }

    /**
     * Updates the state of the "Process Journal Voucher" button and report actions.
     */
    function updateJournalVoucherUI() {
        const processButton = document.getElementById('processJournalVoucherButton');
        const branchInput = document.getElementById('journalVoucherBranch');
        const outputFolderInput = document.getElementById('journalVoucherOutputFolder');
        const reportActions = document.getElementById('journalVoucherReportActions');
        const searchInput = document.getElementById('journalVoucherSearchInput');
        const copyButton = document.getElementById('copyJournalVoucherTableButton');
        const tableExists = document.querySelector('#journalVoucherReportTableContainer table');

        if (processButton && branchInput && outputFolderInput) {
            processButton.disabled = !(
                journalVoucherSelectedFiles.length > 0 &&
                branchInput.value.trim() !== '' &&
                outputFolderInput.value.trim() !== ''
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
     * Renders the Journal Voucher Report table in the UI.
     * @param {Array<Object>} dataToDisplay - The array of row objects to display.
     */
    function renderJournalVoucherTable(dataToDisplay) {
        const tableContainer = document.getElementById('journalVoucherReportTableContainer');
        if (!tableContainer) {
            console.error('Journal Voucher Report table container not found!');
            return;
        }

        tableContainer.innerHTML = ''; // Clear previous content

        if (!dataToDisplay || dataToDisplay.length === 0) {
            tableContainer.innerHTML = '<p class="text-gray-600 text-center">No Journal Voucher report data found for the specified criteria.</p>';
            return;
        }

        const table = document.createElement('table');
        table.className = 'min-w-full bg-white border border-gray-300 rounded-lg shadow-md';

        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        const headers = ['ACCOUNT', 'TITLE', 'DATE', 'DESCRIPTION', 'DR', 'CR']; // Define headers

        headers.forEach(headerText => {
            const th = document.createElement('th');
            th.className = 'py-3 px-4 bg-gray-100 text-left text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300';
            if (['DR', 'CR'].includes(headerText)) {
                th.classList.add('text-right');
            } else if (['DATE'].includes(headerText)) {
                th.classList.add('text-center');
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
                if (['DR', 'CR'].includes(headerKey)) {
                    td.classList.add('text-right');
                } else if (['DATE'].includes(headerKey)) {
                    td.classList.add('text-center');
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
     * Copies the content of the Journal Voucher Report table to the clipboard in TSV format.
     */
    function copyJournalVoucherTable() {
        const table = document.querySelector('#journalVoucherReportTableContainer table');
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
     * Filters the Journal Voucher Report table based on search input.
     */
    function filterJournalVoucherTable() {
        const searchInput = document.getElementById('journalVoucherSearchInput');
        const filter = searchInput.value.toLowerCase();
        
        if (filter === '') {
            renderJournalVoucherTable(journalVoucherReportData);
        } else if (journalVoucherReportData.length > 0) {
            const filteredData = journalVoucherReportData.filter(row => {
                return Object.values(row).some(value => {
                    return String(value).toLowerCase().includes(filter);
                });
            });
            renderJournalVoucherTable(filteredData);
        }
    }

    /**
     * Handles the processing request for Journal Voucher data.
     */
    async function processJournalVoucher() {
        const branchInput = document.getElementById('journalVoucherBranch');
        const outputFolderInput = document.getElementById('journalVoucherOutputFolder');
        const processButton = document.getElementById('processJournalVoucherButton');
        const reportContainer = document.getElementById('journalVoucherReportTableContainer');
        const reportActions = document.getElementById('journalVoucherReportActions');
        const searchInput = document.getElementById('journalVoucherSearchInput');
        const copyButton = document.getElementById('copyJournalVoucherTableButton');

        const branch = branchInput.value.trim();
        const outputPath = outputFolderInput.value.trim();

        if (journalVoucherSelectedFiles.length === 0 || !branch || !outputPath) {
            showMessage('Please select DBF files, select a branch, and enter the output folder path.', 'error');
            return;
        }

        if (processButton) processButton.disabled = true;
        if (searchInput) { searchInput.disabled = true; searchInput.value = ''; }
        if (copyButton) copyButton.disabled = true;
        if (reportActions) reportActions.classList.add('hidden');

        showMessage('Processing Journal Voucher files... This may take a moment.', 'loading');
        reportContainer.innerHTML = '';
        journalVoucherReportData = [];

        const formData = new FormData();
        journalVoucherSelectedFiles.forEach(file => {
            formData.append('files', file);
        });
        formData.append('branch', branch);
        formData.append('output_dir', outputPath);

        try {
            const response = await fetch(`${FLASK_API_BASE_URL}/process_journal_voucher`, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                if (result.data && result.data.length > 0) {
                    journalVoucherReportData = result.data;
                    renderJournalVoucherTable(journalVoucherReportData);
                    showMessage(result.message, 'success', outputPath);
                } else {
                    journalVoucherReportData = [];
                    renderJournalVoucherTable([]);
                    showMessage(result.message || 'No data found for the specified criteria.', 'info');
                }
            } else {
                showMessage(`Error: ${result.message}`, 'error');
                reportContainer.innerHTML = '';
                journalVoucherReportData = [];
            }
        } catch (error) {
            console.error('Fetch error:', error);
            showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
            reportContainer.innerHTML = '';
            journalVoucherReportData = [];
        } finally {
            if (processButton) processButton.disabled = false;
            updateJournalVoucherUI();
        }
    }

    /**
     * Initializes the Journal Voucher sub-tab.
     */
    function initJournalVoucherTab() {
        console.log('Initializing Journal Voucher Tab...');

        const branchInput = document.getElementById('journalVoucherBranch');
        const inputFilesInput = document.getElementById('journalVoucherInputFiles');
        const outputFolderInput = document.getElementById('journalVoucherOutputFolder');
        const processButton = document.getElementById('processJournalVoucherButton');
        const searchInput = document.getElementById('journalVoucherSearchInput');
        const copyButton = document.getElementById('copyJournalVoucherTableButton');
        const reportContainer = document.getElementById('journalVoucherReportTableContainer');

        // Clear report container on tab initialization
        if (reportContainer) {
            reportContainer.innerHTML = '<p class="text-gray-500 text-center">Journal Voucher report will appear here after generation.</p>';
        }

        // If data exists in localStorage, re-render and load inputs
        if (journalVoucherReportData.length > 0) {
            renderJournalVoucherTable(journalVoucherReportData);
            const lastBranch = localStorage.getItem('lastJournalVoucherBranch');
            const lastOutputFolder = localStorage.getItem('lastJournalVoucherOutputFolder');
            if (lastBranch) branchInput.value = lastBranch;
            if (lastOutputFolder) outputFolderInput.value = lastOutputFolder;
        } else {
            // Clear localStorage if no data to persist
            localStorage.removeItem('lastJournalVoucherBranch');
            localStorage.removeItem('lastJournalVoucherOutputFolder');
        }

        // Event Listeners
        if (branchInput && !branchInput.dataset.listenerAttached) {
            branchInput.addEventListener('change', () => {
                updateJournalVoucherUI();
                localStorage.setItem('lastJournalVoucherBranch', branchInput.value.trim());
            });
            branchInput.dataset.listenerAttached = 'true';
        }
        if (inputFilesInput && !inputFilesInput.dataset.listenerAttached) {
            inputFilesInput.addEventListener('change', (event) => {
                Array.from(event.target.files).forEach(file => {
                    if (!journalVoucherSelectedFiles.some(existingFile => existingFile.name === file.name)) {
                        journalVoucherSelectedFiles.push(file);
                    }
                });
                event.target.value = '';
                renderSelectedFiles(journalVoucherSelectedFiles, 'journalVoucherFilesDisplay', removeJournalVoucherFile);
                updateJournalVoucherUI();
            });
            inputFilesInput.dataset.listenerAttached = 'true';
        }
        if (outputFolderInput && !outputFolderInput.dataset.listenerAttached) {
            outputFolderInput.addEventListener('input', () => {
                updateJournalVoucherUI();
                localStorage.setItem('lastJournalVoucherOutputFolder', outputFolderInput.value.trim());
            });
            outputFolderInput.dataset.listenerAttached = 'true';
        }
        if (processButton && !processButton.dataset.listenerAttached) {
            processButton.addEventListener('click', processJournalVoucher);
            processButton.dataset.listenerAttached = 'true';
        }
        if (searchInput && !searchInput.dataset.listenerAttached) {
            searchInput.addEventListener('input', filterJournalVoucherTable);
            searchInput.dataset.listenerAttached = 'true';
        }
        if (copyButton && !copyButton.dataset.listenerAttached) {
            copyButton.addEventListener('click', copyJournalVoucherTable);
            copyButton.dataset.listenerAttached = 'true';
        }

        // Initial UI update
        updateJournalVoucherUI();
        renderSelectedFiles(journalVoucherSelectedFiles, 'journalVoucherFilesDisplay', removeJournalVoucherFile);
    }

    registerTabInitializer('journalVoucherSection', initJournalVoucherTab);
})();
