// js/tabs/actg_gl.js

(function() { // Start IIFE
    let glReportData = []; // To store the full report data for persistence and filtering
    // Updated to store objects with raw and formatted codes
    let glNameMap = new Map(); // Key: GL Name (string), Value: {raw: string, formatted: string}
    let glCodeMap = new Map(); // Key: Formatted GL Code (string), Value: {name: string, raw: string}

    // Variable to hold the actual datalist element
    let glNameDatalistElement = null;
    let glNameInputElement = null;

    // List of branches that should NOT have GL Code formatting in the UI autofill
    const BRANCHES_NO_GL_FORMATTING_UI = ['BAYUGAN', 'BALINGASAG', 'TORIL', 'ILUSTRE', 'TUBIGON'];

    /**
     * Helper function to set the caret (cursor) position in an input field.
     * @param {HTMLInputElement} ctrl - The input element.
     * @param {number} pos - The desired cursor position.
     */
    function setCaretPosition(ctrl, pos) {
        if (ctrl.setSelectionRange) {
            ctrl.focus();
            ctrl.setSelectionRange(pos, pos);
        } else if (ctrl.createTextRange) {
            let range = ctrl.createTextRange();
            range.collapse(true);
            range.moveEnd('character', pos);
            range.moveStart('character', pos);
            range.select();
        }
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
        updateActgGlUI(); // Trigger UI update on input change
    }

    /**
     * Formats a GL Code string based on its digit length.
     * This function is now primarily for client-side display consistency if needed,
     * but the backend will provide the already formatted/raw code.
     * @param {string} code - The raw GL Code string (can contain non-digits).
     * @returns {string} The formatted GL Code or raw digits if not 5, 6, 9, or 10 digits.
     */
    function formatGlCode(code) {
        // This function is still here for potential future client-side formatting needs,
        // but the backend is now responsible for providing the correct format based on branch.
        const digits = String(code).replace(/\D/g, ''); // Get only digits
        
        if (digits.length === 1) {
            return digits;
        } else if (digits.length === 3) {
            return `${digits[0]}-${digits.substring(1, 3)}`;
        } else if (digits.length === 5) {
            return `${digits[0]}-${digits.substring(1, 3)}-${digits.substring(3, 5)}`;
        } else if (digits.length === 9) {
            return `${digits[0]}-${digits.substring(1, 3)}-${digits.substring(3, 5)}-${digits.substring(5, 9)}`;
        } else if (digits.length === 6) {
            if (digits.endsWith('0')) {
                const fiveDigits = digits.substring(0, 5);
                return `${fiveDigits[0]}-${fiveDigits.substring(1, 3)}-${fiveDigits.substring(3, 5)}`;
            } else {
                return `${digits[0]}-${digits.substring(1, 3)}-${digits.substring(3, 5)}-${digits.substring(5, 6)}`;
            }
        } else if (digits.length === 10) {
            return `${digits[0]}-${digits.substring(1, 3)}-${digits.substring(3, 5)}-${digits.substring(5, 10)}`;
        }
        return digits; // For any other length, just return the raw digits.
    }


    /**
     * Loads GL Names and Codes from the backend based on the selected branch.
     * Populates glNameMap, glCodeMap, and the GL Names datalist.
     * Stores both raw and formatted GL Codes.
     * @param {string} branch - The selected branch name.
     */
    async function fetchAndPopulateGlNames(branch) {
        // Ensure elements are available before proceeding
        if (!glNameDatalistElement || !glNameInputElement) {
            console.error('fetchAndPopulateGlNames: Datalist or input element not found during execution. Skipping population.');
            return;
        }

        glNameDatalistElement.innerHTML = ''; // Clear previous options
        glNameMap.clear(); // Reset maps
        glCodeMap.clear();

        if (!branch) {
            console.log('No branch selected, skipping GL name fetch.');
            return;
        }

        showMessage('Loading GL Names and Codes...', 'info');

        try {
            console.log(`Fetching GL names for branch: ${branch}`);
            // Pass the branch name to the backend
            const response = await fetch(`${FLASK_API_BASE_URL}/get_gl_names_and_codes?branch=${encodeURIComponent(branch)}`);
            const result = await response.json();

            if (response.ok) {
                if (result.data && Array.isArray(result.data)) {
                    console.log('Received GL Names data from backend:', result.data);

                    result.data.forEach(item => {
                        const glName = item.TITLE ? String(item.TITLE).trim() : '';
                        const glCodeRaw = item.GLACC_RAW ? String(item.GLACC_RAW).trim() : ''; // Get raw code
                        const glCodeFormatted = item.GLACC_FORMATTED ? String(item.GLACC_FORMATTED).trim() : ''; // Get formatted code

                        if (glName && glCodeRaw) { // Ensure at least raw code exists
                            glNameMap.set(glName, {raw: glCodeRaw, formatted: glCodeFormatted}); // Store both
                            glCodeMap.set(glCodeFormatted, {name: glName, raw: glCodeRaw}); // Store both
                            // Also store raw code in glCodeMap for potential lookup by raw code if needed
                            glCodeMap.set(glCodeRaw, {name: glName, formatted: glCodeFormatted}); 

                            const option = document.createElement('option');
                            option.value = glName; // Datalist options are typically the display value
                            glNameDatalistElement.appendChild(option); 
                        }
                    });
                    console.log(`Datalist population complete. Total options added: ${glNameDatalistElement.children.length}`);
                    showMessage('GL Names and Codes loaded successfully.', 'success', '', 1500);
                } else {
                    showMessage('No GL Names and Codes data found for this branch.', 'info', '', 2000);
                }
            } else {
                showMessage(`Error loading GL Names: ${result.message || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            console.error('Fetch error:', error);
            showMessage(`An unexpected error occurred while loading GL Names: ${error.message}`, 'error');
        } finally {
            updateActgGlUI();
        }
    }

    /**
     * Handles input on the GL Name field to autofill GL Code.
     */
    function handleGlNameInput() {
        const glNameInput = document.getElementById('actgGlGlName');
        const glCodeInput = document.getElementById('actgGlGlCode');
        const branchInput = document.getElementById('actgGlBranch'); // Get branch input
        const selectedBranch = branchInput.value.trim().toUpperCase();

        const selectedGlName = glNameInput.value.trim();
        
        if (glNameMap.has(selectedGlName)) {
            const codeData = glNameMap.get(selectedGlName); 
            let codeToDisplay = '';

            // Conditional formatting based on branch
            if (BRANCHES_NO_GL_FORMATTING_UI.includes(selectedBranch)) {
                codeToDisplay = codeData.raw; // Use raw code for specified branches
            } else {
                codeToDisplay = codeData.formatted; // Use formatted code for others
            }

            glCodeInput.value = codeToDisplay;
            localStorage.setItem('lastGlName', selectedGlName);
            localStorage.setItem('lastGlCode', glCodeInput.value);
        } else {
            glCodeInput.value = '';
            localStorage.removeItem('lastGlName'); 
        }
        updateActgGlUI();
    }

    /**
     * Handles input on the GL Code field to autofill GL Name.
     * Also applies formatting to the GL Code field as user types.
     */
    function handleGlCodeInput(event) {
        const glNameInput = document.getElementById('actgGlGlName');
        const glCodeInput = document.getElementById('actgGlGlCode');
        const branchInput = document.getElementById('actgGlBranch'); // Get branch input
        const selectedBranch = branchInput.value.trim().toUpperCase();

        let currentGlCode = glCodeInput.value;
        let cursorPosition = glCodeInput.selectionStart; 

        const oldLength = currentGlCode.length;
        
        let formattedGlCode = '';
        if (BRANCHES_NO_GL_FORMATTING_UI.includes(selectedBranch)) {
            formattedGlCode = currentGlCode.replace(/\D/g, ''); // Keep only digits, no specific format
        } else {
            formattedGlCode = formatGlCode(currentGlCode); // Apply standard formatting
        }

        glCodeInput.value = formattedGlCode;

        const newLength = formattedGlCode.length;
        
        // Adjust cursor position based on added/removed non-digit characters
        const nonDigitsBeforeCursor = (currentGlCode.substring(0, cursorPosition).match(/[^0-9]/g) || []).length;
        const newNonDigitsBeforeCursor = (formattedGlCode.substring(0, cursorPosition + (newLength - oldLength)).match(/[^0-9]/g) || []).length;

        let adjustedCursorPosition = cursorPosition + (newNonDigitsBeforeCursor - nonDigitsBeforeCursor);

        adjustedCursorPosition = Math.min(adjustedCursorPosition, newLength);
        adjustedCursorPosition = Math.max(0, adjustedCursorPosition);

        if (event && event.inputType === 'deleteContentBackward' && cursorPosition > 0 && currentGlCode.charAt(cursorPosition -1) === '-') {
            adjustedCursorPosition--;
        }

        setCaretPosition(glCodeInput, adjustedCursorPosition);

        // Lookup GL Name using the formatted code (or raw if that's what's displayed)
        // Prioritize lookup by formatted code if formatting is applied
        let glName = '';
        if (glCodeMap.has(formattedGlCode)) { 
            glName = glCodeMap.get(formattedGlCode).name;
        } else if (glCodeMap.has(currentGlCode.replace(/\D/g, ''))) { // Try lookup by raw digits if no match on formatted
             glName = glCodeMap.get(currentGlCode.replace(/\D/g, '')).name;
        }

        if (glName) {
            glNameInput.value = glName;
            localStorage.setItem('lastGlName', glNameInput.value);
            localStorage.setItem('lastGlCode', glCodeInput.value);
        } else {
            glNameInput.value = ''; 
            localStorage.removeItem('lastGlName');
        }
        updateActgGlUI();
    }

    /**
     * Renders the General Ledger Report table in the UI.
     * @param {Array<Object>} dataToDisplay - The array of row objects to display.
     */
    function renderGlReportTable(dataToDisplay) { 
        const tableContainer = document.getElementById('actgGlReportContainer');
        if (!tableContainer) {
            console.error('GL Report table container not found!');
            return;
        }

        tableContainer.innerHTML = ''; 

        if (!dataToDisplay || dataToDisplay.length === 0) {
            tableContainer.innerHTML = '<p class="text-gray-600 text-center">No General Ledger report data found for the specified criteria.</p>';
            return;
        }

        tableContainer.style.maxHeight = '500px'; 
        tableContainer.style.overflowY = 'auto';
        tableContainer.style.position = 'relative'; 

        const table = document.createElement('table');
        table.className = 'min-w-full bg-white border border-gray-300 rounded-lg shadow-md'; 

        const thead = document.createElement('thead');
        thead.style.position = 'sticky';
        thead.style.top = '0'; 
        thead.style.zIndex = '10'; 
        thead.style.backgroundColor = '#f3f4f6'; 

        const headerRow = document.createElement('tr');
        const headers = ['DATE', 'GL CODE', 'GL NAME', 'TRN', 'DESCRIPTION', 'REF', 'DR', 'CR', 'BALANCE'];

        headers.forEach(headerText => {
            const th = document.createElement('th');
            th.className = 'py-3 px-4 bg-gray-100 text-center text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300'; 
            
            if (['DR', 'CR', 'BALANCE'].includes(headerText)) {
                th.classList.add('text-right');
            }
            
            th.textContent = headerText;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        dataToDisplay.forEach((rowData, rowIndex) => { 
            const tr = document.createElement('tr');
            tr.className = 'hover:bg-gray-50'; 

            headers.forEach(headerKey => { 
                const td = document.createElement('td');
                td.className = 'py-2 px-4 text-sm text-gray-800 border-b border-gray-200';

                if (['DR', 'CR', 'BALANCE'].includes(headerKey)) {
                    td.classList.add('text-right');
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
     * Copies the content of the GL Report table to the clipboard in TSV format.
     */
    function copyGlReportTable() {
        const table = document.querySelector('#actgGlReportContainer table');
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
     * Filters the GL Report table based on search input.
     */
    function filterGlReportTable() {
        const searchInput = document.getElementById('actgGlSearchInput');
        const filter = searchInput.value.toLowerCase();
        
        if (filter === '') {
            renderGlReportTable(glReportData); 
        } else if (glReportData.length > 0) {
            const filteredData = glReportData.filter(row => {
                return Object.values(row).some(value => {
                    return String(value).toLowerCase().includes(filter);
                });
            });
            renderGlReportTable(filteredData);
        }
    }

    /**
     * Updates the state of the "Generate Report" button and actions bar.
     */
    function updateActgGlUI() {
        const branchInput = document.getElementById('actgGlBranch');
        const fromDateInput = document.getElementById('actgGlFromDate');
        const toDateInput = document.getElementById('actgGlToDate');
        const glCodeInput = document.getElementById('actgGlGlCode');
        const processButton = document.getElementById('processActgGlButton');
        const reportActions = document.getElementById('actgGlReportActions');
        const tableExists = document.querySelector('#actgGlReportContainer table');
        const searchInput = document.getElementById('actgGlSearchInput');
        const copyButton = document.getElementById('copyActgGlTableButton');

        if (processButton) {
            processButton.disabled = !(
                branchInput.value.trim() &&
                isValidDate(fromDateInput.value.trim()) &&
                isValidDate(toDateInput.value.trim()) &&
                glCodeInput.value.trim() // GL Code is now the main filter
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
     * Handles the processing request for Accounting General Ledger data.
     */
    async function processGlReport() {
        const branchInput = document.getElementById('actgGlBranch');
        const fromDateInput = document.getElementById('actgGlFromDate');
        const toDateInput = document.getElementById('actgGlToDate');
        const glCodeInput = document.getElementById('actgGlGlCode');
        const processButton = document.getElementById('processActgGlButton');
        const reportContainer = document.getElementById('actgGlReportContainer');
        const reportActions = document.getElementById('actgGlReportActions');
        const searchInput = document.getElementById('actgGlSearchInput');
        const copyButton = document.getElementById('copyActgGlTableButton');

        const branch = branchInput.value.trim();
        const fromDate = fromDateInput.value.trim();
        const toDate = toDateInput.value.trim();
        const glCode = glCodeInput.value.trim();

        if (!branch || !isValidDate(fromDate) || !isValidDate(toDate) || !glCode) {
            showMessage('Please fill all required fields and ensure dates are in MM/DD/YYYY format.', 'error');
            return;
        }

        // Disable UI elements during processing
        if (processButton) processButton.disabled = true;
        if (searchInput) { searchInput.disabled = true; searchInput.value = ''; }
        if (copyButton) copyButton.disabled = true;
        if (reportActions) reportActions.classList.add('hidden');

        showMessage('Generating General Ledger report... This may take a moment.', 'loading');
        reportContainer.innerHTML = ''; 
        glReportData = []; 

        const formData = new FormData();
        formData.append('branch', branch);
        formData.append('from_date', fromDate);
        formData.append('to_date', toDate);
        formData.append('gl_code', glCode); 

        try {
            const response = await fetch(`${FLASK_API_BASE_URL}/process_accounting_gl`, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                if (result.data && result.data.length > 0) {
                    glReportData = result.data; 
                    renderGlReportTable(glReportData); 
                    showMessage(result.message, 'success');
                } else {
                    glReportData = [];
                    renderGlReportTable([]);
                    showMessage(result.message || 'No data found for the specified criteria.', 'info');
                }
            } else {
                showMessage(`Error: ${result.message}`, 'error');
                reportContainer.innerHTML = '';
                glReportData = [];
            }
        } catch (error) {
            console.error('Fetch error:', error);
            showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
            reportContainer.innerHTML = '';
            glReportData = [];
        } finally {
            if (processButton) processButtonButton.disabled = false;
            updateActgGlUI();
        }
    }

    /**
     * Initializes the General Ledger sub-tab: attaches event listeners and performs initial UI update.
     * This function is called by main.js when the sub-tab is activated.
     */
    function initActgGlTab() {
        console.log('Initializing General Ledger Tab...');

        const branchInput = document.getElementById('actgGlBranch');
        const fromDateInput = document.getElementById('actgGlFromDate');
        const toDateInput = document.getElementById('actgGlToDate');
        const glNameInput = document.getElementById('actgGlGlName'); // New GL Name input
        const glCodeInput = document.getElementById('actgGlGlCode'); // New GL Code input
        const processButton = document.getElementById('processActgGlButton');
        const reportContainer = document.getElementById('actgGlReportContainer');
        const searchInput = document.getElementById('actgGlSearchInput');
        const copyButton = document.getElementById('copyActgGlTableButton');
        const reportActions = document.getElementById('actgGlReportActions');

        // Store references to the GL name input and datalist globally within the IIFE
        // so other functions like fetchAndPopulateGlNames can access them reliably.
        glNameInputElement = glNameInput;
        glNameDatalistElement = document.getElementById('glNameDatalist');


        // Initial check for required elements before attaching listeners
        if (!branchInput || !fromDateInput || !toDateInput || !glNameInput || !glCodeInput || !processButton || !reportContainer || !searchInput || !copyButton || !reportActions || !glNameDatalistElement) {
            console.error("Critical: One or more required DOM elements for actg_gl tab were not found. Cannot initialize tab fully. Ensure all element IDs are correct in PHP, and datalist element exists.");
            return; 
        }

        // Clear report container on tab initialization IF there's no data to persist
        if (reportContainer && glReportData.length === 0) {
            reportContainer.innerHTML = '<p class="text-gray-500 text-center">General Ledger report will appear here after generation.</p>';
        }

        // If glReportData already has data, re-render it instead of clearing
        if (glReportData.length > 0) {
            renderGlReportTable(glReportData);
            // Also ensure input fields retain their values if data persists
            const lastBranch = localStorage.getItem('lastGlBranch');
            const lastFromDate = localStorage.getItem('lastGlFromDate');
            const lastToDate = localStorage.getItem('lastGlToDate');
            const lastGlCode = localStorage.getItem('lastGlCode'); // Retrieve stored GL Code
            const lastGlName = localStorage.getItem('lastGlName'); // Retrieve stored GL Name


            if (lastBranch) branchInput.value = lastBranch;
            if (lastFromDate) fromDateInput.value = lastFromDate;
            if (lastToDate) toDateInput.value = lastToDate;
            if (lastGlCode) glCodeInput.value = lastGlCode; // Set GL Code
            if (lastGlName) glNameInput.value = lastGlName; // Set GL Name
            
            updateActgGlUI(); // Update UI after values are set
        } else {
            // Clear stored data if no data to persist
            glReportData = [];
            // Clear local storage if no data to persist
            localStorage.removeItem('lastGlBranch');
            localStorage.removeItem('lastGlFromDate');
            localStorage.removeItem('lastGlToDate');
            localStorage.removeItem('lastGlCode');
            localStorage.removeItem('lastGlName');
        }

        // Attach event listeners (ensure they are attached only once)
        if (!branchInput.dataset.listenerAttached) {
            branchInput.addEventListener('change', () => {
                updateActgGlUI();
                localStorage.setItem('lastGlBranch', branchInput.value.trim());
                // Fetch GL names when branch changes
                fetchAndPopulateGlNames(branchInput.value.trim());
            });
            branchInput.dataset.listenerAttached = 'true';
        }
        if (!fromDateInput.dataset.listenerAttached) {
            fromDateInput.addEventListener('input', (event) => { // Added event parameter
                formatDateInput(event); // Call formatting
                updateActgGlUI();
                localStorage.setItem('lastGlFromDate', fromDateInput.value.trim());
            });
            fromDateInput.dataset.listenerAttached = 'true';
        }
        if (!toDateInput.dataset.listenerAttached) {
            toDateInput.addEventListener('input', (event) => { // Added event parameter
                formatDateInput(event); // Call formatting
                updateActgGlUI();
                localStorage.setItem('lastGlToDate', toDateInput.value.trim());
            });
            toDateInput.dataset.listenerAttached = 'true';
        }
        // New event listeners for GL Name and GL Code
        if (!glNameInput.dataset.listenerAttached) {
            glNameInput.addEventListener('input', handleGlNameInput);
            glNameInput.addEventListener('change', handleGlNameInput); // Crucial for datalist selection
            glNameInput.dataset.listenerAttached = 'true';
        }
        if (!glCodeInput.dataset.listenerAttached) {
            glCodeInput.addEventListener('input', handleGlCodeInput);
            glCodeInput.addEventListener('change', handleGlCodeInput); // Add change listener for consistency
            glCodeInput.dataset.listenerAttached = 'true';
        }

        if (!processButton.dataset.listenerAttached) {
            processButton.addEventListener('click', processGlReport);
            processButton.dataset.listenerAttached = 'true';
        }
        if (!searchInput.dataset.listenerAttached) {
            searchInput.addEventListener('input', filterGlReportTable);
            searchInput.dataset.listenerAttached = 'true';
        }
        if (!copyButton.dataset.listenerAttached) {
            copyButton.addEventListener('click', copyGlReportTable);
            copyButton.dataset.listenerAttached = 'true';
        }

        // Initial UI update and fetch GL names if a branch is pre-selected (e.g., from local storage)
        updateActgGlUI();
        if (branchInput.value.trim()) {
            fetchAndPopulateGlNames(branchInput.value.trim());
        }
    }

    // Register this sub-tab's initializer with the main application logic
    document.addEventListener('DOMContentLoaded', () => {
        registerTabInitializer('actgGl', initActgGlTab);
    });
})(); // End IIFE
