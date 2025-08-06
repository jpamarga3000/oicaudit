// js/tabs/operations_deposit_counterpart.js

(function() {
    // Guard to prevent multiple executions of this IIFE
    if (window.operationsDepositCounterpartTabInitialized) {
        return;
    }
    window.operationsDepositCounterpartTabInitialized = true; // Set flag for Deposit Counterpart
    console.log('Operations Deposit Counterpart Tab Initialized - Version 2025-07-16-ManualDateInput-v2'); // ADDED FOR DEBUGGING

    // Define the branch mappings for each area (reused from operations_aging_report.js for consistency)
    const areaBranchesMap = {
        'Area 1': [
            'BAUNGON', 'BULUA', 'CARMEN', 'COGON', 'EL SALVADOR',
            'ILIGAN', 'TALAKAG', 'YACAPIN'
        ],
        'Area 2': [
            'AGLAYAN', 'DON CARLOS', 'ILUSTRE', 'MANOLO', 'MARAMAG',
            'TORIL', 'VALENCIA'
        ],
        'Area 3': [
            'AGORA', 'BALINGASAG', 'BUTUAN', 'GINGOOG', 'PUERTO',
            'TAGBILARAN', 'TUBIGON', 'UBAY'
        ],
        'Consolidated': [ // This will be dynamically populated with ALL branches
            'AGLAYAN', 'AGORA', 'BALINGASAG', 'BAUNGON', 'BULUA', 'BUTUAN',
            'CARMEN', 'COGON', 'DON CARLOS', 'EL SALVADOR', 'GINGOOG', 'ILIGAN',
            'ILUSTRE', 'MANOLO', 'MARAMAG', 'PUERTO', 'TAGBILARAN', 'TALAKAG',
            'TORIL', 'TUBIGON', 'UBAY', 'VALENCIA', 'YACAPIN' // Added missing branches from the example list
        ]
    };

    // State variables for deposit counterpart requirements and report data
    let depositRequirementsData = []; // To store deposit counterpart configuration

    // Report data storage
    let memberBorrowersReportData = [];
    let detailsReportData = [];

    // Sorting state for new reports
    let memberBorrowersCurrentSortKey = 'LOANS_TOTAL_BALANCE'; // Default sort key
    let memberBorrowersCurrentSortDirection = 'desc'; // Default sort direction

    let detailsCurrentSortKey = 'ACCOUNT'; // Default sort key
    let detailsCurrentSortDirection = 'asc'; // Default sort direction

    // Mapping from GROUP code (from AGING CSV) to LOAN PRODUCT GROUP
    const LOAN_PRODUCT_GROUP_MAP_JS = {
        "1": "Additional Loan", "2": "Agricultural Loan", "3": "Business Recovery Loan",
        "4": "Commercial Loan", "5": "Financing Loan - Vehicle", "6": "Financing Loan - Motorcycle",
        "7": "Real Estate Loan", "8": "Receivable Financing", "9": "SME", "10": "Instant Loan",
        "11": "Loan Against PS", "12": "Loan Against TD", "13": "Micro-Enterprise Loan",
        "14": "Pension Loan", "15": "Petty Cash Loan", "16": "Providential Loan",
        "17": "Restructured Loan", "18": "Salary Loan", "19": "Salary Loan Plus",
        "20": "Show Money Loan", "21": "Spcl Prep - Clothing", "22": "Spcl Prep - PEI",
        "23": "Spcl Prep - Salary Bonus", "24": "Allotment Loan", "25": "Others",
        "26": "Check Discounting", "27": "Rice Loan", "28": "FASS Loan",
        "29": "Restructured - Real Estate", "30": "Restructured - Agriculture",
        "31": "Restructured - FASS loan", "32": "Restructured - Commercial",
        "33": "Restructured - Providential", "34": "Restructured - Petty Cash",
        "35": "Restructured - Salary Loan", "36": "Restructured - Special Loan",
        "37": "Restructured - SME", "38": "Restructured - Others"
    };

    // Mapping SVACC ACCNAMEs to Report Headers (for Deposits section of Member-Borrowers)
    const DEPOSIT_ACCNAME_TO_REPORT_COL_JS = {
        'Regular Savings': 'DEPOSITS_REGULAR_SAVINGS',
        'Share Capital': 'DEPOSITS_SHARE_CAPITAL',
        'ATM Savings': 'DEPOSITS_ATM',
        'Compulsory Savings Deposit': 'DEPOSITS_CSD',
        'Time Deposit -A': 'TIME_DEPOSITS_BALANCE',
        'Time Deposit -B': 'TIME_DEPOSITS_BALANCE',
        'Time Deposit -C': 'TIME_DEPOSITS_BALANCE',
        'Time Deposit - Maturity': 'TIME_DEPOSITS_BALANCE',
        'Time Deposit - Monthly': 'TIME_DEPOSITS_BALANCE',
    };

    /**
     * Helper function to format a number as currency (PHP).
     * @param {number} value - The number to format.
     * @returns {string} The formatted currency string.
     */
    function formatCurrency(value) {
        if (typeof value !== 'number' || isNaN(value)) {
            return '0.00';
        }
        return new Intl.NumberFormat('en-PH', { style: 'currency', currency: 'PHP' }).format(value);
    }

    /**
     * Helper to generate a simple UUID for client-side table rows.
     */
    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * Normalizes a product name for comparison. THIS MUST EXACTLY MATCH THE PYTHON BACKEND'S _normalize_product_name.
     * @param {string} name - The product name to normalize.
     * @returns {string} The normalized product name.
     */
    function normalizeProductName(name) {
        if (typeof name !== 'string' || name === null) {
            return "";
        }
        // This JavaScript version exactly mimics the Python regex and string operations
        // Python: re.sub(r'[^a-zA-Z0-9\s]', '', name).strip().upper().replace(' ', '')
        // 1. Remove non-alphanumeric characters except spaces
        let cleaned = name.replace(/[^a-zA-Z0-9\s]/g, '');
        // 2. Strip leading/trailing whitespace
        cleaned = cleaned.trim();
        // 3. Convert to uppercase
        cleaned = cleaned.toUpperCase();
        // 4. Remove all remaining spaces (this is the crucial part that was previously different)
        cleaned = cleaned.replace(/\s/g, ''); // Use \s to catch all whitespace, not just ' '
        return cleaned;
    }

    /**
     * Populates the Deposit Product dropdowns in the requirements table.
     */
    function populateDepositProductDropdown(selectElement, selectedProduct = '') {
        selectElement.innerHTML = '<option value="">Select Product</option>';
        for (const code in LOAN_PRODUCT_GROUP_MAP_JS) {
            const productName = LOAN_PRODUCT_GROUP_MAP_JS[code];
            const option = document.createElement('option');
            option.value = productName;
            option.textContent = productName;
            if (productName === selectedProduct) {
                option.selected = true;
            }
            selectElement.appendChild(option);
        }
    }


    // --- Deposit Counterpart Requirements Table Functions ---

    /**
     * Loads deposit counterpart requirements from the backend database.
     */
    async function loadDepositRequirements() {
        const col1Container = document.getElementById('depositRequirementsTableCol1');
        const col2Container = document.getElementById('depositRequirementsTableCol2');
        const saveButton = document.getElementById('saveDepositRequirementsButton');
        const addButton = document.getElementById('addRequirementRowButton');

        if (col1Container) {
            col1Container.innerHTML = '<p class="text-gray-500 text-center py-8">Loading deposit requirements...</p>';
        }
        if (col2Container) { // Clear second column as well
            col2Container.innerHTML = ''; // Will be populated if data exists
        }
        if (saveButton) saveButton.disabled = true;
        if (addButton) addButton.disabled = true;

        try {
            const response = await fetch(`${FLASK_API_BASE_URL}/get_default_deposit_requirements`);
            const result = await response.json();
            if (response.ok && result.data) {
                depositRequirementsData = result.data;
                renderDepositRequirementsTables(); // Call the new rendering function
            } else {
                depositRequirementsData = [];
                renderDepositRequirementsTables(); // Call the new rendering function
                showMessage(result.message || "No deposit requirements found. Add new rows.", "info", "", 3000);
            }
        } catch (error) {
            console.error("Error loading deposit requirements:", error);
            showMessage("Error loading deposit requirements. Backend might not be running or database not configured.", "error");
            depositRequirementsData = [];
            renderDepositRequirementsTables(); // Call the new rendering function
        } finally {
            if (saveButton) saveButton.disabled = (depositRequirementsData.length === 0);
            if (addButton) addButton.disabled = false;
        }
    }

    /**
     * Renders the editable tables for Deposit Counterpart Requirements into two columns.
     */
    function renderDepositRequirementsTables() {
        const col1Container = document.getElementById('depositRequirementsTableCol1');
        const col2Container = document.getElementById('depositRequirementsTableCol2');
        if (!col1Container || !col2Container) return;

        col1Container.innerHTML = ''; // Clear previous content
        col2Container.innerHTML = ''; // Clear previous content

        if (depositRequirementsData.length === 0) {
            col1Container.innerHTML = '<p class="text-gray-500 text-center py-8">No deposit requirements defined. Click "Add New Requirement" to start.</p>';
            return;
        }

        const chunkSize = Math.ceil(depositRequirementsData.length / 2);
        const dataCol1 = depositRequirementsData.slice(0, chunkSize);
        const dataCol2 = depositRequirementsData.slice(chunkSize);

        // Helper function to create and populate a single table
        const createTable = (data, container) => {
            if (data.length === 0) {
                container.innerHTML = '<p class="text-gray-500 text-center py-8">No data in this column.</p>';
                return;
            }

            const table = document.createElement('table');
            table.className = 'min-w-full bg-white border border-gray-300 rounded-lg shadow-md';
            table.innerHTML = `
                <thead>
                    <tr>
                        <th class="py-2 px-3 bg-gray-100 text-left text-xs font-semibold text-gray-700 uppercase border-b border-gray-300">LOAN PRODUCT</th>
                        <th class="py-2 px-3 bg-gray-100 text-left text-xs font-semibold text-gray-700 uppercase border-b border-gray-300">CONDITION</th>
                        <th class="py-2 px-3 bg-gray-100 text-left text-xs font-semibold text-gray-700 uppercase border-b border-gray-300">DETAILS</th>
                        <th class="py-2 px-3 bg-gray-100 text-center text-xs font-semibold text-gray-700 uppercase border-b border-gray-300">ACTIONS</th>
                    </tr>
                </thead>
                <tbody></tbody>
            `;
            const tbody = table.querySelector('tbody');

            data.forEach(item => {
                const loanProductSelect = document.createElement('select');
                loanProductSelect.className = 'select-field w-full text-xs';
                populateDepositProductDropdown(loanProductSelect, item.product);
                loanProductSelect.onchange = (event) => handleRequirementChange(event, item.id, 'product');

                const conditionSelect = document.createElement('select');
                conditionSelect.className = 'select-field w-full text-xs';
                conditionSelect.innerHTML = `
                    <option value="">Select Condition</option>
                    <option value="% of Total Deposit" ${item.condition === '% of Total Deposit' ? 'selected' : ''}>% of Total Deposit</option>
                    <option value="% of Loan Principal" ${item.condition === '% of Loan Principal' ? 'selected' : ''}>% of Loan Principal</option>
                    <option value="Specific Amount per Deposit" ${item.condition === 'Specific Amount per Deposit' ? 'selected' : ''}>Specific Amount per Deposit</option>
                    <option value="Number of Times in Principal" ${item.condition === 'Number of Times in Principal' ? 'selected' : ''}>Number of Times in Principal</option>
                `;
                conditionSelect.onchange = (event) => {
                    handleRequirementChange(event, item.id, 'condition');
                    renderDepositRequirementsTables(); // Re-render both tables to update details column based on new condition
                };

                const detailsDiv = document.createElement('div');
                detailsDiv.className = 'deposit-details-cell'; // New class for flex wrapping
                detailsDiv.innerHTML = getDetailsHtml(item);


                const row = tbody.insertRow();
                row.dataset.id = item.id;
                row.className = 'hover:bg-gray-50';
                
                row.insertCell().appendChild(loanProductSelect);
                row.insertCell().appendChild(conditionSelect);
                row.insertCell().appendChild(detailsDiv); // Append the div, not raw HTML

                const actionsCell = row.insertCell();
                actionsCell.className = 'py-1.5 px-3 text-xs text-gray-800 border-b border-gray-200 text-center';
                const deleteButton = document.createElement('button');
                deleteButton.className = 'text-red-500 hover:text-red-700 focus:outline-none';
                deleteButton.innerHTML = '<i class="fas fa-trash-alt"></i>';
                deleteButton.onclick = () => deleteRequirementRow(item.id);
                actionsCell.appendChild(deleteButton);
            });
            container.appendChild(table);
        };

        createTable(dataCol1, col1Container);
        createTable(dataCol2, col2Container);
    }

    /**
     * Generates the HTML for the "DETAILS" column based on the selected condition.
     * @param {Object} item - The requirement item data.
     * @returns {string} HTML string for the details inputs.
     */
    function getDetailsHtml(item) {
        let html = '';
        const dc = item.depositCounterpart || {}; // Ensure dc exists
        const id = item.id;

        switch (item.condition) {
            case '% of Total Deposit':
            case '% of Loan Principal':
                html = `
                    <input type="number" step="0.01" min="0" class="text-input-field w-24 text-xs text-center flex-shrink-0"
                        value="${dc.percentage !== undefined ? dc.percentage : ''}"
                        oninput="window.operationsDepositCounterpart.handleDetailsChange(event, '${id}', 'percentage')"> <span class="flex-shrink-0">%</span>
                `;
                // For "% of Total Deposit", also add a deposit type dropdown
                if (item.condition === '% of Total Deposit') {
                    html += `<select class="select-field w-full text-xs mt-1"
                        onchange="window.operationsDepositCounterpart.handleDetailsChange(event, '${id}', 'depositType')">
                        <option value="">Select Deposit Type</option>
                        <option value="All Deposits" ${dc.depositType === 'All Deposits' ? 'selected' : ''}>All Deposits</option>
                        <option value="Savings Deposit" ${dc.depositType === 'Savings Deposit' ? 'selected' : ''}>Savings Deposit</option>
                        <option value="Share Capital" ${dc.depositType === 'Share Capital' ? 'selected' : ''}>Share Capital</option>
                    </select>`;
                }
                break;
            case 'Specific Amount per Deposit':
                html = `
                    <span class="flex-shrink-0">Share:</span> <input type="number" step="0.01" min="0" class="text-input-field w-24 text-xs text-right flex-grow"
                        value="${dc.shareAmount !== undefined ? dc.shareAmount : ''}"
                        oninput="window.operationsDepositCounterpart.handleDetailsChange(event, '${id}', 'shareAmount')"><br/>
                    <span class="flex-shrink-0 mt-1">Savings:</span> <input type="number" step="0.01" min="0" class="text-input-field w-24 text-xs text-right flex-grow mt-1"
                        value="${dc.savingsAmount !== undefined ? dc.savingsAmount : ''}"
                        oninput="window.operationsDepositCounterpart.handleDetailsChange(event, '${id}', 'savingsAmount')">
                `;
                break;
            case 'Number of Times in Principal':
                html = `
                    <input type="number" step="0.01" min="0" class="text-input-field w-24 text-xs text-center flex-shrink-0"
                        value="${dc.numberOfTimes !== undefined ? dc.numberOfTimes : ''}"
                        oninput="window.operationsDepositCounterpart.handleDetailsChange(event, '${id}', 'numberOfTimes')"> <span class="flex-shrink-0">x</span>
                `;
                break;
            default:
                html = '<span class="gray-500">Select a condition</span>';
                break;
        }
        return html;
    }

    /**
     * Handles changes in the details fields (percentage, amount, etc.).
     * @param {Event} event - The input event.
     * @param {string} id - The ID of the row.
     * @param {string} fieldName - The specific field in depositCounterpart to update.
     */
    function handleDetailsChange(event, id, fieldName) {
        const item = depositRequirementsData.find(d => d.id === id);
        if (item) {
            item.depositCounterpart = item.depositCounterpart || {};
            if (event.target.type === 'number') {
                item.depositCounterpart[fieldName] = parseFloat(event.target.value) || 0;
            } else {
                item.depositCounterpart[fieldName] = event.target.value;
            }
        }
    }

    /**
     * Handles changes in the loan product or condition dropdowns.
     * @param {Event} event - The change event.
     * @param {string} id - The ID of the row.
     * @param {string} fieldName - 'product' or 'condition'.
     */
    function handleRequirementChange(event, id, fieldName) {
        const item = depositRequirementsData.find(d => d.id === id);
        if (item) {
            item[fieldName] = event.target.value;
            // If condition changes, reset depositCounterpart details
            if (fieldName === 'condition') {
                item.depositCounterpart = {}; 
            }
            renderDepositRequirementsTables(); // Re-render to reflect changes in details column
        }
    }


    /**
     * Adds a new row to the deposit requirements table.
     */
    function addRequirementRow() {
        const newId = generateUUID();
        depositRequirementsData.push({
            id: newId,
            product: '',
            condition: '',
            depositCounterpart: {}
        });
        renderDepositRequirementsTables(); // Re-render both tables
        const saveButton = document.getElementById('saveDepositRequirementsButton');
        if (saveButton) saveButton.disabled = (depositRequirementsData.length === 0);
    }

    /**
     * Deletes a row from the deposit requirements table.
     * @param {string} id - The ID of the row to delete.
     */
    async function deleteRequirementRow(id) {
        showMessage('Deleting requirement...', 'loading');
        try {
            const response = await fetch(`${FLASK_API_BASE_URL}/delete_deposit_requirement?id=${encodeURIComponent(id)}`, {
                method: 'DELETE'
            });
            const result = await response.json();
            if (response.ok) {
                depositRequirementsData = depositRequirementsData.filter(item => item.id !== id);
                renderDepositRequirementsTables(); // Re-render both tables
                showMessage(result.message, 'success');
            } else {
                showMessage(`Error: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('Fetch error:', error);
            showMessage(`An unexpected error occurred during deletion: ${error.message}.`, 'error');
        } finally {
            const saveButton = document.getElementById('saveDepositRequirementsButton');
            if (saveButton) saveButton.disabled = (depositRequirementsData.length === 0);
        }
    }

    /**
     * Saves deposit requirements to the backend database.
     */
    async function saveDepositRequirements() {
        showMessage('Saving deposit requirements...', 'loading');
        try {
            const response = await fetch(`${FLASK_API_BASE_URL}/save_deposit_requirements`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(depositRequirementsData)
            });
            const result = await response.json();
            if (response.ok) {
                showMessage(result.message, 'success');
            } else {
                showMessage(`Error: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('Fetch error:', error);
            showMessage(`An unexpected error occurred during saving: ${error.message}.`, 'error');
        } finally {
            const saveButton = document.getElementById('saveDepositRequirementsButton');
            if (saveButton) saveButton.disabled = (depositRequirementsData.length === 0);
        }
    }


    // --- Deposit Counterpart Report Functions ---

    /**
     * Populates the Branch dropdown based on the selected Area.
     * @param {string} selectedArea - The selected area (e.g., 'Area 1', 'Consolidated').
     */
    function populateBranchDropdown(selectedArea) {
        const branchInput = document.getElementById('depositReportBranch');
        // const dateInput = document.getElementById('depositReportDate'); // No longer needed for dropdown
        branchInput.innerHTML = '<option value="">Select Branch</option>';
        branchInput.disabled = true; // Disable branch until an area is selected or for consolidated
        // dateInput.innerHTML = ''; // No longer needed for dropdown
        // dateInput.disabled = true; // No longer needed for dropdown

        if (!selectedArea) {
            // If no area selected, keep branch disabled.
            updateDepositCounterpartReportUI();
            return;
        }

        // Add 'ALL' option if not 'Consolidated'
        if (selectedArea !== 'Consolidated') {
            const allOption = document.createElement('option');
            allOption.value = 'ALL';
            allOption.textContent = 'ALL';
            branchInput.appendChild(allOption);
        }

        const branchesForArea = areaBranchesMap[selectedArea];
        if (branchesForArea) {
            branchesForArea.forEach(branchName => {
                // Only add specific branches if not 'Consolidated'
                if (selectedArea !== 'Consolidated' || branchName === 'CONSOLIDATED') {
                    const option = document.createElement('option');
                    option.value = branchName;
                    option.textContent = branchName;
                    branchInput.appendChild(option);
                }
            });
            branchInput.disabled = false; // Enable branch dropdown
        } else {
            // If an invalid area is selected, keep branch disabled.
            console.warn(`Invalid area selected: '${selectedArea}'. No branches to populate.`);
        }
        updateDepositCounterpartReportUI(); // Update UI state after populating branches
    }

    /**
     * Validates if a string is in MM/DD/YYYY format.
     * @param {string} dateString - The date string to validate.
     * @returns {boolean} True if valid, false otherwise.
     */
    function isValidDate(dateString) {
        const regex = /^(0[1-9]|1[0-2])\/(0[1-9]|[1-2][0-9]|3[0-1])\/\d{4}$/;
        if (!regex.test(dateString)) {
            return false;
        }
        const parts = dateString.split('/');
        const month = parseInt(parts[0], 10);
        const day = parseInt(parts[1], 10);
        const year = parseInt(parts[2], 10);

        const date = new Date(year, month - 1, day);
        return date.getFullYear() === year && date.getMonth() + 1 === month && date.getDate() === day;
    }

    // Removed fetchAndPopulateDates as it's no longer needed for manual input

    /**
     * Updates the UI state for Deposit Counterpart Report, including button and actions visibility.
     */
    function updateDepositCounterpartReportUI() {
        const areaInput = document.getElementById('depositReportArea');
        const branchInput = document.getElementById('depositReportBranch');
        const dateInput = document.getElementById('depositReportDate'); // Now a text input
        const generateButton = document.getElementById('generateDepositReportButton');
        const overallActions = document.getElementById('depositReportOverallActions');
        const memberBorrowersTableExists = document.querySelector('#memberBorrowersReportTableContainer table');
        const detailsTableExists = document.querySelector('#detailsReportTableContainer table');

        const searchInput = document.getElementById('depositReportSearchInput');
        const copyButton = document.getElementById('copyAllDepositTablesButton');
        const downloadButton = document.getElementById('downloadDepositReportExcelButton');

        if (generateButton) {
            // Enable generate button only if a valid area/branch is selected AND a valid date is entered
            const isAreaOrBranchSelected = areaInput.value.trim() && (areaInput.value.trim() === 'Consolidated' || branchInput.value.trim());
            const isDateValid = isValidDate(dateInput.value.trim());
            generateButton.disabled = !(isAreaOrBranchSelected && isDateValid);
        }

        // Show/hide overall actions based on whether any report data exists
        const anyTableExists = memberBorrowersTableExists || detailsTableExists;
        if (overallActions) {
            if (anyTableExists) {
                overallActions.classList.remove('hidden');
            } else {
                overallActions.classList.add('hidden');
            }
        }

        if (searchInput) {
            searchInput.disabled = !anyTableExists;
            if (!anyTableExists) searchInput.value = '';
        }
        if (copyButton) {
            copyButton.disabled = !anyTableExists;
        }
        if (downloadButton) {
            downloadButton.disabled = !anyTableExists;
        }
    }

    /**
     * Renders the Member-Borrowers Report table.
     * @param {Array<Object>} data - The data for the table.
     */
    function renderMemberBorrowersTable(data) {
        const tableContainer = document.getElementById('memberBorrowersReportTableContainer');
        if (!tableContainer) return;

        tableContainer.innerHTML = '<p class="text-gray-500 text-center">Member-Borrower report will appear here after generation.</p>'; // Reset content

        if (!data || data.length === 0) {
            return; // Exit if no data
        }

        const table = document.createElement('table');
        table.className = 'min-w-full bg-white border border-gray-300 rounded-lg shadow-md';
        table.style.borderCollapse = 'separate'; // Crucial for sticky columns
        table.style.borderSpacing = '0'; // Remove space between cells

        const thead = document.createElement('thead');
        const tbody = document.createElement('tbody');

        const headers = [
            { key: 'NAME', label: 'NAME', align: 'left', sortable: true, sticky: 'sticky-col-mb-1' },
            { key: 'CID', label: 'CID', align: 'center', sortable: true, sticky: 'sticky-col-mb-2' },
            { key: 'BRANCH', label: 'BRANCH', align: 'left', sortable: true, sticky: '' }, // Not sticky
            { key: 'LOANS_PRINCIPAL', label: 'LOANS PRINCIPAL', align: 'right', sortable: true },
            { key: 'LOANS_CURRENT_BALANCE', label: 'LOANS CURRENT BALANCE', align: 'right', sortable: true },
            { key: 'LOANS_PAST_DUE_BALANCE', label: 'LOANS PAST DUE BALANCE', align: 'right', sortable: true },
            { key: 'LOANS_TOTAL_BALANCE', label: 'LOANS TOTAL BALANCE', align: 'right', sortable: true },
            { key: 'DEPOSITS_REGULAR_SAVINGS', label: 'DEPOSITS REGULAR SAVINGS', align: 'right', sortable: true },
            { key: 'DEPOSITS_SHARE_CAPITAL', label: 'DEPOSITS_SHARE_CAPITAL', align: 'right', sortable: true },
            { key: 'DEPOSITS_ATM', label: 'DEPOSITS ATM', align: 'right', sortable: true },
            { key: 'DEPOSITS_CSD', label: 'DEPOSITS CSD', align: 'right', sortable: true },
            { key: 'DEPOSITS_TOTAL', label: 'DEPOSITS TOTAL', align: 'right', sortable: true },
            { key: 'TOTAL_DC', label: 'TOTAL DC', align: 'right', sortable: true },
            { key: 'TIME_DEPOSITS_BALANCE', label: 'TIME DEPOSITS BALANCE', align: 'right', sortable: true },
            { key: 'TOTAL_TDC', label: 'TOTAL TDC', align: 'right', sortable: true },
            { key: 'DC_COMPLIANCE', label: 'DC COMPLIANCE (%)', align: 'center', sortable: true },
            { key: 'TDC_COMPLIANCE', label: 'TDC COMPLIANCE (%)', align: 'center', sortable: true },
            { key: 'ACCOUNTS_COUNT', label: 'ACCOUNTS COUNT', align: 'center', sortable: true }
        ];

        const headerRow = document.createElement('tr');
        headers.forEach(headerInfo => {
            const th = document.createElement('th');
            th.className = `py-3 px-4 bg-gray-100 text-${headerInfo.align} text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300`;
            if (headerInfo.sticky) th.classList.add(headerInfo.sticky);
            th.textContent = headerInfo.label;

            // Add sorting functionality
            if (headerInfo.sortable) {
                th.classList.add('cursor-pointer', 'hover:bg-gray-200');
                th.setAttribute('data-sort-key', headerInfo.key);
                th.addEventListener('click', () => sortMemberBorrowersTable(headerInfo.key));
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
                if (headerInfo.sticky) td.classList.add(headerInfo.sticky);
                
                let value;
                if (headerInfo.key === 'DC_COMPLIANCE' || headerInfo.key === 'TDC_COMPLIANCE') {
                    value = rowData[headerInfo.key]; // These are already percentages from backend
                    td.textContent = typeof value === 'number' ? `${value.toFixed(2)}%` : value;
                } else if (headerInfo.key === 'ACCOUNTS_COUNT') {
                    value = rowData[headerInfo.key];
                    td.textContent = value.toLocaleString();
                } else {
                    value = rowData[headerInfo.key];
                    td.textContent = value;
                }
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        tableContainer.appendChild(table);
    }

    /**
     * Sorts the Member-Borrowers table data.
     * @param {string} sortKey - The key to sort by.
     */
    function sortMemberBorrowersTable(sortKey) {
        let newDirection = 'asc';
        if (memberBorrowersCurrentSortKey === sortKey && memberBorrowersCurrentSortDirection === 'asc') {
            newDirection = 'desc';
        }
        memberBorrowersCurrentSortKey = sortKey;
        memberBorrowersCurrentSortDirection = newDirection;

        const sortedData = [...memberBorrowersReportData].sort((a, b) => {
            let valA = a[sortKey];
            let valB = b[sortKey];

            // Handle numeric values that come as formatted strings
            if (['LOANS_PRINCIPAL', 'LOANS_CURRENT_BALANCE', 'LOANS_PAST_DUE_BALANCE', 'LOANS_TOTAL_BALANCE',
                'DEPOSITS_REGULAR_SAVINGS', 'DEPOSITS_SHARE_CAPITAL', 'DEPOSITS_ATM', 'DEPOSITS_CSD', 'DEPOSITS_TOTAL',
                'TOTAL_DC', 'TIME_DEPOSITS_BALANCE', 'TOTAL_TDC'].includes(sortKey)) {
                
                // Assuming raw numeric values are also available for precise sorting, e.g., LOANS_PRINCIPAL_RAW
                // If not, parse the formatted string
                valA = parseFloat(String(a[sortKey + '_FORMATTED']).replace(/[₱,()]/g, '')) || 0;
                if (String(a[sortKey + '_FORMATTED']).includes('(')) valA *= -1; // Handle parentheses for negative
                
                valB = parseFloat(String(b[sortKey + '_FORMATTED']).replace(/[₱,()]/g, '')) || 0;
                if (String(b[sortKey + '_FORMATTED']).includes('(')) valB *= -1;
                
            } else if (['DC_COMPLIANCE', 'TDC_COMPLIANCE', 'ACCOUNTS_COUNT'].includes(sortKey)) {
                valA = parseFloat(valA) || 0;
                valB = parseFloat(valB) || 0;
            } else {
                valA = String(valA).toLowerCase();
                valB = String(valB).toLowerCase();
            }

            if (valA < valB) return newDirection === 'asc' ? -1 : 1;
            if (valA > valB) return newDirection === 'asc' ? 1 : -1;
            return 0;
        });

        renderMemberBorrowersTable(sortedData);
    }

    /**
     * Renders the Details Report table.
     * @param {Array<Object>} data - The data for the table.
     */
    function renderDetailsReportTable(data) {
        const tableContainer = document.getElementById('detailsReportTableContainer');
        if (!tableContainer) return;

        tableContainer.innerHTML = '<p class="text-gray-500 text-center">Details report will appear here after generation.</p>'; // Reset content

        if (!data || data.length === 0) {
            return; // Exit if no data
        }

        const table = document.createElement('table');
        table.className = 'min-w-full bg-white border border-gray-300 rounded-lg shadow-md';
        table.style.borderCollapse = 'separate'; // Crucial for sticky columns
        table.style.borderSpacing = '0'; // Remove space between cells

        const thead = document.createElement('thead');
        const tbody = document.createElement('tbody');

        const headers = [
            { key: 'NAME', label: 'NAME', align: 'left', sortable: true, sticky: 'sticky-col-details-1' },
            { key: 'CID', label: 'CID', align: 'center', sortable: true, sticky: 'sticky-col-details-2' },
            { key: 'ACCOUNT', label: 'ACCOUNT', align: 'left', sortable: true, sticky: 'sticky-col-details-3' },
            { key: 'PRINCIPAL', label: 'PRINCIPAL', align: 'right', sortable: true },
            { key: 'BALANCE', label: 'BALANCE', align: 'right', sortable: true },
            { key: 'DISBURSED', label: 'DISBURSED', align: 'center', sortable: true },
            { key: 'MATURITY', label: 'MATURITY', align: 'center', sortable: true },
            { key: 'PRODUCT', label: 'PRODUCT', align: 'left', sortable: true },
            { key: 'AGING', label: 'AGING', align: 'center', sortable: true },
            { key: 'DC_CONDITIONS', label: 'DC CONDITIONS', align: 'left', sortable: true },
            { key: 'DC_REQ', label: 'DC REQ', align: 'right', sortable: true }
        ];

        const headerRow = document.createElement('tr');
        headers.forEach(headerInfo => {
            const th = document.createElement('th');
            th.className = `py-3 px-4 bg-gray-100 text-${headerInfo.align} text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300`;
            if (headerInfo.sticky) th.classList.add(headerInfo.sticky);
            th.textContent = headerInfo.label;

            // Add sorting functionality
            if (headerInfo.sortable) {
                th.classList.add('cursor-pointer', 'hover:bg-gray-200');
                th.setAttribute('data-sort-key', headerInfo.key);
                th.addEventListener('click', () => sortDetailsTable(headerInfo.key));
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
                if (headerInfo.sticky) td.classList.add(headerInfo.sticky);
                
                let value;
                if (['PRINCIPAL', 'BALANCE', 'DC_REQ'].includes(headerInfo.key)) {
                    // Prefer _FORMATTED if available, otherwise format the raw value using frontend formatCurrency
                    value = rowData[headerInfo.key + '_FORMATTED'];
                    if (value === undefined || value === null || value === '') {
                        value = formatCurrency(rowData[headerInfo.key]); // Fallback to format raw number
                    }
                    td.textContent = value;
                } else {
                    value = rowData[headerInfo.key];
                    td.textContent = value;
                }
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        tableContainer.appendChild(table);
    }

    /**
     * Sorts the Details table data.
     * @param {string} sortKey - The key to sort by.
     */
    function sortDetailsTable(sortKey) {
        let newDirection = 'asc';
        if (detailsCurrentSortKey === sortKey && detailsCurrentSortDirection === 'asc') {
            newDirection = 'desc';
        }
        detailsCurrentSortKey = sortKey;
        detailsCurrentSortDirection = newDirection;

        const sortedData = [...detailsReportData].sort((a, b) => {
            let valA = a[sortKey];
            let valB = b[sortKey];

            // Handle numeric values that come as formatted strings
            if (['PRINCIPAL', 'BALANCE', 'DC_REQ'].includes(sortKey)) {
                // Assuming raw numeric values are also available for precise sorting, e.g., PRINCIPAL_RAW
                // If not, parse the formatted string
                valA = parseFloat(String(a[sortKey + '_FORMATTED']).replace(/[₱,()]/g, '')) || 0;
                if (String(a[sortKey + '_FORMATTED']).includes('(')) valA *= -1; // Handle parentheses for negative
                
                valB = parseFloat(String(b[sortKey + '_FORMATTED']).replace(/[₱,()]/g, '')) || 0;
                if (String(b[sortKey + '_FORMATTED']).includes('(')) valB *= -1;
                
            } else if (['DISBURSED', 'MATURITY'].includes(sortKey)) {
                valA = new Date(valA);
                valB = new Date(valB);
            } else {
                valA = String(valA).toLowerCase();
                valB = String(valB).toLowerCase();
            }

            if (valA < valB) return newDirection === 'asc' ? -1 : 1;
            if (valA > valB) return newDirection === 'asc' ? 1 : -1;
            return 0;
        });

        renderDetailsReportTable(sortedData);
    }

    /**
     * Handles the generation of the Deposit Counterpart Report.
     */
    async function generateDepositCounterpartReport() {
        const areaInput = document.getElementById('depositReportArea');
        const branchInput = document.getElementById('depositReportBranch');
        const dateInput = document.getElementById('depositReportDate');
        const generateButton = document.getElementById('generateDepositReportButton');

        const selectedArea = areaInput.value.trim();
        const selectedBranch = branchInput.value.trim();
        const reportDate = dateInput.value.trim();

        if (!(selectedArea || selectedBranch) || !isValidDate(reportDate)) { // Validate date using isValidDate
            showMessage('Please select Area/Branch and enter a valid Date (MM/DD/YYYY).', 'error');
            return;
        }

        if (generateButton) generateButton.disabled = true;
        showMessage('Generating Deposit Counterpart Report... This may take a moment.', 'loading');
        
        memberBorrowersReportTableContainer.innerHTML = '<p class="text-gray-500 text-center">Loading Member-Borrower report...</p>'; // Corrected variable name
        detailsReportTableContainer.innerHTML = '<p class="text-gray-500 text-center">Loading Details report...</p>'; // Corrected variable name
        
        memberBorrowersReportData = [];
        detailsReportData = [];

        try {
            // First, load the current deposit requirements from the DB
            await loadDepositRequirements(); // This will update `depositRequirementsData`

            const payload = {
                report_date: reportDate,
                deposit_requirements_data: depositRequirementsData,
                area: selectedArea, // NEW: Send area to backend
                branch: selectedBranch // NEW: Send branch to backend
            };

            const response = await fetch(`${FLASK_API_BASE_URL}/generate_deposit_counterpart_report`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload),
            });

            const result = await response.json();

            if (response.ok) {
                if (result.details_data && result.details_data.length > 0) {
                    detailsReportData = result.details_data;
                    renderDetailsReportTable(detailsReportData);
                } else {
                    renderDetailsReportTable([]);
                }

                if (result.member_borrowers_data && result.member_borrowers_data.length > 0) {
                    memberBorrowersReportData = result.member_borrowers_data;
                    renderMemberBorrowersTable(memberBorrowersReportData);
                } else {
                    renderMemberBorrowersTable([]);
                }
                
                showMessage(result.message || 'Deposit Counterpart Report generated successfully!', 'success');
            } else {
                showMessage(`Error: ${result.message}`, 'error');
                renderMemberBorrowersTable([]);
                renderDetailsReportTable([]);
            }
        } catch (error) {
            console.error('Fetch error:', error);
            showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
            renderMemberBorrowersTable([]);
            renderDetailsReportTable([]);
        } finally {
            if (generateButton) generateButton.disabled = false;
            updateDepositCounterpartReportUI();
        }
    }

    /**
     * Copies content of both Member-Borrowers and Details tables to clipboard.
     */
    function copyAllDepositTables() {
        const mbTable = document.querySelector('#memberBorrowersReportTableContainer table');
        const detailsTable = document.querySelector('#detailsReportTableContainer table');
        let combinedText = [];

        if (mbTable) {
            combinedText.push("MEMBER-BORROWERS REPORT\n");
            let rows = mbTable.querySelectorAll('tr');
            rows.forEach(row => {
                let rowData = Array.from(row.querySelectorAll('th, td')).map(cell => cell.innerText.trim().replace(/,/g, ''));
                combinedText.push(rowData.join('\t'));
            });
            combinedText.push("\n\n"); // Add spacing between tables
        }

        if (detailsTable) {
            combinedText.push("DETAILS REPORT\n");
            let rows = detailsTable.querySelectorAll('tr');
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
                showMessage('All table data copied to clipboard!', 'success', '', 2000);
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
     * Downloads the Deposit Counterpart Report as an Excel file.
     */
    async function downloadDepositReportExcel() {
        const areaInput = document.getElementById('depositReportArea');
        const branchInput = document.getElementById('depositReportBranch');
        const dateInput = document.getElementById('depositReportDate');

        const selectedArea = areaInput.value.trim();
        const selectedBranch = branchInput.value.trim();
        const reportDate = dateInput.value.trim();

        if (!(selectedArea || selectedBranch) || !isValidDate(reportDate)) { // Validate date using isValidDate
            showMessage('Please select Area/Branch and enter a valid Date (MM/DD/YYYY) for Excel download.', 'error');
            return;
        }

        showMessage('Generating Excel file... This may take a moment.', 'loading');

        try {
            const payload = {
                report_date: reportDate,
                deposit_requirements_data: depositRequirementsData,
                area: selectedArea, // NEW: Send area to backend
                branch: selectedBranch // NEW: Send branch to backend
            };

            const response = await fetch(`${FLASK_API_BASE_URL}/download_deposit_counterpart_excel`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                // Format filename: BRANCH_NAME DEPOSIT COUNTERPART - MM-DD-YYYY.xlsx
                const dateParts = reportDate.split('/'); // Assuming MM/DD/YYYY format
                const month = dateParts[0];
                const day = dateParts[1];
                const year = dateParts[2];
                
                let filenamePrefix = '';
                if (selectedArea === 'Consolidated') {
                    filenamePrefix = 'CONSOLIDATED';
                } else if (selectedArea.startsWith('Area')) {
                    filenamePrefix = selectedArea.toUpperCase().replace(' ', '_');
                } else {
                    filenamePrefix = selectedBranch.toUpperCase();
                }

                a.download = `${filenamePrefix} DEPOSIT COUNTERPART - ${month}-${day}-${year}.xlsx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                showMessage('Excel file downloaded successfully!', 'success');
            } else {
                const errorResult = await response.json();
                showMessage(`Error downloading Excel: ${errorResult.message}`, 'error');
            }
        } catch (error) {
            console.error('Download error:', error);
            showMessage(`An unexpected error occurred during Excel download: ${error.message}.`, 'error');
        }
    }

    /**
     * Filters both Deposit Counterpart tables based on search input.
     */
    function filterDepositCounterpartTables() {
        const searchInput = document.getElementById('depositReportSearchInput');
        const filter = searchInput.value.toLowerCase();
        
        // Filter Member-Borrowers table
        if (memberBorrowersReportData.length > 0) {
            const filteredMb = memberBorrowersReportData.filter(row => {
                return Object.values(row).some(value => String(value).toLowerCase().includes(filter));
            });
            renderMemberBorrowersTable(filteredMb);
        } else {
            renderMemberBorrowersTable([]);
        }

        // Filter Details table
        if (detailsReportData.length > 0) {
            const filteredDetails = detailsReportData.filter(row => {
                return Object.values(row).some(value => String(value).toLowerCase().includes(filter));
            });
            renderDetailsReportTable(filteredDetails);
        } else {
            renderDetailsReportTable([]);
        }
    }


    /**
     * Initializes the Deposit Counterpart tab: attaches event listeners and performs initial UI update.
     */
    function initOperationsDepositCounterpartTab() {
        console.log('Initializing Operations Deposit Counterpart Tab - Version 2025-07-16-ManualDateInput-v2'); // ADDED FOR DEBUGGING

        // Expose functions globally for HTML inline event handlers
        window.operationsDepositCounterpart = {
            handleDetailsChange,
            handleRequirementChange,
            addRequirementRow,
            deleteRequirementRow,
            saveDepositRequirements,
        };

        // Get elements for Deposit Counterpart Requirements config
        const addRequirementRowButton = document.getElementById('addRequirementRowButton');
        const saveDepositRequirementsButton = document.getElementById('saveDepositRequirementsButton');
        const depositRequirementsTableContainer = document.getElementById('depositRequirementsTableContainer');

        // Get elements for Deposit Counterpart Report criteria
        const depositReportAreaInput = document.getElementById('depositReportArea');
        const depositReportBranchInput = document.getElementById('depositReportBranch');
        const depositReportDateInput = document.getElementById('depositReportDate'); // Now a text input
        const generateDepositReportButton = document.getElementById('generateDepositReportButton');

        // Get elements for Deposit Counterpart Report actions
        const depositReportSearchInput = document.getElementById('depositReportSearchInput');
        const copyAllDepositTablesButton = document.getElementById('copyAllDepositTablesButton');
        const downloadDepositReportExcelButton = document.getElementById('downloadDepositReportExcelButton');
        const memberBorrowersReportTableContainer = document.getElementById('memberBorrowersReportTableContainer');
        const detailsReportTableContainer = document.getElementById('detailsReportTableContainer');


        // Clear report containers on tab initialization
        if (depositRequirementsTableContainer) {
            depositRequirementsTableContainer.innerHTML = '<p class="text-gray-500 text-center py-8">Loading deposit requirements...</p>';
        }
        if (memberBorrowersReportTableContainer) {
            memberBorrowersReportTableContainer.innerHTML = '<p class="text-gray-500 text-center">Member-Borrower report will appear here after generation.</p>';
        }
        if (detailsReportTableContainer) {
            detailsReportTableContainer.innerHTML = '<p class="text-gray-500 text-center">Details report will appear here after generation.</p>';
        }

        // Attach event listeners for Deposit Counterpart Requirements
        if (addRequirementRowButton && !addRequirementRowButton.dataset.listenerAttached) {
            addRequirementRowButton.addEventListener('click', addRequirementRow);
            addRequirementRowButton.dataset.listenerAttached = 'true';
        }
        if (saveDepositRequirementsButton && !saveDepositRequirementsButton.dataset.listenerAttached) {
            saveDepositRequirementsButton.addEventListener('click', saveDepositRequirements);
            saveDepositRequirementsButton.dataset.listenerAttached = 'true';
        }

        // Attach event listeners for Deposit Counterpart Report criteria
        if (depositReportAreaInput && !depositReportAreaInput.dataset.listenerAttached) {
            depositReportAreaInput.addEventListener('change', (event) => {
                populateBranchDropdown(event.target.value);
                updateDepositCounterpartReportUI(); // Update UI after area change
            });
            depositReportAreaInput.dataset.listenerAttached = 'true';
        }
        if (depositReportBranchInput && !depositReportBranchInput.dataset.listenerAttached) {
            depositReportBranchInput.addEventListener('change', () => {
                updateDepositCounterpartReportUI(); // Update UI after branch change
            });
            depositReportBranchInput.dataset.listenerAttached = 'true';
        }
        // NEW: Event listener for manual date input
        if (depositReportDateInput && !depositReportDateInput.dataset.listenerAttached) {
            depositReportDateInput.addEventListener('input', () => {
                updateDepositCounterpartReportUI(); // Update UI on every input change
            });
            depositReportDateInput.dataset.listenerAttached = 'true';
        }
        if (generateDepositReportButton && !generateDepositReportButton.dataset.listenerAttached) {
            generateDepositReportButton.addEventListener('click', generateDepositCounterpartReport);
            generateDepositReportButton.dataset.listenerAttached = 'true';
        }

        // Attach event listeners for Deposit Counterpart Report actions
        if (depositReportSearchInput && !depositReportSearchInput.dataset.listenerAttached) {
            depositReportSearchInput.addEventListener('input', filterDepositCounterpartTables);
            depositReportSearchInput.dataset.listenerAttached = 'true';
        }
        if (copyAllDepositTablesButton && !copyAllDepositTablesButton.dataset.listenerAttached) {
            copyAllDepositTablesButton.addEventListener('click', copyAllDepositTables);
            copyAllDepositTablesButton.dataset.listenerAttached = 'true';
        }
        if (downloadDepositReportExcelButton && !downloadDepositReportExcelButton.dataset.listenerAttached) {
            downloadDepositReportExcelButton.addEventListener('click', downloadDepositReportExcel);
            downloadDepositReportExcelButton.dataset.listenerAttached = 'true';
        }

        // Initial load of deposit requirements when the tab is opened
        loadDepositRequirements();
        
        // --- INITIALIZATION LOGIC FOR AREA AND BRANCH (NO DATE POPULATION) ---
        // 1. Set initial area if not already set (e.g., from localStorage)
        let initialArea = depositReportAreaInput.value.trim();
        if (!initialArea) {
            initialArea = Object.keys(areaBranchesMap)[0]; // Default to the first area
            if (initialArea) {
                depositReportAreaInput.value = initialArea;
            }
        }

        // 2. Populate branches based on the determined initial area
        populateBranchDropdown(initialArea);

        // 3. Set initial branch value (if any was stored or if a default is desired)
        let initialBranch = depositReportBranchInput.value.trim();
        if (!initialBranch && initialArea && initialArea !== 'Consolidated' && areaBranchesMap[initialArea] && areaBranchesMap[initialArea].length > 0) {
             initialBranch = areaBranchesMap[initialArea][0]; // Set to the first branch in the area
             depositReportBranchInput.value = initialBranch;
        }
        // --- END INITIALIZATION LOGIC ---
        
        updateDepositCounterpartReportUI(); // Final UI update after all initial selections
    }

    // Register this sub-tab's initializer with the main application logic
    registerTabInitializer('operationsDepositCounterpart', initOperationsDepositCounterpartTab);

})();
