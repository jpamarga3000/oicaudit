document.addEventListener('DOMContentLoaded', function() {
    const areaSelect = document.getElementById('areaSelect');
    const branchSelect = document.getElementById('branchSelect');
    const dateInput = document.getElementById('dateInput');
    const generateReportBtn = document.getElementById('generateReportBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const logoLoader = document.getElementById('logoLoader'); // Get the logo image element
    const financialStatementSection = document.getElementById('financialStatementSection');
    const financialStatementBody = document.getElementById('financialStatementBody');
    const financialStatementFooter = document.getElementById('financialStatementFooter');
    const financialPerformanceSection = document.getElementById('financialPerformanceSection');
    const financialPerformanceBody = document.getElementById('financialPerformanceBody');

    // Custom Alert elements
    const customAlert = document.getElementById('customAlert');
    const customAlertText = document.getElementById('customAlertText');

    // To store active trend chart instance and the element it belongs to
    let activeTrendChart = null;
    let activeTrendRowElement = null; // Store the currently open trend row

    // Cache for trend data: Maps a unique key (account label + report type + area + branch + date) to trend data
    const trendDataCache = new Map();

    // Define the Area-Branch mapping directly in JavaScript (now includes 'ALL' option)
    const areaBranchMap = {
        'Area 1': [
            'ALL', // Add 'ALL' option for Area 1
            'BAUNGON', "BULUA", "CARMEN", "COGON", "EL SALVADOR",
            "ILIGAN", "TALAKAG", "YACAPIN"
        ],
        'Area 2': [
            'ALL', // Add 'ALL' option for Area 2
            "AGLAYAN", "DON CARLOS", "ILUSTRE", "MANOLO", "MARAMAG",
            "TORIL", "VALENCIA"
        ],
        'Area 3': [
            'ALL', // Add 'ALL' option for Area 3
            "AGORA", "BALINGASAG", "BUTUAN", "GINGOOG", "PUERTO",
            "TAGBILARAN", "TUBIGON", "UBAY"
        ],
        'CONSOLIDATED': [ // Capitalized 'CONSOLIDATED'
            'CONSOLIDATED', 'HEAD OFFICE' // Capitalized 'CONSOLIDATED'
        ]
    };

    // Function to format currency
    const formatCurrency = (value) => {
        if (value === null || value === undefined || isNaN(value)) {
            return '0.00'; // Return '0.00' for invalid numbers
        }
        const numValue = parseFloat(value);
        if (numValue < 0) {
            return `(${Math.abs(numValue).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })})`;
        }
        return numValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    };

    // Function to format percentage
    const formatPercentage = (value) => {
        if (value === null || value === undefined || isNaN(value) || !isFinite(value)) {
            return '0.00%'; // Return '0.00%' for invalid numbers or infinity
        }
        return `${value.toFixed(2)}%`;
    };

    // Populate Area and Branch dropdowns based on the new map
    const populateDropdowns = async () => {
        // Populate Area Select
        areaSelect.innerHTML = '<option value="">Select Area</option>';
        for (const area in areaBranchMap) {
            const option = document.createElement('option');
            option.value = area;
            option.textContent = area;
            areaSelect.appendChild(option);
        }

        // Event listener for Area select to filter branches
        areaSelect.addEventListener('change', () => {
            const selectedArea = areaSelect.value;
            branchSelect.innerHTML = '<option value="">Select Branch</option>';

            if (selectedArea && areaBranchMap[selectedArea]) {
                areaBranchMap[selectedArea].forEach(branch => {
                    const option = document.createElement('option');
                    option.value = branch;
                    option.textContent = branch;
                    branchSelect.appendChild(option);
                });
            }
        });
    };

    // Function to show custom alert message
    const showAlert = (message, type = 'info', duration = 3000) => {
        // Set up the customAlert for centering and overlay
        customAlert.className = `fixed inset-0 z-50 flex items-center justify-center p-4 transition-opacity duration-300 ease-in-out bg-black bg-opacity-50`; // Added inset-0, flex, items-center, justify-center, bg-black, bg-opacity-50
        customAlertText.textContent = message;
        
        // Create a content container for the alert text to apply styling without affecting the overlay
        const alertContent = document.createElement('div');
        alertContent.className = `p-6 rounded-lg shadow-lg text-white font-bold text-center`; // Base styling for the alert box itself
        
        // Add type-specific background color to the content container
        if (type === 'success') {
            alertContent.classList.add('bg-green-500');
        } else if (type === 'error') {
            alertContent.classList.add('bg-red-500');
        } else { // Default to info
            alertContent.classList.add('bg-blue-500');
        }

        // Clear previous content and append the new alert content
        customAlert.innerHTML = ''; // Clear existing content
        alertContent.appendChild(customAlertText); // Append the text span to the new content div
        customAlert.appendChild(alertContent); // Append the content div to the customAlert container

        customAlert.classList.remove('hidden'); // Show the alert container
        customAlert.style.opacity = '1'; // Fade in

        setTimeout(() => {
            customAlert.style.opacity = '0'; // Fade out
            setTimeout(() => {
                customAlert.classList.add('hidden'); // Hide after fade out
                customAlert.innerHTML = ''; // Clear content after hiding
            }, 300); // Wait for fade out transition
        }, duration);
    };

    const showError = (message) => {
        showAlert(message, 'error', 5000); // Show error for 5 seconds
        financialStatementSection.classList.add('hidden');
        financialPerformanceSection.classList.add('hidden');
    };

    // Function to draw a simple trend line on a canvas (now using Chart.js)
    const drawTrendChart = (canvas, data, labels, accountLabel) => {
        if (activeTrendChart) {
            activeTrendChart.destroy(); // Destroy existing chart instance if any
        }

        const ctx = canvas.getContext('2d');
        const isNegativeTrend = data[data.length - 1] < data[0]; // Simple check for overall trend direction

        const borderColor = isNegativeTrend ? '#ef4444' : '#22c55e'; // red-500 or green-500
        const backgroundColor = isNegativeTrend ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)'; // Light red or green fill

        activeTrendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: accountLabel,
                    data: data,
                    borderColor: borderColor,
                    backgroundColor: backgroundColor,
                    fill: true, // Fill the area under the line
                    tension: 0.4, // Makes the line curved (Bezier curve tension)
                    pointRadius: 5,
                    pointBackgroundColor: borderColor,
                    pointBorderColor: '#fff',
                    pointHoverRadius: 7,
                    pointHoverBackgroundColor: borderColor,
                    pointHoverBorderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false, // Allow canvas to resize based on container
                plugins: {
                    legend: {
                        display: false // Hide legend
                    },
                    title: {
                        display: true,
                        text: `${accountLabel} Trend`, // Title for the chart
                        color: '#4a5568',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${formatCurrency(context.raw)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Date',
                            color: '#4a5568'
                        },
                        ticks: {
                            color: '#4a5568'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Amount',
                            color: '#4a5568'
                        },
                        ticks: {
                            color: '#4a5568',
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                },
                elements: {
                    line: {
                        borderWidth: 2 // Thicker line
                    }
                }
            }
        });
    };

    /**
     * Populates the trendDataCache with trend data for all accounts
     * from the fetched financial statement data.
     * @param {object} data - The full financial statement data received from the backend.
     * @param {string} area - The selected area.
     * @param {string} branch - The selected branch.
     * @param {string} date - The selected date (YYYY-MM-DD).
     */
    const populateTrendCache = (data, area, branch, date) => {
        // Helper to add data to cache
        const addAccountTrendToCache = (account, reportType) => {
            if (account && account.label && account.trend_data && account.trend_data.length > 0) {
                const cacheKey = `${account.label}-${reportType}-${area}-${branch}-${date}`;
                trendDataCache.set(cacheKey, {
                    account_label: account.label,
                    report_type: reportType,
                    dates: [], // Dates are not directly in account.trend_data, will need to be derived or passed
                    values: account.trend_data
                });
            }
        };

        // Financial Position (Balance Sheet)
        const fpData = data.financialPosition;
        for (const categoryKey of ['assets', 'liabilities', 'equity']) {
            for (const subCategoryKey in fpData[categoryKey]) {
                if (Array.isArray(fpData[categoryKey][subCategoryKey])) {
                    for (const account of fpData[categoryKey][subCategoryKey]) {
                        addAccountTrendToCache(account, 'financial_position');
                        if (account.components) {
                            for (const subComponent of account.components) {
                                addAccountTrendToCache(subComponent, 'financial_position');
                            }
                        }
                    }
                } else if (typeof fpData[categoryKey][subCategoryKey] === 'object' && fpData[categoryKey][subCategoryKey] !== null) {
                    // Handle total accounts like totalCurrent, totalNonCurrent, grandTotal
                    addAccountTrendToCache(fpData[categoryKey][subCategoryKey], 'financial_position');
                }
            }
        }
        // Handle top-level totalLiabilitiesAndMembersEquity
        addAccountTrendToCache(fpData.totalLiabilitiesAndMembersEquity, 'financial_position');

        // Financial Performance (Income Statement)
        const ipData = data.financialPerformance;
        for (const categoryKey of ['revenues', 'expenses', 'otherItems']) {
            for (const accountKey in ipData[categoryKey]) {
                const account = ipData[categoryKey][accountKey];
                if (typeof account === 'object' && account !== null) {
                    addAccountTrendToCache(account, 'financial_performance');
                    if (account.components) {
                        for (const subComponent of account.components) {
                            addAccountTrendToCache(subComponent, 'financial_performance');
                        }
                    }
                }
            }
        }
        // Handle top-level netSurplusBeforeOtherItems and netSurplusForAllocation
        addAccountTrendToCache(ipData.netSurplusBeforeOtherItems, 'financial_performance');
        addAccountTrendToCache(ipData.netSurplusForAllocation, 'financial_performance');

        // IMPORTANT: The backend's `financial_statement_process.py` currently returns `trend_data`
        // as just values. The `dates` for the trend are generated in `get_financial_statement_trend_data`
        // based on the report_date_dt. We need to regenerate these dates here for the cached data.
        try {
            const reportDateDt = new Date(date);
            const bsTrendDates = [];
            for (let i = 4; i >= 0; i--) { // 5 years including current
                const trendYearDt = new Date(reportDateDt.getFullYear() - i, 11, 31); // Dec 31 for BS
                bsTrendDates.push(trendYearDt.toLocaleDateString('en-US', { month: 'numeric', day: 'numeric', year: 'numeric' }));
            }

            const isTrendDates = [];
            for (let i = 4; i >= 0; i--) { // 5 years including current
                const trendYearDt = new Date(reportDateDt.getFullYear() - i, reportDateDt.getMonth(), reportDateDt.getDate());
                isTrendDates.push(trendYearDt.toLocaleDateString('en-US', { month: 'numeric', day: 'numeric', year: 'numeric' }));
            }

            // Now, iterate through the cache and add the correct dates
            for (let [key, trendItem] of trendDataCache.entries()) {
                if (trendItem.report_type === 'financial_position') {
                    trendItem.dates = bsTrendDates;
                } else if (trendItem.report_type === 'financial_performance') {
                    trendItem.dates = isTrendDates;
                }
                // Ensure values and dates match length, truncate if necessary
                const minLen = Math.min(trendItem.values.length, trendItem.dates.length);
                trendItem.values = trendItem.values.slice(0, minLen);
                trendItem.dates = trendItem.dates.slice(0, minLen);
                trendDataCache.set(key, trendItem); // Update cache with dates
            }

        } catch (e) {
            console.error("Error generating trend dates for cache:", e);
        }
    };


    generateReportBtn.addEventListener('click', async () => {
        financialStatementSection.classList.add('hidden');
        financialPerformanceSection.classList.add('hidden'); // Hide performance section before new generation
        
        // Clear the cache when a new report is generated
        trendDataCache.clear();

        // Close any open trend rows before generating new report
        if (activeTrendRowElement) {
            activeTrendRowElement.remove();
            activeTrendRowElement = null;
            if (activeTrendChart) {
                activeTrendChart.destroy();
                activeTrendChart = null;
            }
        }

        // Show loading indicator with fade-in and glow
        loadingIndicator.classList.remove('hidden');
        loadingIndicator.style.opacity = '1'; 
        logoLoader.classList.add('glowing'); // Apply glowing animation to the logo

        const area = areaSelect.value; // Get selected area
        const branch = branchSelect.value;
        const date = dateInput.value; // This will be inYYYY-MM-DD format from input type="date"

        if (!area || !branch || !date) { // Validate area as well
            showError('Please select an Area, Branch, and a Date.');
            // Hide loading indicator with fade-out and remove glow
            loadingIndicator.style.opacity = '0'; 
            logoLoader.classList.remove('glowing');
            setTimeout(() => {
                loadingIndicator.classList.add('hidden'); 
            }, 300); // Match CSS transition duration
            return;
        }

        try {
            const response = await fetch(`${window.FLASK_API_BASE_URL}/financial_statement`, { // Use the full API base URL
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    area: area, // Send area to backend
                    branch: branch,
                    date: date // Send asYYYY-MM-DD, backend will handle conversion for Excel lookup
                })
            });

            const responseText = await response.text(); // Read response body as text once

            if (!response.ok) {
                console.error('HTTP Error:', response.status, response.statusText, 'Response Body:', responseText);
                showError(`Failed to fetch financial statement: Server responded with status ${response.status}. See console for details.`);
                // Hide loading indicator with fade-out and remove glow
                loadingIndicator.style.opacity = '0'; 
                logoLoader.classList.remove('glowing');
                setTimeout(() => {
                    loadingIndicator.classList.add('hidden'); 
                }, 300);
                return;
            }

            let result;
            try {
                result = JSON.parse(responseText);
            } catch (jsonError) {
                console.error('JSON Parsing Error:', jsonError);
                console.error('Raw Response Text:', responseText);
                showError('An error occurred while parsing the financial statement data. Please check the console for raw response.');
                // Hide loading indicator with fade-out and remove glow
                loadingIndicator.style.opacity = '0'; 
                logoLoader.classList.remove('glowing');
                setTimeout(() => {
                    loadingIndicator.classList.add('hidden'); 
                }, 300);
                return;
            }

            if (result.status === 'success') {
                const data = result.data; // This data now contains both financialPosition and financialPerformance
                console.log("Financial Statement Data Received:", data); // Log the received data

                // Populate the trend data cache immediately after receiving the main report
                populateTrendCache(data, area, branch, date);

                // Parse the input date to get the year for dynamic headers
                const inputDate = new Date(date);
                const currentYear = inputDate.getFullYear();
                const previousYear = currentYear - 1;

                // Format the input date for display in headers
                const formattedInputDate = new Date(date).toLocaleDateString('en-US', {
                    month: '2-digit',
                    day: '2-digit',
                    year: 'numeric'
                });

                // Determine the last December date for header
                const lastDecemberDateForHeader = `12/31/${previousYear}`;
                
                // Determine the previous period date for header (same month/day, previous year)
                const previousPeriodDateForHeader = new Date(inputDate);
                previousPeriodDateForHeader.setFullYear(previousPeriodDateForHeader.getFullYear() - 1);
                const formattedPreviousPeriodDate = previousPeriodDateForHeader.toLocaleDateString('en-US', {
                    month: '2-digit',
                    day: '2-digit',
                    year: 'numeric'
                });


                // --- Update Financial Position Headers ---
                const fpTableHead = financialStatementSection.querySelector('thead tr');
                fpTableHead.innerHTML = `
                    <th class="text-left">ACCOUNT</th>
                    <th class="text-right">${formattedInputDate}</th>
                    <th class="text-right">${lastDecemberDateForHeader}</th>
                    <th class="text-center">CHANGES (%)</th>
                    <th class="text-center">TREND</th>
                    <th class="text-center">STRUCTURE (%)</th>
                `;

                // --- Render Financial Position (Balance Sheet) ---
                financialStatementBody.innerHTML = ''; // Clear previous content
                financialStatementFooter.innerHTML = ''; // Clear previous content

                const financialPositionData = data.financialPosition;

                // Helper to add a row to the Financial Position table
                const addFinancialPositionRow = (accountData, isSubAccount = false, parentKey = '') => {
                    const row = financialStatementBody.insertRow();
                    const labelCell = row.insertCell(0);
                    const currentBalanceCell = row.insertCell(1);
                    const lastDecemberBalanceCell = row.insertCell(2);
                    const changesPercentageCell = row.insertCell(3);
                    const trendCell = row.insertCell(4); // New cell for trend graph
                    const structurePercentageCell = row.insertCell(5);

                    labelCell.textContent = accountData.label;
                    currentBalanceCell.textContent = formatCurrency(accountData.current_balance);
                    lastDecemberBalanceCell.textContent = formatCurrency(accountData.last_december_balance);
                    changesPercentageCell.textContent = formatPercentage(accountData.changes_percentage);
                    structurePercentageCell.textContent = formatPercentage(accountData.structure_percentage);

                    currentBalanceCell.classList.add('text-right');
                    lastDecemberBalanceCell.classList.add('text-right'); // Ensure data cells are right-aligned
                    changesPercentageCell.classList.add('text-center'); // Changed to center
                    structurePercentageCell.classList.add('text-center'); // Changed to center
                    trendCell.classList.add('text-center'); // Center the trend graph

                    // Apply color to Changes (%) text
                    if (accountData.changes_percentage < 0) {
                        changesPercentageCell.classList.add('text-red-500');
                    } else if (accountData.changes_percentage > 0) {
                        changesPercentageCell.classList.add('text-green-500');
                    }

                    // Add a placeholder for the trend line (will be clickable)
                    const trendSpan = document.createElement('span');
                    trendSpan.classList.add('trend-data', 'cursor-pointer', 'font-bold');
                    trendSpan.textContent = 'View Trend'; // Or a small icon
                    trendSpan.dataset.accountLabel = accountData.label;
                    trendSpan.dataset.reportType = 'financial_position';
                    trendSpan.dataset.area = area;
                    trendSpan.dataset.branch = branch;
                    trendSpan.dataset.date = date; // Pass the selected date
                    trendSpan.classList.add(accountData.changes_percentage < 0 ? 'text-red-600' : 'text-green-600');
                    trendCell.appendChild(trendSpan);


                    if (isSubAccount) {
                        row.classList.add('sub-account-row', 'hidden', `sub-account-of-fp-position-${parentKey}`);
                        labelCell.classList.add('item-label', 'sub-account-label-indent');
                        // REMOVED: sub-account-data-indent from numerical cells
                    } else {
                        labelCell.classList.add('item-label');
                        if (accountData.components && accountData.components.length > 0) {
                            labelCell.classList.add('toggle-sub-accounts', 'cursor-pointer');
                            labelCell.dataset.accountKey = `fp-position-${accountData.label.replace(/\s/g, '-').replace(/[^\w-]/g, '')}`;
                        }
                    }

                    // Apply specific styles for totals
                    if (accountData.type === 'total') {
                        labelCell.classList.add('font-bold', 'total-item');
                        currentBalanceCell.classList.add('font-bold', 'total-item');
                        lastDecemberBalanceCell.classList.add('font-bold', 'total-item');
                        changesPercentageCell.classList.add('font-bold', 'total-item');
                        structurePercentageCell.classList.add('font-bold', 'total-item');
                        trendCell.classList.add('total-item'); // Apply to trend cell as well
                    } else if (accountData.type === 'grand_total') {
                        labelCell.classList.add('font-bold', 'text-lg', 'grand-total-row');
                        currentBalanceCell.classList.add('font-bold', 'text-lg', 'grand-total-row');
                        lastDecemberBalanceCell.classList.add('font-bold', 'text-lg', 'grand-total-row');
                        changesPercentageCell.classList.add('font-bold', 'text-lg', 'grand-total-row');
                        structurePercentageCell.classList.add('font-bold', 'text-lg', 'grand-total-row');
                        trendCell.classList.add('grand-total-row'); // Apply to trend cell as well
                    }
                };

                // Define the order of accounts for display in Financial Position
                const FP_ACCOUNTS_ORDER = [
                    // Assets
                    { label: 'ASSETS', type: 'section_header' }, // New section header
                    { label: 'CURRENT ASSETS', type: 'category' },
                    { key: 'cashAndCashEquivalents', label: 'Cash and Cash Equivalents:', type: 'main', category: 'assets', subCategory: 'current' },
                    { key: 'loansAndReceivables', label: 'Loans and Receivables:', type: 'main', category: 'assets', subCategory: 'current' },
                    { key: 'financialAssetsCurrent', label: 'Financial Assets:', type: 'main', category: 'assets', subCategory: 'current' },
                    { key: 'otherCurrentAssets', label: 'Other Current Assets:', type: 'main', category: 'assets', subCategory: 'current' },
                    { key: 'totalCurrent', label: 'TOTAL CURRENT ASSETS:', type: 'total', category: 'assets' },
                    
                    { label: 'NON-CURRENT ASSETS', type: 'category' },
                    { key: 'financialAssetsNonCurrent', label: 'Financial Assets - Non-Current:', type: 'main', category: 'assets', subCategory: 'non-current' },
                    { key: 'investmentInSubsidiaries', label: 'Investment in Subsidiaries:', type: 'main', category: 'assets', subCategory: 'non-current' },
                    { key: 'investmentInAssociates', label: 'Investment in Associates:', type: 'main', category: 'assets', subCategory: 'non-current' },
                    { key: 'investmentInJointVentures', label: 'Investment in Joint Ventures:', type: 'main', category: 'assets', subCategory: 'non-current' },
                    { key: 'investmentProperty', label: 'Investment Property:', type: 'main', category: 'assets', subCategory: 'non-current' },
                    { key: 'propertyPlantAndEquipment', label: 'Property, Plant, and Equipment:', type: 'main', category: 'assets', subCategory: 'non-current' },
                    { key: 'otherNonCurrentAssets', label: 'Other Non-Current Assets:', type: 'main', category: 'assets', subCategory: 'non-current' },
                    { key: 'totalNonCurrent', label: 'TOTAL NON-CURRENT ASSETS:', type: 'total', category: 'assets' },
                    { key: 'grandTotal', label: 'TOTAL ASSETS:', type: 'grand_total', category: 'assets' },

                    // Separator between Assets and Liabilities/Equity
                    { type: 'separator' }, 

                    // Liabilities
                    { label: 'LIABILITIES', type: 'section_header' }, // New section header
                    { label: 'CURRENT LIABILITIES', type: 'category' },
                    { key: 'depositLiabilities', label: 'Deposit Liabilities:', type: 'main', category: 'liabilities', subCategory: 'current' },
                    { key: 'accountsAndOtherPayables', label: 'Accounts and Other Payables:', type: 'main', category: 'liabilities', subCategory: 'current' },
                    { key: 'accruedExpenses', label: 'Accrued Expenses:', type: 'main', category: 'liabilities', subCategory: 'current' },
                    { key: 'otherCurrentLiabilities', label: 'Other Current Liabilities:', type: 'main', category: 'liabilities', subCategory: 'current' },
                    { key: 'totalCurrent', label: 'TOTAL CURRENT LIABILITIES:', type: 'total', category: 'liabilities' },

                    { label: 'NON-CURRENT LIABILITIES', type: 'category' },
                    { key: 'loansPayableNet', label: 'Loans Payable, Net:', type: 'main', category: 'liabilities', subCategory: 'non-current' },
                    { key: 'revolvingCapitalPayable', label: 'Revolving Capital Payable:', type: 'main', category: 'liabilities', subCategory: 'non-current' },
                    { key: 'retirementFundPayable', label: 'Retirement Fund Payable:', type: 'main', category: 'liabilities', subCategory: 'non-current' },
                    { key: 'projectSubsidyFundPayable', label: 'Project Subsidy Fund Payable:', type: 'main', category: 'liabilities', subCategory: 'non-current' },
                    { key: 'membersBenefitsAndOtherFundsPayable', label: 'Members\' Benefits and Other Funds Payable:', type: 'main', category: 'liabilities', subCategory: 'non-current' },
                    { key: 'dueToHeadOfficeBranchSubsidiary', label: 'Due to Head Office/Branch/Subsidiary:', type: 'main', category: 'liabilities', subCategory: 'non-current' },
                    { key: 'otherNonCurrentLiabilities', label: 'Other Non-Current Liabilities:', type: 'main', category: 'liabilities', subCategory: 'non-current' },
                    { key: 'totalNonCurrent', label: 'TOTAL NON-CURRENT LIABILITIES:', type: 'total', category: 'liabilities' },
                    { key: 'grandTotal', label: 'TOTAL LIABILITIES:', type: 'total', category: 'liabilities' },

                    // Equity
                    { label: 'MEMBERS\' EQUITY', type: 'section_header' }, // New section header
                    { key: 'commonShares', label: 'Common Shares:', type: 'main', category: 'equity', subCategory: 'equity' },
                    { key: 'preferredShares', label: 'Preferred Shares:', type: 'main', category: 'equity', subCategory: 'equity' },
                    { key: 'depositsForShareCapitalSubscription', label: 'Deposits for Share Capital Subscription:', type: 'main', category: 'equity', subCategory: 'equity' },
                    { key: 'undividedNetSurplusNetLoss', label: 'Undivided Net Surplus (Net Loss):', type: 'main', category: 'equity', subCategory: 'equity' },
                    { key: 'statutoryFunds', label: 'STATUTORY FUNDS:', type: 'main', category: 'equity', subCategory: 'equity' },
                    { key: 'grandTotal', label: 'TOTAL MEMBERS\' EQUITY:', type: 'total', category: 'equity' },
                    { key: 'totalLiabilitiesAndMembersEquity', label: 'TOTAL LIABILITIES AND MEMBERS\' EQUITY:', type: 'grand_total' }
                ];

                // Iterate through the predefined order and render Financial Position
                FP_ACCOUNTS_ORDER.forEach(item => {
                    if (item.type === 'category') {
                        const headerRow = financialStatementBody.insertRow();
                        const headerCell = headerRow.insertCell(0);
                        headerCell.colSpan = 6; // Span all 6 columns including trend
                        headerCell.classList.add('category-header', 'text-gray-600', 'font-semibold', 'mt-4');
                        headerCell.textContent = item.label;
                    } else if (item.type === 'section_header') { // Handle new section headers
                        const sectionHeaderRow = financialStatementBody.insertRow();
                        const sectionHeaderCell = sectionHeaderRow.insertCell(0);
                        sectionHeaderCell.colSpan = 6; // Span all 6 columns
                        sectionHeaderCell.classList.add('section-header'); // Apply new styling
                        sectionHeaderCell.textContent = item.label;
                    }
                    else if (item.type === 'separator') {
                        const separatorRow = financialStatementBody.insertRow();
                        const separatorCell = separatorRow.insertCell(0);
                        separatorCell.colSpan = 6; // Span all 6 columns
                        separatorCell.classList.add('py-4'); // Add some vertical padding
                        separatorCell.innerHTML = '<div class="h-1 bg-gray-300 rounded-full my-2"></div>'; // Horizontal line
                    }
                    else if (item.type === 'main') {
                        const mainAccountData = financialPositionData[item.category][item.subCategory].find(acc => acc.label === item.label);
                        if (mainAccountData) {
                            addFinancialPositionRow(mainAccountData, false); // Add main account
                            // Add sub-accounts
                            if (mainAccountData.components && mainAccountData.components.length > 0) {
                                mainAccountData.components.forEach(component => {
                                    addFinancialPositionRow(component, true, mainAccountData.label.replace(/\s/g, '-').replace(/[^\w-]/g, ''));
                                });
                            }
                        }
                    } else if (item.type === 'total' || item.type === 'grand_total') {
                        let totalAccountData;
                        if (item.category) {
                            totalAccountData = financialPositionData[item.category][item.key];
                        } else { // For totalLiabilitiesAndMembersEquity which is at root level
                            totalAccountData = financialPositionData[item.key];
                        }

                        if (totalAccountData) {
                             // Create a temporary object to pass to addFinancialPositionRow for consistent handling
                            const formattedTotalData = {
                                label: item.label,
                                current_balance: totalAccountData.current_balance,
                                last_december_balance: totalAccountData.last_december_balance,
                                changes_percentage: totalAccountData.changes_percentage,
                                structure_percentage: totalAccountData.structure_percentage,
                                trend_data: totalAccountData.trend_data, // Pass trend data for totals
                                type: item.type // Pass type for styling
                            };
                            addFinancialPositionRow(formattedTotalData, false);
                        }
                    }
                });

                financialStatementSection.classList.remove('hidden');


                // --- Update Financial Performance Headers ---
                const fpPerformanceTableHead = financialPerformanceSection.querySelector('thead tr');
                fpPerformanceTableHead.innerHTML = `
                    <th class="text-left">ACCOUNT</th>
                    <th class="text-right">${formattedInputDate}</th>
                    <th class="text-right">${formattedPreviousPeriodDate}</th>
                    <th class="text-center">CHANGES (%)</th>
                    <th class="text-center">TREND</th>
                    <th class="text-center">STRUCTURE (%)</th>
                `;

                // --- Render Financial Performance (Income Statement) ---
                financialPerformanceBody.innerHTML = ''; // Clear previous content
                financialPerformanceFooter.innerHTML = ''; // Clear previous content

                const financialPerformanceData = data.financialPerformance;
                console.log("Financial Performance Data Received:", financialPerformanceData); // Log the received data for IS

                // Define the order of accounts for display
                const IS_ACCOUNTS_ORDER = [
                    // Revenues
                    { label: 'REVENUES', type: 'category' },
                    { key: 'incomeFromCreditOperations', label: 'Income from Credit Operations', type: 'main', category: 'revenues' },
                    { key: 'otherIncome', label: 'Other Income', type: 'main', category: 'revenues' },
                    { key: 'totalRevenues', label: 'TOTAL REVENUES', type: 'total', category: 'revenues' },

                    // Expenses
                    { label: 'EXPENSES', type: 'category' },
                    { key: 'financingCost', label: 'FINANCING COST', type: 'main', category: 'expenses' },
                    { key: 'administrativeCosts', label: 'Administrative Costs', type: 'main', category: 'expenses' },
                    { key: 'operatingCosts', label: 'Operating Costs', type: 'main', category: 'expenses' },
                    { key: 'totalExpenses', label: 'TOTAL EXPENSES', type: 'total', category: 'expenses' },

                    // Net Surplus Before Other Items
                    { key: 'netSurplusBeforeOtherItems', label: 'Net Surplus Before Other Items', type: 'total_special' },

                    // Other Items
                    { label: 'Other Items - Subsidy/Gain (Losses)', type: 'category' },
                    { key: 'otherItemsSubsidyGainLosses', label: 'Other Items - Subsidy/Gain (Losses)', type: 'main', category: 'otherItems' },
                    { key: 'totalOtherItems', label: 'TOTAL OTHER ITEMS', type: 'total', category: 'otherItems' },

                    // Net Surplus For Allocation
                    { key: 'netSurplusForAllocation', label: 'NET SURPLUS (FOR ALLOCATION)', type: 'grand_total' }
                ];

                // Helper to add a row to the performance table
                const addPerformanceRow = (accountData, isSubAccount = false, parentKey = '') => {
                    const row = financialPerformanceBody.insertRow();
                    const labelCell = row.insertCell(0);
                    const currentBalanceCell = row.insertCell(1);
                    const lastDecemberBalanceCell = row.insertCell(2); // This is now "Previous Period"
                    const changesPercentageCell = row.insertCell(3);
                    const trendCell = row.insertCell(4); // New cell for trend graph
                    const structurePercentageCell = row.insertCell(5);

                    labelCell.textContent = accountData.label;
                    currentBalanceCell.textContent = formatCurrency(accountData.current_balance);
                    lastDecemberBalanceCell.textContent = formatCurrency(accountData.last_december_balance); // Use last_december_balance for previous period
                    changesPercentageCell.textContent = formatPercentage(accountData.changes_percentage);
                    structurePercentageCell.textContent = formatPercentage(accountData.structure_percentage);

                    currentBalanceCell.classList.add('text-right');
                    lastDecemberBalanceCell.classList.add('text-right');
                    changesPercentageCell.classList.add('text-center');
                    structurePercentageCell.classList.add('text-center');
                    trendCell.classList.add('text-center'); // Center the trend graph

                    // Apply color to Changes (%) text
                    if (accountData.changes_percentage < 0) {
                        changesPercentageCell.classList.add('text-red-500');
                    } else if (accountData.changes_percentage > 0) {
                        changesPercentageCell.classList.add('text-green-500');
                    }

                    // Add a placeholder for the trend line (will be clickable)
                    const trendSpan = document.createElement('span');
                    trendSpan.classList.add('trend-data', 'cursor-pointer', 'font-bold');
                    trendSpan.textContent = 'View Trend'; // Or a small icon
                    trendSpan.dataset.accountLabel = accountData.label;
                    trendSpan.dataset.reportType = 'financial_performance';
                    trendSpan.dataset.area = area;
                    trendSpan.dataset.branch = branch;
                    trendSpan.dataset.date = date; // Pass the selected date
                    trendSpan.classList.add(accountData.changes_percentage < 0 ? 'text-red-600' : 'text-green-600');
                    trendCell.appendChild(trendSpan);

                    if (isSubAccount) {
                        row.classList.add('sub-account-row', 'hidden', `sub-account-of-fp-performance-${parentKey}`);
                        labelCell.classList.add('item-label', 'sub-account-label-indent');
                        // REMOVED: sub-account-data-indent from numerical cells
                    } else {
                        labelCell.classList.add('item-label');
                        if (accountData.components && accountData.components.length > 0) {
                            labelCell.classList.add('toggle-sub-accounts', 'cursor-pointer');
                            labelCell.dataset.accountKey = `fp-performance-${accountData.label.replace(/\s/g, '-').replace(/[^\w-]/g, '')}`;
                        }
                    }

                    // Apply specific styles for totals
                    if (accountData.type === 'total') {
                        labelCell.classList.add('font-bold', 'total-item');
                        currentBalanceCell.classList.add('font-bold', 'total-item');
                        lastDecemberBalanceCell.classList.add('font-bold', 'total-item');
                        changesPercentageCell.classList.add('font-bold', 'total-item');
                        structurePercentageCell.classList.add('font-bold', 'total-item');
                        trendCell.classList.add('total-item');
                    } else if (accountData.type === 'total_special') { // For "Net Surplus Before Other Items"
                        labelCell.classList.add('font-bold', 'total-item');
                        currentBalanceCell.classList.add('font-bold', 'total-item');
                        lastDecemberBalanceCell.classList.add('font-bold', 'total-item');
                        changesPercentageCell.classList.add('font-bold', 'total-item');
                        structurePercentageCell.classList.add('font-bold', 'total-item');
                        trendCell.classList.add('total-item');
                    } else if (accountData.type === 'grand_total') { // For "Net Surplus For Allocation"
                        labelCell.classList.add('font-bold', 'text-lg', 'grand-total-row');
                        currentBalanceCell.classList.add('font-bold', 'text-lg', 'grand-total-row');
                        lastDecemberBalanceCell.classList.add('font-bold', 'text-lg', 'grand-total-row');
                        changesPercentageCell.classList.add('font-bold', 'text-lg', 'grand-total-row');
                        structurePercentageCell.classList.add('font-bold', 'text-lg', 'grand-total-row');
                        trendCell.classList.add('grand-total-row');
                    }
                };

                // Iterate through the predefined order and render
                IS_ACCOUNTS_ORDER.forEach(item => {
                    if (item.type === 'category') {
                        const headerRow = financialPerformanceBody.insertRow();
                        const headerCell = headerRow.insertCell(0);
                        headerCell.colSpan = 6; // Span all 6 columns
                        headerCell.classList.add('category-header', 'text-gray-600', 'font-semibold', 'mt-4');
                        headerCell.textContent = item.label;
                    } else if (item.type === 'main') {
                        const mainAccountData = financialPerformanceData[item.category][item.key];
                        if (mainAccountData) {
                            addPerformanceRow(mainAccountData, false); // Add main account
                            // Add sub-accounts
                            if (mainAccountData.components && mainAccountData.components.length > 0) {
                                mainAccountData.components.forEach(component => {
                                    addPerformanceRow(component, true, mainAccountData.label.replace(/\s/g, '-').replace(/[^\w-]/g, ''));
                                });
                            }
                        }
                    } else if (item.type === 'total' || item.type === 'total_special' || item.type === 'grand_total') {
                        // For totals, the data is directly under the category or root
                        let totalAccountData;
                        if (item.category) {
                            totalAccountData = financialPerformanceData[item.category][item.key];
                        } else {
                            totalAccountData = financialPerformanceData[item.key];
                        }

                        if (totalAccountData) {
                            // Create a temporary object to pass to addPerformanceRow for consistent handling
                            const formattedTotalData = {
                                label: item.label,
                                current_balance: totalAccountData.current_balance,
                                last_december_balance: totalAccountData.last_december_balance,
                                changes_percentage: totalAccountData.changes_percentage,
                                structure_percentage: totalAccountData.structure_percentage,
                                trend_data: totalAccountData.trend_data, // Pass trend data for totals
                                type: item.type // Pass type for styling
                            };
                            addPerformanceRow(formattedTotalData, false);
                        }
                    }
                });

                financialPerformanceSection.classList.remove('hidden');

                // --- Toggle Sub-accounts Logic (for both sections) ---
                // Re-attach event listeners to the *label cells*
                document.querySelectorAll('.toggle-sub-accounts').forEach(labelCell => {
                    labelCell.removeEventListener('click', handleToggleClick); // Remove existing listeners
                    labelCell.addEventListener('click', handleToggleClick); // Add new listener
                });

                function handleToggleClick() {
                    const accountKey = this.dataset.accountKey;
                    const subAccountRows = document.querySelectorAll(`.sub-account-of-${accountKey}`);
                    subAccountRows.forEach(subRow => {
                        subRow.classList.toggle('hidden');
                    });
                }

                // --- Event Listener for Trend Data Clicks (Modified for in-table dropdown) ---
                document.querySelectorAll('.trend-data').forEach(trendSpan => {
                    trendSpan.removeEventListener('click', handleTrendClick); // Remove existing listeners
                    trendSpan.addEventListener('click', handleTrendClick); // Add new listener
                });

                async function handleTrendClick() {
                    const clickedSpan = this;
                    const accountLabel = clickedSpan.dataset.accountLabel;
                    const reportType = clickedSpan.dataset.reportType;
                    const selectedArea = clickedSpan.dataset.area;
                    const selectedBranch = clickedSpan.dataset.branch;
                    const selectedDate = clickedSpan.dataset.date;

                    const parentRow = clickedSpan.closest('tr');
                    const tbody = parentRow.parentNode;
                    const cacheKey = `${accountLabel}-${reportType}-${selectedArea}-${selectedBranch}-${selectedDate}`;

                    // Check if the trend row for this specific account is already open
                    // We identify the trend row by checking if the next sibling is a .trend-row
                    const isAlreadyOpen = activeTrendRowElement && 
                                         activeTrendRowElement.previousElementSibling === parentRow &&
                                         activeTrendRowElement.classList.contains('trend-row');

                    // If the clicked trend is already open, close it
                    if (isAlreadyOpen) {
                        activeTrendRowElement.remove();
                        if (activeTrendChart) {
                            activeTrendChart.destroy();
                            activeTrendChart = null;
                        }
                        activeTrendRowElement = null; // Clear active reference
                        return; // Exit function
                    }

                    // If a different trend row is open, close it first
                    if (activeTrendRowElement) {
                        activeTrendRowElement.remove();
                        if (activeTrendChart) {
                            activeTrendChart.destroy();
                            activeTrendChart = null;
                        }
                        activeTrendRowElement = null; // Clear active reference
                    }
                    
                    // Create a new row for the trend chart
                    const newTrendRow = tbody.insertRow(parentRow.rowIndex + 1);
                    newTrendRow.classList.add('trend-row');
                    const trendCell = newTrendRow.insertCell(0);
                    trendCell.colSpan = 6; // Span all 6 columns of the table

                    trendCell.innerHTML = `
                        <div class="trend-chart-container p-4">
                            <canvas id="inlineTrendChart"></canvas>
                            <p class="text-gray-600 text-center mt-2" id="inlineTrendDateRange"></p>
                        </div>
                    `;

                    // Store the new trend row as the active one
                    activeTrendRowElement = newTrendRow;

                    const inlineTrendChartCanvas = newTrendRow.querySelector('#inlineTrendChart');
                    const inlineTrendDateRange = newTrendRow.querySelector('#inlineTrendDateRange');

                    let trendData;

                    // Check cache first
                    if (trendDataCache.has(cacheKey)) {
                        console.log(`Using cached trend data for ${accountLabel}`);
                        trendData = trendDataCache.get(cacheKey);
                    } else {
                        // This block should ideally not be reached if populateTrendCache works correctly
                        // but it's a fallback for robustness or if data was not available initially.
                        console.log(`Trend data not found in cache for ${accountLabel}. Attempting to fetch from backend.`);
                        try {
                            // Fallback to fetching from backend if not in cache (should be rare)
                            const trendResponse = await fetch(`${window.FLASK_API_BASE_URL}/financial_statement/trend?area=${selectedArea}&branch=${selectedBranch}&date=${selectedDate}&account_label=${encodeURIComponent(accountLabel)}&report_type=${reportType}`);
                            
                            if (!trendResponse.ok) {
                                const errorText = await trendResponse.text();
                                console.error('HTTP Error fetching trend (fallback):', trendResponse.status, trendResponse.statusText, 'Response Body:', errorText);
                                showAlert(`Failed to fetch trend data (fallback): Server responded with status ${trendResponse.status}.`, 'error');
                                newTrendRow.remove();
                                activeTrendRowElement = null;
                                return;
                            }

                            const trendResult = await trendResponse.json();

                            if (trendResult.status === 'success' && trendResult.data) {
                                trendData = trendResult.data;
                                trendDataCache.set(cacheKey, trendData); // Cache the fallback data
                                console.log("Trend Data Received via fallback and Cached:", trendData);
                                
                            } else {
                                showAlert(trendResult.message || 'No trend data found for this account (fallback).', 'error');
                                newTrendRow.remove();
                                activeTrendRowElement = null;
                                return;
                            }
                        } catch (error) {
                            console.error('Error fetching trend data (fallback):', error);
                            showAlert('An error occurred while fetching trend data (fallback). Please check the console for more details.', 'error');
                            newTrendRow.remove();
                            activeTrendRowElement = null;
                            return;
                        }
                    }
                    
                    // Render the chart if trendData is available
                    if (trendData) {
                        inlineTrendDateRange.textContent = `Trend from ${trendData.dates[0]} to ${trendData.dates[trendData.dates.length - 1]}`;
                        drawTrendChart(inlineTrendChartCanvas, trendData.values, trendData.dates, trendData.account_label);
                    }
                }

            } else {
                showAlert(result.message || 'No financial statement data found for the specified criteria.', 'error'); // Use custom alert for errors
            }
        } catch (error) {
            console.error('Error fetching financial statement:', error);
            showAlert('An error occurred while fetching the financial statement. Please check the console for more details.', 'error');
        } finally {
            // Hide loading indicator with fade-out and remove glow
            loadingIndicator.style.opacity = '0'; 
            logoLoader.classList.remove('glowing');
            setTimeout(() => {
                loadingIndicator.classList.add('hidden'); 
            }, 300);
        }
    });

    // Initial population of dropdowns
    populateDropdowns();
});
