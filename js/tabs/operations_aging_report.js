// js/tabs/operations_aging_report.js

(function() { // Start IIFE
    // Guard to prevent multiple executions of this IIFE
    if (window.operationsAgingReportTabInitialized) {
        return;
    }
    window.operationsAgingReportTabInitialized = true;

    // Expose nameCidMap globally so other aging report files can access it
    window.nameCidMap = new Map(); // Key: Name, Value: CID
    let agingReportData = {}; // To store the full report data {headers, full_month_years, data} for filtering
    let provisionsReportData = { per_accounts_data: [], per_member_data: [] }; // To store data for the new section
    let topBorrowersReportData = []; // To store data for the new Top Borrowers section
    let newLoansReportData = []; // To store data for the new loans report

    // Track current sorting state for New Loans table
    let newLoansCurrentSortKey = 'PRINCIPAL';
    let newLoansCurrentSortDirection = 'desc'; // Default sort by Principal highest to lowest

    // Track current sorting state for New Loans Details modal table
    let newLoansDetailsCurrentSortKey = 'DATE'; // Changed default sort key to DATE
    let newLoansDetailsCurrentSortDirection = 'asc';

    // Define the branch mappings for each area
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
            'AGORA', 'BALINGASAG', 'BUTUAN', 'BAYUGAN', 'GINGOOG', 'PUERTO',
            'TAGBILARAN', 'TUBIGON', 'UBAY'
        ],
        'Consolidated': [ // This will be dynamically populated with ALL branches
            'AGLAYAN', 'AGORA', 'BALINGASAG', 'BAUNGON', 'BULUA', 'BUTUAN',
            'CARMEN', 'COGON', 'DON CARLOS', 'EL SALVADOR', 'GINGOOG', 'ILIGAN',
            'ILUSTRE', 'MANOLO', 'MARAMAG', 'PUERTO', 'TAGBILARAN', 'TALAKAG',
            'TORIL', 'TUBIGON', 'UBAY', 'VALENCIA', 'YACAPIN'
        ]
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

    // Declare functions at the top level of the IIFE to ensure hoisting and scope availability
    // Use const named function expressions for clarity and better debugging in stack traces
    const processOperationsAgingReport = function() {
        const areaInput = document.getElementById('agingArea');
        const branchInput = document.getElementById('agingBranch');
        const dateInput = document.getElementById('agingDate'); // NEW: Get date input
        const nameInput = document.getElementById('agingName');
        const cidInput = document.getElementById('agingCid');
        const processButton = document.getElementById('processAgingReportButton');
        const reportContainer = document.getElementById('agingReportTableContainer');

        const area = areaInput.value.trim();
        const branch = branchInput.value.trim();
        const selectedDate = dateInput.value.trim(); // NEW: Get selected date
        const name = nameInput.value.trim();
        const cid = cidInput.value.trim();

        if (!branch || !selectedDate || !name || !cid) { // NEW: selectedDate is now required
            showMessage('Please select a Branch, Date, Name, and ensure CID is autofilled.', 'error');
            return;
        }

        if (processButton) processButton.disabled = true;
        showMessage('Generating Aging History... This may take a moment.', 'loading');
        reportContainer.innerHTML = '<p class="text-gray-500 text-center">Aging history table will appear here after generation.</p>';
        agingReportData = {}; // Clear stored data on new processing

        const formData = new FormData();
        formData.append('branch', branch);
        formData.append('cid', cid);
        formData.append('selected_date', selectedDate); // NEW: Send selectedDate to backend

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
    }; // Note the semicolon here for function expression

    const generateProvisionsReport = function() { // Changed to const named function expression
        const branchInput = document.getElementById('agingBranch'); // Use the main branch input
        const dateInput = document.getElementById('agingDate'); // NEW: Get date input
        const monthInput = document.getElementById('provisionMonth');
        const yearInput = document.getElementById('provisionYear');
        const agingInput = document.getElementById('provisionAging');
        const generateButton = document.getElementById('generateProvisionsReportButton');
        const perAccountsTableContainer = document.getElementById('perAccountsTableContainer');
        const perMemberTableContainer = document.getElementById('perMemberTableContainer');
        const areaInput = document.getElementById('agingArea'); // Get area input

        const area = areaInput.value.trim(); // Get area value
        const branch = branchInput.value.trim();
        const selectedDate = dateInput.value.trim(); // NEW: Get selected date
        const selectedMonth = parseInt(monthInput.value);
        const selectedYear = parseInt(yearInput.value);
        const selectedAgingCategory = agingInput.value.trim();

        // Check if Consolidated/ALL is selected, then month, year, aging are not required
        const isConsolidatedOrAll = area === 'Consolidated' || branch === 'ALL';

        if (!area || !branch || !selectedDate || (!isConsolidatedOrAll && (isNaN(selectedMonth) || isNaN(selectedYear) || !selectedAgingCategory))) { // NEW: selectedDate is now required
            showMessage('Please select Area, Branch, Date, Month, Year, and Aging for Provisions Report (Month, Year, Aging are not required for Consolidated/ALL branches).', 'error');
            return;
        }

        if (generateButton) generateButton.disabled = true;
        showMessage('Generating Provisions Report... This may take a moment.', 'loading');
        
        perAccountsTableContainer.innerHTML = '<h5 class="text-lg font-semibold text-gray-700 mb-2 p-2">PER ACCOUNTS</h5><p class="text-gray-500 text-center">Per Accounts report will appear here.</p>';
        perMemberTableContainer.innerHTML = '<h5 class="text-lg font-semibold text-gray-700 mb-2 p-2">PER MEMBER</h5><p class="text-gray-500 text-center">Per Member report will appear here.</p>';
        provisionsReportData = { per_accounts_data: [], per_member_data: [] }; // Clear stored data


        const formData = new FormData();
        formData.append('area', area); // Send area to backend
        formData.append('branch', branch);
        formData.append('selected_date', selectedDate); // NEW: Send selectedDate to backend
        // Only append month, year, aging if not Consolidated/ALL
        if (!isConsolidatedOrAll) {
            formData.append('selected_month', selectedMonth);
            formData.append('selected_year', selectedYear);
            formData.append('selected_aging_category', selectedAgingCategory);
        }

        fetch(`${FLASK_API_BASE_URL}/get_accounts_contribute_to_provisions_report`, {
            method: 'POST',
            body: formData,
        })
        .then(response => { // Capture response here
            if (!response.ok) {
                return response.json().then(errorData => { throw new Error(errorData.message || 'Unknown error'); });
            }
            return response.json();
        })
        .then(result => {
            // result is now the parsed JSON from a successful response
            if (result.data && (result.data.per_accounts_data.length > 0 || result.data.per_member_data.length > 0)) {
                provisionsReportData.per_accounts_data = result.data.per_accounts_data;
                provisionsReportData.per_member_data = result.data.per_member_data;
                renderPerAccountsTable(provisionsReportData.per_accounts_data, selectedMonth, selectedYear);
                renderPerMemberTable(provisionsReportData.per_member_data, selectedYear); // Pass selectedYear
                showMessage(result.message || 'Provisions Report generated successfully!', 'success');
            } else {
                renderPerAccountsTable([], selectedMonth, selectedYear); // Render empty
                renderPerMemberTable([], selectedYear); // Render empty
                showMessage(result.message || 'No data found for the specified provisions criteria.', 'info');
            }

        })
        .catch(error => {
            console.error('Fetch error:', error);
            showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
            provisionsReportData = { per_accounts_data: [], per_member_data: [] };
            renderPerAccountsTable([], selectedMonth, selectedYear);
            renderPerMemberTable([], selectedYear);
        })
        .finally(() => {
            if (generateButton) generateButton.disabled = false;
            updateProvisionsReportUI();
        });
    }; // Note the semicolon here for function expression


    /**
     * Populates the Branch dropdown based on the selected Area.
     * @param {string} selectedArea - The selected area ('Area 1', 'Area 2', 'Area 3', 'Consolidated').
     */
    function populateBranchDropdown(selectedArea) {
        const branchDropdown = document.getElementById('agingBranch');
        const dateDropdown = document.getElementById('agingDate'); // NEW: Get date dropdown
        const nameInput = document.getElementById('agingName'); // Get Name input
        const cidInput = document.getElementById('agingCid'); // Get CID input

        // Clear current options except the "Select Branch" placeholder
        branchDropdown.innerHTML = '<option value="">Select Branch</option>';
        dateDropdown.innerHTML = '<option value="">Select Date</option>'; // NEW: Clear date dropdown
        dateDropdown.disabled = true; // NEW: Disable date dropdown by default

        let branchesToShow = [];

        if (selectedArea === 'Consolidated') {
            // If Consolidated, the branch dropdown should be disabled and only have "Select Branch"
            branchDropdown.disabled = true;
            branchDropdown.value = ''; // Reset branch selection
            // Disable Name and CID inputs for Consolidated
            if (nameInput) nameInput.disabled = true;
            if (cidInput) cidInput.disabled = true;
            nameInput.value = ''; // Clear Name/CID
            cidInput.value = '';
            return; // Exit here, no "ALL" option needed
        } else if (areaBranchesMap[selectedArea]) {
            // Add an "ALL" option at the top of the specific area list
            const allOption = document.createElement('option');
            allOption.value = 'ALL';
            allOption.textContent = 'ALL';
            branchDropdown.appendChild(allOption);

            branchesToShow = areaBranchesMap[selectedArea];
            // Enable Name and CID inputs for specific areas
            if (nameInput) nameInput.disabled = false;
            if (cidInput) cidInput.disabled = false;
        } else {
            // If no area selected, disable branch, name, and CID inputs
            branchDropdown.disabled = true;
            if (nameInput) nameInput.disabled = true;
            if (cidInput) cidInput.disabled = true;
            nameInput.value = ''; // Clear Name/CID
            cidInput.value = '';
        }
        
        branchesToShow.forEach(branchName => {
            const option = document.createElement('option');
            option.value = branchName;
            option.textContent = branchName;
            branchDropdown.appendChild(option);
        });

        // Enable or disable branch dropdown
        branchDropdown.disabled = selectedArea === '';
        branchDropdown.value = ''; // Reset branch selection
    }

    /**
     * Populates the Date dropdown based on the selected Area and Branch.
     * @param {string} area - The selected area.
     * @param {string} branch - The selected branch.
     */
    function populateDateDropdown(area, branch) {
        const dateDropdown = document.getElementById('agingDate');
        dateDropdown.innerHTML = '<option value="">Select Date</option>'; // Clear previous options
        dateDropdown.disabled = true; // Disable until dates are loaded

        if (!area || !branch || branch === 'ALL' || area === 'Consolidated') {
            console.log('No specific area/branch selected, or "ALL"/"Consolidated" selected. Skipping date load.');
            return;
        }

        showMessage('Loading Dates...', 'info');

        fetch(`${FLASK_API_BASE_URL}/get_unique_aging_dates?area=${encodeURIComponent(area)}&branch=${encodeURIComponent(branch)}`)
            .then(response => {
                if (!response.ok) {
                    return response.json().then(errorData => { throw new Error(errorData.message || 'Unknown error'); });
                }
                return response.json();
            })
            .then(result => {
                if (result.data && Array.isArray(result.data) && result.data.length > 0) {
                    result.data.forEach(dateStr => {
                        const option = document.createElement('option');
                        option.value = dateStr;
                        option.textContent = dateStr;
                        dateDropdown.appendChild(option);
                    });
                    dateDropdown.disabled = false; // Enable dropdown once populated
                    showMessage('Dates loaded successfully.', 'success', '', 1500);
                } else {
                    showMessage('No unique dates found for this branch/area.', 'info', '', 2000);
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
                showMessage(`An unexpected error occurred while loading dates: ${error.message}`, 'error');
            });
    }


    /**
     * Loads Names and CIDs from the backend based on the selected area and branch.
     * Populates window.nameCidMap and the agingNamesDatalist.
     * @param {string} area - The selected area.
     * @param {string} branch - The selected branch name.
     * @param {string} selectedDate - The selected date (MM/DD/YYYY).
     */
    function loadNamesAndCids(area, branch, selectedDate) { // Updated signature
        const namesDatalist = document.getElementById('agingNamesDatalist');
        namesDatalist.innerHTML = ''; // Clear previous options
        window.nameCidMap.clear(); // Use window.nameCidMap

        // Only load names/CIDs if a specific branch and date are selected
        if (!branch || branch === 'ALL' || area === 'Consolidated' || !selectedDate) {
            console.log('No specific branch or date selected, or "ALL"/"Consolidated" selected, skipping names and CIDs load for Aging Report.');
            return;
        }

        showMessage('Loading Names and CIDs...', 'info');

        fetch(`${FLASK_API_BASE_URL}/get_aging_names_and_cids?area=${encodeURIComponent(area)}&branch=${encodeURIComponent(branch)}&selected_date=${encodeURIComponent(selectedDate)}`)
            .then(response => { // Capture response here
                if (!response.ok) {
                    return response.json().then(errorData => { throw new Error(errorData.message || 'Unknown error'); });
                }
                return response.json();
            })
            .then(result => {
                // result is now the parsed JSON from a successful response
                if (result.data && Array.isArray(result.data)) {
                    // Sort by name alphabetically before populating datalist
                    result.data.sort((a, b) => (a.NAME || '').localeCompare(b.NAME || ''));

                    result.data.forEach(item => {
                        const name = item.NAME ? String(item.NAME).trim() : '';
                        const cid = item.CID ? String(item.CID).trim() : '';

                        if (name) { // Only add if name is not empty
                            window.nameCidMap.set(name, cid); // Use window.nameCidMap
                            const option = document.createElement('option');
                            option.value = name;
                            namesDatalist.appendChild(option);
                        }
                    });
                    showMessage('Names and CIDs loaded successfully.', 'success', '', 1500);
                } else {
                    showMessage('No Names and CIDs data found for this branch/date.', 'info', '', 2000);
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
                showMessage(`An unexpected error occurred while loading Names and CIDs: ${error.message}`, 'error');
            })
            .finally(() => {
                updateOperationsAgingReportUI();
                updateProvisionsReportUI(); // Update UI for the new section as well
                updateTopBorrowersReportUI(); // Update UI for top borrowers section
                updateNewLoansReportUI(); // Update UI for new loans section
            });
    }

    /**
     * Fetches and displays the summary data (Current, Past Due, Total, As of Date).
     * @param {string} area - The selected area.
     * @param {string} branch - The selected branch name.
     * @param {string} selectedDate - The selected date (MM/DD/YYYY).
     */
    function fetchAndDisplaySummary(area, branch, selectedDate) { // Updated signature
        const totalCurrentBalanceElement = document.getElementById('totalCurrentBalance');
        const totalPastDueElement = document.getElementById('totalPastDue');
        const totalBothDueElement = document.getElementById('totalBothDue');
        const agingReportAsOfDateElement = document.getElementById('agingReportAsOfDate'); // For main report title
        const agingSummaryAsOfDateElement = document.getElementById('agingSummaryAsOfDate'); // For Summary Totals header
        const currentAccountsCountElement = document.getElementById('currentAccountsCount');
        const pastDueAccountsCountElement = document.getElementById('pastDueAccountsCount');
        const totalAccountsCountElement = document.getElementById('totalAccountsCount');
        const delinquencyRateElement = document.getElementById('delinquencyRate');
        const provision1To365DaysBalanceElement = document.getElementById('provision1To365DaysBalance');
        const provision1To365DaysAccountsCountElement = document.getElementById('provision1To365DaysAccountsCount');
        const provisionOver365DaysBalanceElement = document.getElementById('provisionOver365DaysBalance');
        const provisionOver365DaysAccountsCountElement = document.getElementById('provisionOver365DaysAccountsCount');
        const totalProvisionsElement = document.getElementById('totalProvisions');


        // Reset display
        totalCurrentBalanceElement.textContent = formatCurrency(0);
        totalPastDueElement.textContent = formatCurrency(0);
        totalBothDueElement.textContent = formatCurrency(0);
        agingReportAsOfDateElement.textContent = ''; // Clear As of Date
        agingSummaryAsOfDateElement.textContent = ''; // Clear As of Date
        currentAccountsCountElement.textContent = 'Accounts: 0';
        pastDueAccountsCountElement.textContent = 'Accounts: 0';
        totalAccountsCountElement.textContent = 'Accounts: 0';
        delinquencyRateElement.textContent = '0.00%';
        provision1To365DaysBalanceElement.textContent = formatCurrency(0);
        provision1To365DaysAccountsCountElement.textContent = 'Accounts: 0';
        provisionOver365DaysBalanceElement.textContent = formatCurrency(0);
        provisionOver365DaysAccountsCountElement.textContent = 'Accounts: 0';
        totalProvisionsElement.textContent = 'Total Provisions: 0.00';


        // Always attempt to fetch summary if area or branch (including 'ALL' or 'Consolidated') is selected.
        // The backend `get_aging_summary_data` is robust to handle these.
        if (!area && !branch) { // Only skip if both are empty
            console.log('No area or branch selected, skipping summary data fetch.');
            return;
        }

        // NEW: If a specific branch is selected, but no date, skip summary.
        // If 'Consolidated' or 'ALL', date is not strictly required for summary as backend will find latest.
        if ((branch && branch !== 'ALL' && area !== 'Consolidated') && !selectedDate) {
            console.log('Specific branch selected but no date, skipping summary data fetch.');
            return;
        }


        fetch(`${FLASK_API_BASE_URL}/get_aging_summary_data?area=${encodeURIComponent(area)}&branch=${encodeURIComponent(branch)}&selected_date=${encodeURIComponent(selectedDate || '')}`)
            .then(response => { // Capture response here
                if (!response.ok) {
                    return response.json().then(errorData => { throw new Error(errorData.message || 'Unknown error'); });
                }
                return response.json();
            })
            .then(result => {
                // result is now the parsed JSON from a successful response
                if (result.data) {
                    totalCurrentBalanceElement.textContent = formatCurrency(result.data["TOTAL CURRENT BALANCE"]);
                    totalPastDueElement.textContent = formatCurrency(result.data["TOTAL PAST DUE"]);
                    totalBothDueElement.textContent = formatCurrency(result.data["TOTAL Both Current and Past Due"]);
                    
                    // Format account counts with commas
                    currentAccountsCountElement.textContent = `Accounts: ${result.data["CURRENT_ACCOUNTS_COUNT"].toLocaleString()}`;
                    pastDueAccountsCountElement.textContent = `Accounts: ${result.data["PAST_DUE_ACCOUNTS_COUNT"].toLocaleString()}`;
                    totalAccountsCountElement.textContent = `Accounts: ${result.data["TOTAL_ACCOUNTS_COUNT"].toLocaleString()}`;

                    delinquencyRateElement.textContent = `${result.data["DELINQUENCY_RATE"].toFixed(2)}%`;
                    provision1To365DaysBalanceElement.textContent = formatCurrency(result.data["PROVISION_1_365_DAYS_BALANCE"]);
                    provision1To365DaysAccountsCountElement.textContent = `Accounts: ${result.data["PROVISION_1_365_DAYS_ACCOUNTS_COUNT"].toLocaleString()}`;
                    provisionOver365DaysBalanceElement.textContent = formatCurrency(result.data["PROVISION_OVER_365_DAYS_BALANCE"]);
                    provisionOver365DaysAccountsCountElement.textContent = `Accounts: ${result.data["PROVISION_OVER_365_DAYS_ACCOUNTS_COUNT"].toLocaleString()}`;
                    totalProvisionsElement.textContent = `Total Provisions: ${formatCurrency(result.data["TOTAL_PROVISIONS"])}`;


                    console.log("AS OF DATE received from backend:", result.data["AS OF DATE"]); // DEBUG LOG

                    if (result.data["AS OF DATE"]) {
                        // Parse the MM/DD/YYYY date string
                        const dateParts = result.data["AS OF DATE"].split('/'); // MM/DD/YYYY
                        // Month is 0-indexed in JavaScript Date object
                        const date = new Date(dateParts[2], dateParts[0] - 1, dateParts[1]);
                        
                        // Format as "MonthName DD,YYYY"
                        const options = { month: 'long', day: 'numeric', year: 'numeric' };
                        const formattedDate = date.toLocaleDateString('en-US', options);

                        agingReportAsOfDateElement.textContent = `(As of ${formattedDate})`;
                        agingSummaryAsOfDateElement.textContent = `(As of ${formattedDate})`; // Updated to use the actual date
                    } else {
                        agingReportAsOfDateElement.textContent = `(As of N/A)`;
                        agingSummaryAsOfDateElement.textContent = `(As of N/A)`;
                    }
                } else {
                    console.error('Failed to fetch summary data:', result.message || 'Unknown error');
                    showMessage('Failed to load summary data.', 'error', '', 2000);
                }
            })
            .catch(error => {
                console.error('Error fetching summary data:', error);
                showMessage(`Error fetching summary data: ${error.message}`, 'error', '', 2000);
            });
    }

    /**
     * Renders the aging legend.
     */
    function renderAgingLegend() {
        const legendContainer = document.getElementById('agingLegendContainer');
        if (!legendContainer) return;

        // Modified to display legend items horizontally
        legendContainer.innerHTML = `
            <h5 class="text-lg font-semibold text-gray-700 mb-2 p-2">AGING LEGEND</h5>
            <div class="flex flex-wrap gap-x-4 gap-y-2 text-gray-600">
                <span class="flex items-center"><span class="font-bold aging-0 mr-1">0</span>: Current</span>
                <span class="flex items-center"><span class="font-bold aging-1 mr-1">1</span>: 1-30 Days Past Due</span>
                <span class="flex items-center"><span class="font-bold aging-2 mr-1">2</span>: 31-60 Days Past Due</span>
                <span class="flex items-center"><span class="font-bold aging-3 mr-1">3</span>: 61-90 Days Past Due</span>
                <span class="flex items-center"><span class="font-bold aging-4 mr-1">4</span>: 91-120 Days Past Due</span>
                <span class="flex items-center"><span class="font-bold aging-5 mr-1">5</span>: 121-180 Days Past Due</span>
                <span class="flex items-center"><span class="font-bold aging-6 mr-1">6</span>: 181-365 Days Past Due</span>
                <span class="flex items-center"><span class="font-bold aging-7 mr-1">7</span>: Over 365 Days Past Due</span>
            </div>
        `;
    }


    /**
     * Initializes the Operations Aging Report sub-tab. This function is called when the tab is opened.
     * It sets up initial UI states, loads persisted data, and attaches event listeners.
     */
    function initOperationsAgingReportTab() {
        console.log('Initializing Operations Aging Report Tab...');

        // --- Get UI Elements ---
        const agingAreaInput = document.getElementById('agingArea');
        const branchInput = document.getElementById('agingBranch');
        const dateInput = document.getElementById('agingDate'); // NEW: Get date input
        const nameInput = document.getElementById('agingName');
        const cidInput = document.getElementById('agingCid');
        const processButton = document.getElementById('processAgingReportButton');
        const searchInput = document.getElementById('agingSearchInput');
        const copyButton = document.getElementById('copyAgingReportTableButton');
        const reportContainer = document.getElementById('agingReportTableContainer');

        const provisionMonthInput = document.getElementById('provisionMonth');
        const provisionYearInput = document.getElementById('provisionYear');
        const provisionAgingInput = document.getElementById('provisionAging');
        const generateProvisionsButton = document.getElementById('generateProvisionsReportButton');
        const provisionsSearchInput = document.getElementById('provisionsSearchInput');
        const copyProvisionsButton = document.getElementById('copyProvisionsReportTablesButton');
        const perAccountsTableContainer = document.getElementById('perAccountsTableContainer');
        const perMemberTableContainer = document.getElementById('perMemberTableContainer');

        const topBorrowersStatusInput = document.getElementById('topBorrowersStatus');
        const generateTopBorrowersButton = document.getElementById('generateTopBorrowersReportButton');
        const topBorrowersSearchInput = document.getElementById('topBorrowersSearchInput');
        const copyTopBorrowersButton = document.getElementById('copyTopBorrowersTableButton');
        const topBorrowersTableContainer = document.getElementById('topBorrowersTableContainer');

        const newLoansYearInput = document.getElementById('newLoansYear');
        const generateNewLoansButton = document.getElementById('generateNewLoansReportButton');
        const newLoansSearchInput = document.getElementById('newLoansSearchInput');
        const copyNewLoansButton = document.getElementById('copyNewLoansTableButton');
        const newLoansTableContainer = document.getElementById('newLoansTableContainer');

        const newLoansDetailsModalCloseButton = document.getElementById('newLoansDetailsModalCloseButton');
        const newLoansDetailsModalSearchInput = document.getElementById('newLoansDetailsModalSearchInput');
        const newLoansDetailsModalCopyButton = document.getElementById('newLoansDetailsModalCopyButton');


        // --- Clear Report Containers on Tab Initialization ---
        if (reportContainer) {
            reportContainer.innerHTML = '<p class="text-gray-500 text-center">Aging report will appear here after generation.</p>';
        }
        if (perAccountsTableContainer) {
            perAccountsTableContainer.innerHTML = '<h5 class="text-lg font-semibold text-gray-700 mb-2 p-2">PER ACCOUNTS</h5><p class="text-gray-500 text-center">Per Accounts report will appear here.</p>';
        }
        if (perMemberTableContainer) {
            perMemberTableContainer.innerHTML = '<h5 class="text-lg font-semibold text-gray-700 mb-2 p-2">PER MEMBER</h5><p class="text-gray-500 text-center">Per Member report will appear here.</p>';
        }
        if (topBorrowersTableContainer) {
            topBorrowersTableContainer.innerHTML = '<h5 class="text-lg font-semibold text-gray-700 mb-2 p-2">TOP BORROWERS</h5><p class="text-gray-500 text-center">Top Borrowers report will appear here.</p>';
        }
        if (newLoansTableContainer) {
            newLoansTableContainer.innerHTML = '<p class="text-gray-500 text-center">New Loans with Past Due Credit History report will appear here.</p>';
        }


        // --- Load Persisted Data and Re-render if Available ---
        // Aging History per Member's Loan
        if (agingReportData.fullResult) {
            renderAgingHistoryTable(agingReportData.fullResult);
            const lastArea = localStorage.getItem('lastAgingArea');
            const lastBranch = localStorage.getItem('lastAgingBranch');
            const lastDate = localStorage.getItem('lastAgingDate'); // NEW: Get last date
            const lastName = localStorage.getItem('lastName');
            const lastCid = localStorage.getItem('lastCid');
            if (lastArea) agingAreaInput.value = lastArea;
            if (lastArea) populateBranchDropdown(lastArea);
            if (lastBranch) branchInput.value = lastBranch;
            if (lastDate) dateInput.value = lastDate; // NEW: Set last date
            if (lastName) nameInput.value = lastName;
            if (lastCid) document.getElementById('agingCid').value = lastCid;
            updateOperationsAgingReportUI();
        } else {
            agingReportData = {};
            localStorage.removeItem('lastAgingArea');
            localStorage.removeItem('lastAgingBranch');
            localStorage.removeItem('lastAgingDate'); // NEW: Remove last date
            localStorage.removeItem('lastName');
            localStorage.removeItem('lastCid');
        }

        // Provisions Report
        if (provisionsReportData.per_accounts_data.length > 0 || provisionsReportData.per_member_data.length > 0) {
            const lastProvisionsArea = localStorage.getItem('lastProvisionsArea');
            const lastProvisionsBranch = localStorage.getItem('lastProvisionsBranch');
            const lastProvisionsDate = localStorage.getItem('lastProvisionsDate'); // NEW: Get last date
            const lastProvisionsMonth = localStorage.getItem('lastProvisionsMonth');
            const lastProvisionsYear = localStorage.getItem('lastProvisionsYear');
            const lastProvisionsAging = localStorage.getItem('lastProvisionsAging');

            if (lastProvisionsArea) agingAreaInput.value = lastProvisionsArea;
            if (lastProvisionsArea) populateBranchDropdown(lastProvisionsArea);
            if (lastProvisionsBranch) branchInput.value = lastProvisionsBranch;
            if (lastProvisionsDate) dateInput.value = lastProvisionsDate; // NEW: Set last date
            if (lastProvisionsMonth) provisionMonthInput.value = lastProvisionsMonth;
            if (lastProvisionsYear) provisionYearInput.value = lastProvisionsYear;
            if (lastProvisionsAging) provisionAgingInput.value = lastProvisionsAging;

            renderPerAccountsTable(provisionsReportData.per_accounts_data, parseInt(provisionMonthInput.value), parseInt(provisionYearInput.value));
            renderPerMemberTable(provisionsReportData.per_member_data, parseInt(provisionYearInput.value));
            updateProvisionsReportUI();
        } else {
            provisionsReportData = { per_accounts_data: [], per_member_data: [] };
            localStorage.removeItem('lastProvisionsArea');
            localStorage.removeItem('lastProvisionsBranch');
            localStorage.removeItem('lastProvisionsDate'); // NEW: Remove last date
            localStorage.removeItem('lastProvisionsMonth');
            localStorage.removeItem('lastProvisionsYear');
            localStorage.removeItem('lastProvisionsAging');
        }

        // Top Borrowers Report
        if (topBorrowersReportData.length > 0) {
            const lastTopBorrowersArea = localStorage.getItem('lastTopBorrowersArea');
            const lastTopBorrowersBranch = localStorage.getItem('lastTopBorrowersBranch');
            const lastTopBorrowersDate = localStorage.getItem('lastTopBorrowersDate'); // NEW: Get last date
            const lastTopBorrowersStatus = localStorage.getItem('lastTopBorrowersStatus');

            if (lastTopBorrowersArea) agingAreaInput.value = lastTopBorrowersArea;
            if (lastTopBorrowersArea) populateBranchDropdown(lastTopBorrowersArea);
            if (lastTopBorrowersBranch) branchInput.value = lastTopBorrowersBranch;
            if (lastTopBorrowersDate) dateInput.value = lastTopBorrowersDate; // NEW: Set last date
            if (lastTopBorrowersStatus) topBorrowersStatusInput.value = lastTopBorrowersStatus;

            renderTopBorrowersTable(topBorrowersReportData);
            updateTopBorrowersReportUI();
        } else {
            topBorrowersReportData = [];
            localStorage.removeItem('lastTopBorrowersArea');
            localStorage.removeItem('lastTopBorrowersBranch');
            localStorage.removeItem('lastTopBorrowersDate'); // NEW: Remove last date
            localStorage.removeItem('lastTopBorrowersStatus');
        }

        // New Loans Report
        if (newLoansReportData.length > 0) {
            const lastNewLoansArea = localStorage.getItem('lastNewLoansArea');
            const lastNewLoansBranch = localStorage.getItem('lastNewLoansBranch');
            const lastNewLoansDate = localStorage.getItem('lastNewLoansDate'); // NEW: Get last date
            const lastNewLoansYear = localStorage.getItem('lastNewLoansYear');

            if (lastNewLoansArea) agingAreaInput.value = lastNewLoansArea;
            if (lastNewLoansArea) populateBranchDropdown(lastNewLoansArea);
            if (lastNewLoansBranch) branchInput.value = lastNewLoansBranch;
            if (lastNewLoansDate) dateInput.value = lastNewLoansDate; // NEW: Set last date
            if (lastNewLoansYear) newLoansYearInput.value = lastNewLoansYear;

            sortNewLoansTable(newLoansCurrentSortKey, newLoansCurrentSortDirection);
            updateNewLoansReportUI();
        } else {
            newLoansReportData = [];
            localStorage.removeItem('lastNewLoansArea');
            localStorage.removeItem('lastNewLoansBranch');
            localStorage.removeItem('lastNewLoansDate'); // NEW: Remove last date
            localStorage.removeItem('lastNewLoansYear');
        }


        // --- Attach Event Listeners (ensure they are attached only once using dataset.listenerAttached) ---
        if (agingAreaInput && !agingAreaInput.dataset.listenerAttached) {
            agingAreaInput.addEventListener('change', () => {
                const selectedArea = agingAreaInput.value.trim();
                populateBranchDropdown(selectedArea);
                const selectedBranch = branchInput.value.trim(); // Get updated branch after repopulation
                populateDateDropdown(selectedArea, selectedBranch); // NEW: Populate date dropdown
                updateOperationsAgingReportUI();
                updateProvisionsReportUI();
                updateTopBorrowersReportUI();
                updateNewLoansReportUI();
                loadNamesAndCids(selectedArea, selectedBranch, dateInput.value.trim()); // NEW: Pass selectedDate
                fetchAndDisplaySummary(selectedArea, selectedBranch, dateInput.value.trim()); // NEW: Pass selectedDate
                nameInput.value = ''; // Clear Name/CID fields when area changes
                document.getElementById('agingCid').value = '';
                localStorage.setItem('lastAgingArea', selectedArea);
                localStorage.setItem('lastProvisionsArea', selectedArea);
                localStorage.setItem('lastTopBorrowersArea', selectedArea);
                localStorage.setItem('lastNewLoansArea', selectedArea);
            });
            agingAreaInput.dataset.listenerAttached = 'true';
        }

        if (branchInput && !branchInput.dataset.listenerAttached) {
            branchInput.addEventListener('change', () => {
                const selectedArea = agingAreaInput.value.trim();
                const selectedBranch = branchInput.value.trim();
                populateDateDropdown(selectedArea, selectedBranch); // NEW: Populate date dropdown
                updateOperationsAgingReportUI();
                updateProvisionsReportUI();
                updateTopBorrowersReportUI();
                updateNewLoansReportUI();


                // Clear Name/CID fields if 'ALL' or 'Consolidated' is selected in Branch
                if (selectedBranch === 'ALL' || selectedBranch === 'Consolidated') {
                    nameInput.value = '';
                    document.getElementById('agingCid').value = '';
                }

                loadNamesAndCids(selectedArea, selectedBranch, dateInput.value.trim()); // NEW: Pass selectedDate
                fetchAndDisplaySummary(selectedArea, selectedBranch, dateInput.value.trim()); // NEW: Pass selectedDate

                localStorage.setItem('lastAgingBranch', selectedBranch);
                localStorage.setItem('lastProvisionsBranch', selectedBranch);
                localStorage.setItem('lastTopBorrowersBranch', selectedBranch);
                localStorage.setItem('lastNewLoansBranch', selectedBranch);
            });
            branchInput.dataset.listenerAttached = 'true';
        }

        // NEW: Event listener for the new Date dropdown
        if (dateInput && !dateInput.dataset.listenerAttached) {
            dateInput.addEventListener('change', () => {
                const selectedArea = agingAreaInput.value.trim();
                const selectedBranch = branchInput.value.trim();
                const selectedDate = dateInput.value.trim();
                
                updateOperationsAgingReportUI();
                updateProvisionsReportUI();
                updateTopBorrowersReportUI();
                updateNewLoansReportUI();

                loadNamesAndCids(selectedArea, selectedBranch, selectedDate);
                fetchAndDisplaySummary(selectedArea, selectedBranch, selectedDate);

                localStorage.setItem('lastAgingDate', selectedDate);
                localStorage.setItem('lastProvisionsDate', selectedDate);
                localStorage.setItem('lastTopBorrowersDate', selectedDate);
                localStorage.setItem('lastNewLoansDate', selectedDate);
            });
            dateInput.dataset.listenerAttached = 'true';
        }


        if (nameInput && !nameInput.dataset.listenerAttached) {
            nameInput.addEventListener('input', () => {
                handleAgingNameInput();
                localStorage.setItem('lastName', nameInput.value.trim());
                localStorage.setItem('lastCid', document.getElementById('agingCid').value.trim());
            });
            // Add a 'blur' event listener to hide the datalist suggestions when the input loses focus
            nameInput.addEventListener('blur', () => {
                // This effectively "hides" the datalist suggestions by ensuring it's not actively showing
                // The datalist itself cannot be truly hidden, but its suggestions will disappear
                // when the input loses focus and is not actively being typed into.
            });
            nameInput.dataset.listenerAttached = 'true';
        }

        if (processButton && !processButton.dataset.listenerAttached) {
            processButton.addEventListener('click', processOperationsAgingReport);
            processButton.dataset.listenerAttached = 'true';
        }
        if (searchInput && !searchInput.dataset.listenerAttached) {
            searchInput.addEventListener('input', filterAgingReportTable);
            searchInput.dataset.listenerAttached = 'true';
        }
        if (copyButton && !copyButton.dataset.listenerAttached) {
            copyButton.addEventListener('click', copyAgingReportTable);
            copyButton.dataset.listenerAttached = 'true';
        }
        
        // Provisions section event listeners
        if (provisionMonthInput && !provisionMonthInput.dataset.listenerAttached) {
            provisionMonthInput.addEventListener('change', () => {
                updateProvisionsReportUI();
                localStorage.setItem('lastProvisionsMonth', provisionMonthInput.value.trim());
            });
            provisionMonthInput.dataset.listenerAttached = 'true';
        }
        if (provisionYearInput && !provisionYearInput.dataset.listenerAttached) {
            provisionYearInput.addEventListener('change', () => {
                updateProvisionsReportUI();
                localStorage.setItem('lastProvisionsYear', provisionYearInput.value.trim());
            });
            provisionYearInput.dataset.listenerAttached = 'true';
        }
        if (provisionAgingInput && !provisionAgingInput.dataset.listenerAttached) {
            provisionAgingInput.addEventListener('change', () => {
                updateProvisionsReportUI();
                localStorage.setItem('lastProvisionsAging', provisionAgingInput.value.trim());
            });
            provisionAgingInput.dataset.listenerAttached = 'true';
        }
        if (generateProvisionsButton && !generateProvisionsButton.dataset.listenerAttached) {
            generateProvisionsButton.addEventListener('click', generateProvisionsReport);
            generateProvisionsButton.dataset.listenerAttached = 'true';
        }
        if (provisionsSearchInput && !provisionsSearchInput.dataset.listenerAttached) {
            provisionsSearchInput.addEventListener('input', filterProvisionsReportTables);
            provisionsSearchInput.dataset.listenerAttached = 'true';
        }
        if (copyProvisionsButton && !copyProvisionsButton.dataset.listenerAttached) {
            copyProvisionsButton.addEventListener('click', copyProvisionsReportTables);
            copyProvisionsButton.dataset.listenerAttached = 'true';
        }

        // Top Borrowers section event listeners
        if (topBorrowersStatusInput && !topBorrowersStatusInput.dataset.listenerAttached) {
            topBorrowersStatusInput.addEventListener('change', () => {
                updateTopBorrowersReportUI();
                localStorage.setItem('lastTopBorrowersStatus', topBorrowersStatusInput.value.trim());
            });
            topBorrowersStatusInput.dataset.listenerAttached = 'true';
        }
        if (generateTopBorrowersButton && !generateTopBorrowersButton.dataset.listenerAttached) {
            generateTopBorrowersButton.addEventListener('click', generateTopBorrowersReport);
            generateTopBorrowersButton.dataset.listenerAttached = 'true';
        }
        if (topBorrowersSearchInput && !topBorrowersSearchInput.dataset.listenerAttached) {
            topBorrowersSearchInput.addEventListener('input', filterTopBorrowersTable);
            topBorrowersSearchInput.dataset.listenerAttached = 'true';
        }
        if (copyTopBorrowersButton && !copyTopBorrowersButton.dataset.listenerAttached) {
            copyTopBorrowersButton.addEventListener('click', copyTopBorrowersTable);
            copyTopBorrowersButton.dataset.listenerAttached = 'true';
        }

        // New Loans with Past Due Credit History section event listeners
        if (newLoansYearInput && !newLoansYearInput.dataset.listenerAttached) {
            newLoansYearInput.addEventListener('change', () => {
                updateNewLoansReportUI();
                localStorage.setItem('lastNewLoansYear', newLoansYearInput.value.trim());
            });
            newLoansYearInput.dataset.listenerAttached = 'true';
        }
        if (generateNewLoansButton && !generateNewLoansButton.dataset.listenerAttached) {
            generateNewLoansButton.addEventListener('click', generateNewLoansReport);
            generateNewLoansButton.dataset.listenerAttached = 'true';
        }
        if (newLoansSearchInput && !newLoansSearchInput.dataset.listenerAttached) {
            newLoansSearchInput.addEventListener('input', filterNewLoansTable);
            newLoansSearchInput.dataset.listenerAttached = 'true';
        }
        if (copyNewLoansButton && !copyNewLoansButton.dataset.listenerAttached) {
            copyNewLoansButton.addEventListener('click', copyNewLoansTable);
            copyNewLoansButton.dataset.listenerAttached = 'true';
        }

        // New Loans Details Modal close button
        if (newLoansDetailsModalCloseButton && !newLoansDetailsModalCloseButton.dataset.listenerAttached) {
            newLoansDetailsModalCloseButton.addEventListener('click', hideNewLoansDetailsModal);
            newLoansDetailsModalCloseButton.dataset.listenerAttached = 'true';
        }
        // New Loans Details Modal search and copy buttons
        if (newLoansDetailsModalSearchInput && !newLoansDetailsModalSearchInput.dataset.listenerAttached) {
            newLoansDetailsModalSearchInput.addEventListener('input', filterNewLoansDetailsTable);
            newLoansDetailsModalSearchInput.dataset.listenerAttached = 'true';
        }
        if (newLoansDetailsModalCopyButton && !newLoansDetailsModalCopyButton.dataset.listenerAttached) {
            newLoansDetailsModalCopyButton.addEventListener('click', copyNewLoansDetailsTable);
            newLoansDetailsModalCopyButton.dataset.listenerAttached = 'true';
        }


        // Initial UI update and load data if a branch is already selected
        populateProvisionsYearDropdown(); // Populate year dropdown on init
        populateNewLoansYearDropdown(); // Populate new loans year dropdown on init

        // Load stored area and branch first for initial population
        const initialArea = localStorage.getItem('lastAgingArea') || '';
        const initialBranch = localStorage.getItem('lastAgingBranch') || '';
        const initialDate = localStorage.getItem('lastAgingDate') || ''; // NEW: Get initial date
        agingAreaInput.value = initialArea; // Set initial area
        populateBranchDropdown(initialArea); // Populate branches based on initial area
        branchInput.value = initialBranch; // Set initial branch
        populateDateDropdown(initialArea, initialBranch); // NEW: Populate date dropdown
        dateInput.value = initialDate; // NEW: Set initial date


        updateOperationsAgingReportUI();
        updateProvisionsReportUI(); // Initial update for provisions section
        updateTopBorrowersReportUI(); // Initial update for top borrowers section
        updateNewLoansReportUI(); // Initial update for new loans section
        
        // Call initial data loading with potentially loaded values
        loadNamesAndCids(initialArea, initialBranch, initialDate); // NEW: Pass initialDate
        fetchAndDisplaySummary(initialArea, initialBranch, initialDate); // NEW: Pass initialDate
        
        // Render the aging legend on tab initialization
        renderAgingLegend();
    }

    // Register this sub-tab's initializer with the main application logic
    registerTabInitializer('operationsAgingReport', initOperationsAgingReportTab);

})(); // End IIFE
