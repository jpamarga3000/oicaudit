// audit_tool/js/tabs/operations_rest.js

(function() {
    const restructuredDateInput = document.getElementById('restructuredDate');
    const generateRestructuredReportButton = document.getElementById('generateRestructuredReportButton');
    const restructuredSummarySection = document.getElementById('restructuredSummarySection');
    const restructuredDetailsSection = document.getElementById('restructuredDetailsSection');
    const restructuredDetailsTableBody = document.querySelector('#restructuredDetailsTable tbody');
    const restructuredLoadingOverlay = document.getElementById('restructuredLoadingOverlay');

    // Summary elements
    const summaryCurrentRemedial = document.getElementById('summaryCurrentRemedial');
    const summaryCurrentRegular = document.getElementById('summaryCurrentRegular');
    const summaryCurrentBRL = document.getElementById('summaryCurrentBRL');
    const summaryCurrentTotal = document.getElementById('summaryCurrentTotal');
    const summaryPastDueRemedial = document.getElementById('summaryPastDueRemedial');
    const summaryPastDueRegular = document.getElementById('summaryPastDueRegular');
    const summaryPastDueBRL = document.getElementById('summaryPastDueBRL');
    const summaryPastDueTotal = document.getElementById('summaryPastDueTotal');

    /**
     * Shows the custom logo loading animation.
     */
    function showLogoAnimation() {
        if (restructuredLoadingOverlay) {
            restructuredLoadingOverlay.classList.add('active');
            document.body.style.overflow = 'hidden'; // Prevent scrolling
        }
    }

    /**
     * Hides the custom logo loading animation.
     */
    function hideLogoAnimation() {
        if (restructuredLoadingOverlay) {
            restructuredLoadingOverlay.classList.remove('active');
            document.body.style.overflow = ''; // Restore scrolling
        }
    }

    /**
     * Formats a number as currency.
     * @param {number} value - The number to format.
     * @returns {string} The formatted currency string.
     */
    function formatCurrency(value) {
        if (typeof value !== 'number' || isNaN(value)) {
            return '0.00';
        }
        return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    /**
     * Updates the state of the Generate Report button.
     */
    function updateGenerateButtonState() {
        if (generateRestructuredReportButton) {
            generateRestructuredReportButton.disabled = !restructuredDateInput.value;
        }
    }

    /**
     * Handles the generation of the Restructured Loans report.
     */
    async function generateRestructuredReport() {
        const selectedDate = restructuredDateInput.value; // YYYY-MM-DD format

        if (!selectedDate) {
            window.showMessage('Please select a date.', 'error');
            return;
        }

        showLogoAnimation();
        generateRestructuredReportButton.disabled = true;
        window.hideMessage();
        restructuredSummarySection.classList.add('hidden');
        restructuredDetailsSection.classList.add('hidden');
        restructuredDetailsTableBody.innerHTML = ''; // Clear previous table data

        try {
            const response = await fetch(`${window.FLASK_API_BASE_URL}/get_restructured_loan_data`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ report_date: selectedDate }),
            });

            const result = await response.json();

            if (response.ok) {
                if (result.summary && result.details) {
                    // Populate Summary
                    summaryCurrentRemedial.textContent = formatCurrency(result.summary.current.REMEDIAL);
                    summaryCurrentRegular.textContent = formatCurrency(result.summary.current.REGULAR);
                    summaryCurrentBRL.textContent = formatCurrency(result.summary.current.BRL);
                    summaryCurrentTotal.textContent = formatCurrency(result.summary.current.TOTAL);

                    summaryPastDueRemedial.textContent = formatCurrency(result.summary.past_due.REMEDIAL);
                    summaryPastDueRegular.textContent = formatCurrency(result.summary.past_due.REGULAR);
                    summaryPastDueBRL.textContent = formatCurrency(result.summary.past_due.BRL);
                    summaryPastDueTotal.textContent = formatCurrency(result.summary.past_due.TOTAL);

                    restructuredSummarySection.classList.remove('hidden');

                    // Populate Details Table
                    restructuredDetailsTableBody.innerHTML = ''; // Clear existing rows
                    if (result.details.length > 0) {
                        result.details.forEach(row => {
                            const tr = document.createElement('tr');
                            tr.className = 'hover:bg-gray-100';
                            tr.innerHTML = `
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${row.BRANCH || ''}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row.CID || ''}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row.NAME || ''}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row.ACCOUNT || ''}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row.TYPE || ''}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">${formatCurrency(row['PRINCIPAL BALANCE'])}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row.DISBDATE || ''}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row['DUE DATE'] || ''}</td>
                            `;
                            restructuredDetailsTableBody.appendChild(tr);
                        });
                        restructuredDetailsSection.classList.remove('hidden');
                    } else {
                        restructuredDetailsTableBody.innerHTML = `<tr><td colspan="8" class="px-6 py-4 text-center text-sm text-gray-500">No restructured loan details found for the selected date.</td></tr>`;
                        restructuredDetailsSection.classList.remove('hidden'); // Still show section, but with no data message
                    }
                    window.showMessage(result.message || 'Restructured Loans report generated successfully!', 'success');
                } else {
                    window.showMessage(result.message || 'No data found for the selected date.', 'info');
                }
            } else {
                window.showMessage(`Error: ${result.message || 'An unknown error occurred.'}`, 'error');
            }
        } catch (error) {
            console.error('Fetch error:', error);
            window.showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
        } finally {
            hideLogoAnimation();
            generateRestructuredReportButton.disabled = false;
        }
    }

    // Event Listeners
    if (restructuredDateInput) {
        restructuredDateInput.addEventListener('change', updateGenerateButtonState);
    }
    if (generateRestructuredReportButton) {
        generateRestructuredReportButton.addEventListener('click', generateRestructuredReport);
    }

    /**
     * Initializes the Restructured Loans tab.
     */
    function initRestructuredLoanTab() {
        console.log('Initializing Restructured Loans Tab...');
        updateGenerateButtonState(); // Set initial button state
        restructuredSummarySection.classList.add('hidden'); // Hide summary on init
        restructuredDetailsSection.classList.add('hidden'); // Hide details on init
        restructuredDetailsTableBody.innerHTML = ''; // Clear table
    }

    // Register this sub-tab's initializer with the main application logic
    window.registerTabInitializer('operationsRestructuredLoan', initRestructuredLoanTab);
})();
