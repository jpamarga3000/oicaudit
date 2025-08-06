// audit_tool/js/tabs/actg_trend.js

(function() { // Start IIFE
    // Maps to store GL Name to Code and Code to Name for autofill
    let glNameMap = new Map(); // Key: GL Name, Value: GL Code
    let glCodeMap = new Map(); // Key: GL Code, Value: GL Name

    // Variable to store the full Trend report data for filtering
    let trendReportData = []; // This should hold the complete, unfiltered data

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
        let formattedValue = '';

        // Automatically add first slash after MM
        if (value.length > 2) {
            formattedValue += value.substring(0, 2) + '/';
            value = value.substring(2);
        } else {
            formattedValue += value;
            value = '';
        }

        // Automatically add second slash after DD
        if (value.length > 2) {
            formattedValue += value.substring(0, 2) + '/';
            value = value.substring(2);
        } else {
            formattedValue += value;
            value = '';
        }

        // Append the remaining digits (for year) up to 4 characters
        formattedValue += value.substring(0, 4);

        input.value = formattedValue;
        updateActgTrendUI(); // Trigger UI update on input change
    }

    /**
     * Formats a GL Code string based on its digit length.
     * @param {string} code - The raw GL Code string (can contain non-digits).
     * @returns {string} The formatted GL Code or raw digits if not 5, 6, 9, or 10 digits.
     */
    function formatGlCode(code) {
        const digits = String(code).replace(/\D/g, ''); // Get only digits

        if (digits.length === 5) {
            return `${digits[0]}-${digits.substring(1, 3)}-${digits.substring(3, 5)}`;
        } else if (digits.length === 6) {
            if (digits.endsWith('0')) {
                const fiveDigits = digits.substring(0, 5);
                return `${fiveDigits[0]}-${fiveDigits.substring(1, 3)}-${fiveDigits.substring(3, 5)}`;
            } else {
                return `${digits[0]}-${digits.substring(1, 3)}-${digits.substring(3, 5)}-${digits.substring(5, 6)}`;
            }
        } else if (digits.length === 9) {
            return `${digits[0]}-${digits.substring(1, 3)}-${digits.substring(3, 5)}-${digits.substring(5, 9)}`;
        } else if (digits.length === 10) {
            return `${digits[0]}-${digits.substring(1, 3)}-${digits.substring(3, 5)}-${digits.substring(5, 10)}`;
        }
        return digits; // For any other length, just return the raw digits.
    }

    /**
     * Loads GL Names and Codes from the backend based on the selected branch.
     * Populates glNameMap, glCodeMap, and the GL Names datalist for the Trend tab.
     * @param {string} branch - The selected branch name.
     */
    async function loadGlNamesAndCodes(branch) {
        const glNamesDatalist = document.getElementById('trendGlNamesDatalist');
        glNamesDatalist.innerHTML = ''; // Clear previous options
        glNameMap.clear();
        glCodeMap.clear();

        if (!branch) {
            console.log('No branch selected, skipping GL names and codes load for Trend tab.');
            return;
        }

        showMessage('Loading GL Names and Codes...', 'info');

        try {
            const response = await fetch(`${FLASK_API_BASE_URL}/get_gl_names_and_codes?branch=${encodeURIComponent(branch)}`);
            const result = await response.json();

            if (response.ok) {
                if (result.data && Array.isArray(result.data)) {
                    result.data.forEach(item => {
                        const glName = item.TITLE ? String(item.TITLE).trim() : '';
                        let glCodeRaw = item['GLACC'] ? String(item['GLACC']).trim() : ''; 

                        if (glCodeRaw.endsWith('.0') && /^\d+$/.test(glCodeRaw.substring(0, glCodeRaw.length - 2))) {
                            glCodeRaw = glCodeRaw.substring(0, glCodeRaw.length - 2);
                        }

                        if (glName && glCodeRaw) {
                            const glCodeFormatted = formatGlCode(glCodeRaw);
                            glNameMap.set(glName, glCodeFormatted);
                            glCodeMap.set(glCodeFormatted, glName);
                            const option = document.createElement('option');
                            option.value = glName;
                            glNamesDatalist.appendChild(option);
                        }
                    });
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
            updateActgTrendUI();
        }
    }

    /**
     * Handles input on the GL Name field to autofill GL Code for the Trend tab.
     */
    function handleTrendGlNameInput() {
        const glNameInput = document.getElementById('trendGlName');
        const glCodeInput = document.getElementById('trendGlCode');
        const selectedGlName = glNameInput.value.trim();

        if (glNameMap.has(selectedGlName)) {
            glCodeInput.value = glNameMap.get(selectedGlName);
        } else {
            glCodeInput.value = '';
        }
        updateActgTrendUI();
    }

    /**
     * Handles input on the GL Code field to autofill GL Name and format the code for the Trend tab.
     */
    function handleTrendGlCodeInput(event) {
        const glNameInput = document.getElementById('trendGlName');
        const glCodeInput = document.getElementById('trendGlCode');
        let currentGlCode = glCodeInput.value;
        let cursorPosition = glCodeInput.selectionStart;

        let formattedGlCode = formatGlCode(currentGlCode);
        glCodeInput.value = formattedGlCode;

        const newLength = formattedGlCode.length;
        const oldLength = currentGlCode.length;
        let adjustedCursorPosition = cursorPosition + (newLength - oldLength);
        adjustedCursorPosition = Math.min(adjustedCursorPosition, newLength);
        adjustedCursorPosition = Math.max(0, adjustedCursorPosition);

        if (event.inputType === 'deleteContentBackward' && cursorPosition > 0 && currentGlCode.charAt(cursorPosition -1) === '-') {
            adjustedCursorPosition--;
        }
        setCaretPosition(glCodeInput, adjustedCursorPosition);

        if (glCodeMap.has(glCodeInput.value)) {
            glNameInput.value = glCodeMap.get(glCodeInput.value);
        } else {
            glNameInput.value = '';
        }
        updateActgTrendUI();
    }

    /**
     * Renders the Trend Report table in the UI.
     * @param {Array<Object>} dataToDisplay - The array of row objects to display.
     */
    function renderTrendReportTable(dataToDisplay) {
        const tableContainer = document.getElementById('trendReportTableContainer');
        if (!tableContainer) {
            console.error('Trend Report table container not found!');
            return;
        }

        tableContainer.innerHTML = ''; // Clear previous content

        if (!dataToDisplay || dataToDisplay.length === 0) {
            tableContainer.innerHTML = '<p class="text-gray-600 text-center">No Trend report data found for the specified criteria.</p>';
            return;
        }

        const table = document.createElement('table');
        table.className = 'min-w-full bg-white border border-gray-300 rounded-lg shadow-md';

        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        const headers = ['DATE', 'BALANCE', 'CHANGE']; // Define headers explicitly

        headers.forEach(headerText => {
            const th = document.createElement('th');
            th.className = 'py-3 px-4 bg-gray-100 text-left text-sm font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300';
            if (['BALANCE', 'CHANGE'].includes(headerText)) {
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
                if (['BALANCE', 'CHANGE'].includes(headerKey)) {
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
     * Copies the content of the Trend Report table to the clipboard in TSV format.
     */
    function copyTrendReportTable() {
        const table = document.querySelector('#trendReportTableContainer table');
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
     * Filters the Trend Report table based on search input.
     */
    function filterTrendReportTable() {
        const searchInput = document.getElementById('trendSearchInput');
        const filter = searchInput.value.toLowerCase();
        
        if (filter === '') {
            renderTrendReportTable(trendReportData);
        } else if (trendReportData.length > 0) {
            const filteredData = trendReportData.filter(row => {
                return Object.values(row).some(value => {
                    return String(value).toLowerCase().includes(filter);
                });
            });
            renderTrendReportTable(filteredData);
        }
    }

    /**
     * Updates the state of the process button and actions bar.
     */
    function updateActgTrendUI() {
        const trendBranch = document.getElementById('trendBranch');
        const trendFromDate = document.getElementById('trendFromDate');
        const trendToDate = document.getElementById('trendToDate');
        const trendGlName = document.getElementById('trendGlName');
        const trendGlCode = document.getElementById('trendGlCode');
        const trendFrequency = document.getElementById('trendFrequency');
        const trendChartDisplayBy = document.getElementById('trendChartDisplayBy'); // NEW
        const processTrendButton = document.getElementById('processTrendButton');
        const copyTrendTableButton = document.getElementById('copyTrendTableButton');
        const trendSearchInput = document.getElementById('trendSearchInput');
        const trendReportActions = document.getElementById('trendReportActions');

        if (processTrendButton && trendBranch && trendFromDate && trendToDate && trendGlName && trendGlCode && trendFrequency && trendChartDisplayBy) { // Added trendChartDisplayBy
            const hasBranch = trendBranch.value.trim() !== '';
            const hasGlName = trendGlName.value.trim() !== '';
            const hasGlCode = trendGlCode.value.trim() !== '';
            const hasFrequency = trendFrequency.value.trim() !== '';
            const hasChartDisplayBy = trendChartDisplayBy.value.trim() !== ''; // Check new dropdown
            const isValidFromDate = isValidDate(trendFromDate.value.trim());
            const isValidToDate = isValidDate(trendToDate.value.trim());

            processTrendButton.disabled = !(
                hasBranch &&
                isValidFromDate &&
                isValidToDate &&
                hasGlName &&
                hasGlCode &&
                hasFrequency &&
                hasChartDisplayBy // Include new dropdown in validation
            );
        }

        const tableExists = document.querySelector('#trendReportTableContainer table');
        if (trendReportActions) {
            if (tableExists) {
                trendReportActions.classList.remove('hidden');
            } else {
                trendReportActions.classList.add('hidden');
            }
        }
        if (copyTrendTableButton) {
            copyTrendTableButton.disabled = !tableExists;
        }
        if (trendSearchInput) {
            trendSearchInput.disabled = !tableExists;
            if (!tableExists) trendSearchInput.value = '';
        }
    }

    /**
     * Handles the processing request for Accounting Trend data.
     */
    async function processActgTrend() {
        const trendBranch = document.getElementById('trendBranch');
        const trendFromDate = document.getElementById('trendFromDate');
        const trendToDate = document.getElementById('trendToDate');
        const trendGlName = document.getElementById('trendGlName');
        const trendGlCode = document.getElementById('trendGlCode');
        const trendFrequency = document.getElementById('trendFrequency');
        const trendChartDisplayBy = document.getElementById('trendChartDisplayBy'); // NEW
        const processTrendButton = document.getElementById('processTrendButton');
        const trendReportTableContainer = document.getElementById('trendReportTableContainer');
        const trendChartContainer = document.getElementById('trendChartContainer');
        const copyTrendTableButton = document.getElementById('copyTrendTableButton');
        const trendSearchInput = document.getElementById('trendSearchInput');
        const trendReportActions = document.getElementById('trendReportActions');
        const chartPlaceholderText = document.getElementById('chartPlaceholderText'); // Get the placeholder text element


        const branch = trendBranch.value.trim();
        const fromDate = trendFromDate.value.trim();
        const toDate = trendToDate.value.trim();
        const glName = trendGlName.value.trim();
        const glCode = trendGlCode.value.trim();
        const frequency = trendFrequency.value.trim();
        const chartDisplayBy = trendChartDisplayBy.value.trim(); // NEW

        if (!branch || !isValidDate(fromDate) || !isValidDate(toDate) || !glName || !glCode || !frequency || !chartDisplayBy) { // Added chartDisplayBy
            showMessage('Please fill all required fields and ensure dates are in MM/DD/YYYY format.', 'error');
            return;
        }

        if (processTrendButton) processTrendButton.disabled = true;
        if (copyTrendTableButton) copyTrendTableButton.disabled = true;
        if (trendSearchInput) { trendSearchInput.disabled = true; trendSearchInput.value = ''; }
        if (trendReportActions) trendReportActions.classList.add('hidden');

        showMessage('Generating Trend report... This may take a moment.', 'loading');
        trendReportTableContainer.innerHTML = '<p class="text-gray-500 text-center">Report table will appear here after generation.</p>'; // Reset table content

        // Hide chart placeholder and destroy existing chart immediately before new generation
        if (chartPlaceholderText) {
            chartPlaceholderText.style.display = 'block'; // Show placeholder initially
        }
        if (window.trendChartInstance) { // Destroy previous chart instance
            window.trendChartInstance.destroy();
        }
        const chartCanvas = document.getElementById('trendChart'); // Get canvas element
        if (chartCanvas) {
            chartCanvas.style.display = 'none'; // Hide canvas until data is ready
            // Clear any previous drawing on the canvas if it was hidden
            const ctx = chartCanvas.getContext('2d');
            ctx.clearRect(0, 0, chartCanvas.width, chartCanvas.height);
        }


        trendReportData = []; // Clear stored data on new processing

        const formData = new FormData();
        formData.append('branch', branch);
        formData.append('from_date', fromDate);
        formData.append('to_date', toDate);
        formData.append('gl_code', glCode); // Send formatted GL Code
        formData.append('frequency', frequency);

        try {
            const response = await fetch(`${FLASK_API_BASE_URL}/process_accounting_trend`, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                if (result.data && result.data.length > 0) {
                    trendReportData = result.data; // Store the full data
                    renderTrendReportTable(trendReportData); // Render the table

                    // --- Chart.js Integration Starts Here ---
                    if (chartPlaceholderText) {
                        chartPlaceholderText.style.display = 'none'; // Hide placeholder
                    }
                    if (chartCanvas) {
                        chartCanvas.style.display = 'block'; // Show canvas
                    }

                    const ctx = document.getElementById('trendChart').getContext('2d');

                    // Destroy existing chart instance if it exists to prevent re-rendering issues
                    if (window.trendChartInstance) {
                        window.trendChartInstance.destroy();
                    }

                    // Prepare data for Chart.js based on selected display option
                    const labels = trendReportData.map(row => row.DATE); // Use DATE from your data
                    let dataPoints;
                    let chartLabel;

                    if (chartDisplayBy === 'BALANCE') {
                        dataPoints = trendReportData.map(row => row.BALANCE_RAW);
                        chartLabel = 'Balance';
                    } else if (chartDisplayBy === 'CHANGE') {
                        dataPoints = trendReportData.map(row => row.CHANGE_RAW);
                        chartLabel = 'Change';
                    } else {
                        dataPoints = [];
                        chartLabel = 'N/A';
                    }

                    // Create new chart instance
                    window.trendChartInstance = new Chart(ctx, {
                        type: 'bar', // Can be 'line' or 'bar'
                        data: {
                            labels: labels,
                            datasets: [{
                                label: chartLabel, // Dynamic label
                                data: dataPoints,
                                borderColor: '#4f46e5', // Theme color
                                backgroundColor: 'rgba(79, 70, 229, 0.2)', // Semi-transparent fill
                                fill: true,
                                tension: 0.1 // For a smooth line if type is 'line'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false, // Important for custom height/width
                            scales: {
                                x: {
                                    title: {
                                        display: true,
                                        text: 'Date'
                                    }
                                },
                                y: {
                                    title: {
                                        display: true,
                                        text: chartLabel // Dynamic Y-axis title
                                    },
                                    beginAtZero: false, // Set to true if your balance/change can go to 0 or start at 0
                                    ticks: {
                                        callback: function(value, index, ticks) {
                                            // Format Y-axis ticks as currency
                                            return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'PHP' }).format(value);
                                        }
                                    }
                                }
                            },
                            plugins: {
                                tooltip: {
                                    callbacks: {
                                        label: function(context) {
                                            let label = context.dataset.label || '';
                                            if (label) {
                                                label += ': ';
                                            }
                                            if (context.parsed.y !== null) {
                                                label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'PHP' }).format(context.parsed.y);
                                            }
                                            return label;
                                        }
                                    }
                                }
                            }
                        }
                    });
                    // --- Chart.js Integration Ends Here ---

                    showMessage(result.message, 'success');
                } else {
                    trendReportData = [];
                    renderTrendReportTable([]);
                    // If no data, ensure chart canvas is hidden and placeholder is visible
                    if (chartCanvas) {
                        chartCanvas.style.display = 'none';
                    }
                    if (chartPlaceholderText) {
                        chartPlaceholderText.style.display = 'block';
                    }
                    if (window.trendChartInstance) {
                        window.trendChartInstance.destroy();
                    }
                    showMessage(result.message || 'No data found for the specified criteria.', 'info');
                }
            } else {
                showMessage(`Error: ${result.message}`, 'error');
                trendReportTableContainer.innerHTML = '<p class="text-gray-500 text-center">Report table will appear here after generation.</p>';
                // On error, hide chart and show placeholder
                if (chartCanvas) {
                    chartCanvas.style.display = 'none';
                }
                if (chartPlaceholderText) {
                    chartPlaceholderText.style.display = 'block';
                }
                if (window.trendChartInstance) {
                    window.trendChartInstance.destroy();
                }
                trendReportData = [];
            }
        } catch (error) {
            console.error('Fetch error:', error);
            showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
            trendReportTableContainer.innerHTML = '<p class="text-gray-500 text-center">Report table will appear here after generation.</p>';
            // On unexpected error, hide chart and show placeholder
            if (chartCanvas) {
                chartCanvas.style.display = 'none';
            }
            if (chartPlaceholderText) {
                chartPlaceholderText.style.display = 'block';
            }
            if (window.trendChartInstance) {
                window.trendChartInstance.destroy();
            }
            trendReportData = [];
        } finally {
            if (processTrendButton) processTrendButton.disabled = false;
            updateActgTrendUI();
        }
    }

    /**
     * Initializes the Accounting Trend sub-tab: attaches event listeners and performs initial UI update.
     */
    function initActgTrendTab() {
        console.log('Initializing Accounting Trend Tab...');

        const trendBranchInput = document.getElementById('trendBranch');
        const trendFromDateInput = document.getElementById('trendFromDate');
        const trendToDateInput = document.getElementById('trendToDate');
        const trendGlNameInput = document.getElementById('trendGlName');
        const trendGlCodeInput = document.getElementById('trendGlCode');
        const trendFrequencyInput = document.getElementById('trendFrequency');
        const trendChartDisplayBy = document.getElementById('trendChartDisplayBy'); // NEW
        const processTrendButton = document.getElementById('processTrendButton');
        const copyTrendTableButton = document.getElementById('copyTrendTableButton');
        const trendSearchInput = document.getElementById('trendSearchInput');
        const chartPlaceholderText = document.getElementById('chartPlaceholderText'); // Get the placeholder text element
        const chartCanvas = document.getElementById('trendChart'); // Get the canvas element

        // Clear report containers on tab initialization
        document.getElementById('trendReportTableContainer').innerHTML = '<p class="text-gray-500 text-center">Report table will appear here after generation.</p>';
        
        // Ensure chart is hidden and placeholder is visible on initialization if no data is present
        if (chartCanvas) {
            chartCanvas.style.display = 'none';
        }
        if (chartPlaceholderText) {
            chartPlaceholderText.style.display = 'block';
        }
        if (window.trendChartInstance) {
            window.trendChartInstance.destroy(); // Destroy any lingering chart instance
        }


        // If trendReportData already has data, re-render it
        if (trendReportData.length > 0) {
            renderTrendReportTable(trendReportData);
            
            // Re-render chart if data exists
            if (chartPlaceholderText) {
                chartPlaceholderText.style.display = 'none'; // Hide placeholder
            }
            if (chartCanvas) {
                chartCanvas.style.display = 'block'; // Show canvas
            }
            const ctx = document.getElementById('trendChart').getContext('2d');

            // Determine data points and label based on current selection
            const chartDisplayByValue = trendChartDisplayBy ? trendChartDisplayBy.value : 'BALANCE'; // Default to BALANCE
            let dataPoints;
            let chartLabel;

            if (chartDisplayByValue === 'BALANCE') {
                dataPoints = trendReportData.map(row => row.BALANCE_RAW);
                chartLabel = 'Balance';
            } else if (chartDisplayByValue === 'CHANGE') {
                dataPoints = trendReportData.map(row => row.CHANGE_RAW);
                chartLabel = 'Change';
            } else {
                dataPoints = [];
                chartLabel = 'N/A';
            }

            window.trendChartInstance = new Chart(ctx, {
                type: 'bar', // Can be 'line' or 'bar'
                data: {
                    labels: trendReportData.map(row => row.DATE),
                    datasets: [{
                        label: chartLabel,
                        data: dataPoints,
                        borderColor: '#4f46e5',
                        backgroundColor: 'rgba(79, 70, 229, 0.2)',
                        fill: true,
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Date'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: chartLabel
                            },
                            beginAtZero: false,
                            ticks: {
                                callback: function(value, index, ticks) {
                                    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'PHP' }).format(value);
                                }
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    if (context.parsed.y !== null) {
                                        label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'PHP' }).format(context.parsed.y);
                                    }
                                    return label;
                                }
                            }
                        }
                    }
                }
            });


            if (trendSearchInput) trendSearchInput.disabled = false;
        } else {
            trendReportData = [];
        }

        // Attach event listeners
        if (trendFromDateInput && !trendFromDateInput.dataset.listenerAttached) {
            trendFromDateInput.addEventListener('input', formatDateInput);
            trendFromDateInput.dataset.listenerAttached = 'true';
        }
        if (trendToDateInput && !trendToDateInput.dataset.listenerAttached) {
            trendToDateInput.addEventListener('input', formatDateInput);
            trendToDateInput.dataset.listenerAttached = 'true';
        }
        if (trendGlNameInput && !trendGlNameInput.dataset.listenerAttached) {
            trendGlNameInput.addEventListener('input', handleTrendGlNameInput);
            trendGlNameInput.dataset.listenerAttached = 'true';
        }
        if (trendGlCodeInput && !trendGlCodeInput.dataset.listenerAttached) {
            trendGlCodeInput.addEventListener('input', handleTrendGlCodeInput);
            trendGlCodeInput.dataset.listenerAttached = 'true';
        }
        if (trendBranchInput && !trendBranchInput.dataset.listenerAttached) {
            trendBranchInput.addEventListener('change', () => {
                updateActgTrendUI();
                loadGlNamesAndCodes(trendBranchInput.value.trim());
            });
            trendBranchInput.dataset.listenerAttached = 'true';
        }
        if (trendFrequencyInput && !trendFrequencyInput.dataset.listenerAttached) {
            trendFrequencyInput.addEventListener('change', updateActgTrendUI);
            trendFrequencyInput.dataset.listenerAttached = 'true';
        }
        // NEW: Listener for chart display option
        if (trendChartDisplayBy && !trendChartDisplayBy.dataset.listenerAttached) {
            trendChartDisplayBy.addEventListener('change', () => {
                if (trendReportData.length > 0) {
                    // Re-render chart with new data selection
                    const chartDisplayByValue = trendChartDisplayBy.value;
                    let dataPoints;
                    let chartLabel;

                    if (chartDisplayByValue === 'BALANCE') {
                        dataPoints = trendReportData.map(row => row.BALANCE_RAW);
                        chartLabel = 'Balance';
                    } else if (chartDisplayByValue === 'CHANGE') {
                        dataPoints = trendReportData.map(row => row.CHANGE_RAW);
                        chartLabel = 'Change';
                    }

                    if (window.trendChartInstance) {
                        window.trendChartInstance.data.datasets[0].data = dataPoints;
                        window.trendChartInstance.data.datasets[0].label = chartLabel;
                        window.trendChartInstance.options.scales.y.title.text = chartLabel; // Update Y-axis title
                        window.trendChartInstance.update();
                    }
                }
                updateActgTrendUI();
            });
            trendChartDisplayBy.dataset.listenerAttached = 'true';
        }
        if (processTrendButton && !processTrendButton.dataset.listenerAttached) {
            processTrendButton.addEventListener('click', processActgTrend);
            processTrendButton.dataset.listenerAttached = 'true';
        }
        if (copyTrendTableButton && !copyTrendTableButton.dataset.listenerAttached) {
            copyTrendTableButton.addEventListener('click', copyTrendReportTable);
            copyTrendTableButton.dataset.listenerAttached = 'true';
        }
        if (trendSearchInput && !trendSearchInput.dataset.listenerAttached) {
            trendSearchInput.addEventListener('input', filterTrendReportTable);
            trendSearchInput.dataset.listenerAttached = 'true';
        }

        // Initial UI update and load GL data if a branch is already selected
        updateActgTrendUI();
        if (trendBranchInput.value.trim()) {
            loadGlNamesAndCodes(trendBranchInput.value.trim());
        }
    }

    registerTabInitializer('actgTrend', initActgTrendTab);
})(); // End IIFE
