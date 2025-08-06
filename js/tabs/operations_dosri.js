document.addEventListener('DOMContentLoaded', function() {
    // Base URL for the Flask API backend.
    // IMPORTANT: This should be configured to your actual backend server address.
    // This is now sourced from utils.js
    const API_BASE_URL = window.FLASK_API_BASE_URL;

    // --- Common Utility Functions (Exposed globally for other modules) ---
    /**
     * Displays a customizable message box.
     * @param {string} message - The message to display.
     * @param {'success'|'error'|'warning'|'info'} type - The type of message, which determines styling.
     */
    window.showMessageBox = function(message, type = 'success') {
        const messageBox = document.getElementById('messageBox');
        const messageBoxContent = messageBox.querySelector('div');
        messageBoxContent.textContent = message;
        // Remove existing color classes
        messageBoxContent.classList.remove('bg-green-500', 'bg-red-500', 'bg-yellow-500', 'bg-blue-500');

        // Add new color class based on message type
        if (type === 'success') {
            messageBoxContent.classList.add('bg-green-500');
        } else if (type === 'error') {
            messageBoxContent.classList.add('bg-red-500');
        } else if (type === 'warning') {
            messageBoxContent.classList.add('bg-yellow-500');
        } else if (type === 'info') {
            messageBoxContent.classList.add('bg-blue-500');
        }
        messageBox.classList.remove('hidden');

        // Hide message box after 5 seconds
        setTimeout(() => {
            messageBox.classList.add('hidden');
        }, 5000);
    };

    /**
     * Provides a custom confirmation dialog using a prompt.
     * @param {string} message - The message to display in the confirmation.
     * @returns {Promise<boolean>} - Resolves to true if confirmed ('yes'), false otherwise.
     */
    window.customConfirm = function(message) {
        return new Promise((resolve) => {
            // Using prompt as a simple custom confirm; for better UX, consider a custom modal.
            const result = prompt(message + " (Type 'yes' to confirm, anything else to cancel)");
            resolve(result && result.toLowerCase() === 'yes');
        });
    };

    /**
     * Opens a modal element.
     * @param {HTMLElement} modalElement - The modal element to open.
     */
    window.openModal = function(modalElement) {
        modalElement.classList.remove('hidden');
        modalElement.classList.add('flex');
    };

    /**
     * Closes a modal element.
     * @param {HTMLElement} modalElement - The modal element to close.
     */
    window.closeModal = function(modalElement) {
        modalElement.classList.add('hidden');
        modalElement.classList.remove('flex');
    };

    /**
     * Formats a numeric value as Philippine Peso currency.
     * @param {number|string} value - The value to format.
     * @returns {string} - The formatted currency string.
     */
    window.formatCurrency = function(value) {
        if (typeof value !== 'number') {
            value = parseFloat(value);
        }
        return isNaN(value) ? 'N/A' : value.toLocaleString('en-PH', {
            style: 'currency',
            currency: 'PHP'
        });
    };

    /**
     * Copies table data to the clipboard in a tab-separated format.
     * Includes headers and handles currency formatting removal for raw values.
     * @param {string} tableBodyId - The ID of the table body element.
     */
    window.copyTableToClipboard = function(tableBodyId) {
        const tableBody = document.getElementById(tableBodyId);
        if (!tableBody) {
            window.showMessageBox('Table body not found for copying.', 'error');
            return;
        }

        if (tableBody.rows.length === 0) {
            window.showMessageBox('No data in the table to copy.', 'warning');
            return;
        }

        let csv = [];
        const table = tableBody.closest('table');
        if (!table) {
            window.showMessageBox('Parent table not found for headers.', 'error');
            return;
        }
        // Get headers from thead
        const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.innerText.trim());
        csv.push(headers.join('\t'));

        // Iterate through rows and cells to get data
        Array.from(tableBody.rows).forEach(row => {
            const rowData = Array.from(row.cells).map(cell => {
                let text = cell.innerText.trim();
                // Remove currency symbol and commas for numeric values
                if (text.startsWith('₱')) {
                    text = text.replace('₱', '').replace(/,/g, '');
                }
                // Replace newlines with spaces for single-line output
                text = text.replace(/\n/g, ' ');
                return text;
            });
            csv.push(rowData.join('\t'));
        });

        const csvString = csv.join('\n');

        // Create a temporary textarea to copy text to clipboard
        const textarea = document.createElement('textarea');
        textarea.value = csvString;
        textarea.style.position = 'absolute';
        textarea.style.left = '-9999px';
        textarea.style.top = '0';
        document.body.appendChild(textarea);
        textarea.select(); // Select the text
        try {
            const successful = document.execCommand('copy'); // Execute copy command
            if (successful) {
                window.showMessageBox('Table data copied to clipboard!', 'success');
            } else {
                window.showMessageBox('Failed to copy table data. Please try manually (Ctrl+C).', 'warning');
                console.warn('document.execCommand("copy") returned false.');
            }
        } catch (err) {
            console.error('Error during document.execCommand("copy"):', err);
            window.showMessageBox('An error occurred while copying table data. Please try manually.', 'error');
        } finally {
            document.body.removeChild(textarea); // Clean up the temporary textarea
        }
    };

    // --- DOSRI Elements ---
    const dosriListModal = document.getElementById('dosriListModal');
    const closeDosriListModalBtn = document.getElementById('closeDosriListModalBtn');
    const openDosriListBtn = document.getElementById('openDosriListBtn');
    const dosriTableBody = document.getElementById('dosriListTableBody');
    const dosriModal = document.getElementById('dosriModal');
    const modalTitle = document.getElementById('modalTitle');
    const dosriForm = document.getElementById('dosriForm');
    const addDosriBtn = document.getElementById('addDosriBtn');
    const cancelDosriBtn = document.getElementById('cancelDosriBtn'); // Used by DOSRI add/edit modal
    const dosriIdInput = document.getElementById('dosriId');
    const cidInput = document.getElementById('cid');
    const branchInput = document.getElementById('branch');
    const nameInput = document.getElementById('name');
    const typeInput = document.getElementById('type');
    const positionInput = document.getElementById('position');
    const relatedToInput = document.getElementById('relatedTo');
    const relationshipInput = document = document.getElementById('relationship');
    const uploadCsvBtn = document.getElementById('uploadCsvBtn');
    const uploadCsvModal = document.getElementById('uploadCsvModal');
    const uploadCsvForm = document.getElementById('uploadCsvForm');
    const cancelUploadCsvBtn = document.getElementById('cancelUploadCsvBtn'); // Used by CSV upload modal
    const dosriCsvFileInput = document.getElementById('dosriCsvFile');
    const overrideAllRadio = document.getElementById('overrideAll');
    const appendRadio = document.getElementById('append');
    const dosriSearchInput = document.getElementById('dosriSearchInput');
    const dosriTypeFilter = document.getElementById('dosriTypeFilter'); // Single-select for DOSRI List modal

    // --- Summary Report Elements (DOSRI Specific) ---
    const loanBalancesSummaryTiles = document.getElementById('loan_balances_summary_tiles');
    const loanCurrentBalanceAmount = document.getElementById('loan_current_balance_amount');
    const loanTotalPastDueAmount = document.getElementById('loan_total_past_due_amount');
    const loanPastDueBreakdownTiles = document.getElementById('loan_past_due_breakdown_tiles');
    const pastDue1_30DaysAmount = document.getElementById('past_due_1_30_days_amount');
    const pastDue31_60DaysAmount = document.getElementById('past_due_31_60_days_amount');
    const pastDue61_90DaysAmount = document.getElementById('past_due_61_90_days_amount');
    const pastDue91_120DaysAmount = document.getElementById('past_due_91_120_days_amount');
    const pastDue121_180DaysAmount = document.getElementById('past_due_121_180_days_amount');
    const pastDue181_365DaysAmount = document.getElementById('past_due_181_365_days_amount');
    const pastDueOver365DaysAmount = document.getElementById('past_due_over_365_days_amount');

    // NEW: DOSRI Type Breakdown elements for Loan Balances
    const loanCurrentDAmount = document.getElementById('loan_current_d_amount');
    const loanCurrentOAmount = document.getElementById('loan_current_o_amount');
    const loanCurrentSAmount = document.getElementById('loan_current_s_amount');
    const loanCurrentRIAmount = document.getElementById('loan_current_ri_amount');

    const loanPastDueDAmount = document.getElementById('loan_past_due_d_amount');
    const loanPastDueOAmount = document.getElementById('loan_past_due_o_amount');
    const loanPastDueSAmount = document.getElementById('loan_past_due_s_amount');
    const loanPastDueRIAmount = document.getElementById('loan_past_due_ri_amount');

    const pastDue1_30_DAmount = document.getElementById('past_due_1_30_d_amount');
    const pastDue1_30_OAmount = document.getElementById('past_due_1_30_o_amount');
    const pastDue1_30_SAmount = document.getElementById('past_due_1_30_s_amount');
    const pastDue1_30_RIAmount = document.getElementById('past_due_1_30_ri_amount');

    const pastDue31_60_DAmount = document.getElementById('past_due_31_60_d_amount');
    const pastDue31_60_OAmount = document.getElementById('past_due_31_60_o_amount');
    const pastDue31_60_SAmount = document.getElementById('past_due_31_60_s_amount');
    const pastDue31_60_RIAmount = document.getElementById('past_due_31_60_ri_amount');

    const pastDue61_90_DAmount = document.getElementById('past_due_61_90_d_amount');
    const pastDue61_90_OAmount = document.getElementById('past_due_61_90_o_amount');
    const pastDue61_90_SAmount = document.getElementById('past_due_61_90_s_amount');
    const pastDue61_90_RIAmount = document.getElementById('past_due_61_90_ri_amount');

    const pastDue91_120_DAmount = document.getElementById('past_due_91_120_d_amount');
    const pastDue91_120_OAmount = document.getElementById('past_due_91_120_o_amount');
    const pastDue91_120_SAmount = document.getElementById('past_due_91_120_s_amount');
    const pastDue91_120_RIAmount = document.getElementById('past_due_91_120_ri_amount');

    const pastDue121_180_DAmount = document.getElementById('past_due_121_180_d_amount');
    const pastDue121_180_OAmount = document.getElementById('past_due_121_180_o_amount');
    const pastDue121_180_SAmount = document.getElementById('past_due_121_180_s_amount');
    const pastDue121_180_RIAmount = document.getElementById('past_due_121_180_ri_amount');

    const pastDue181_365_DAmount = document.getElementById('past_due_181_365_d_amount');
    const pastDue181_365_OAmount = document.getElementById('past_due_181_365_o_amount');
    const pastDue181_365_SAmount = document.getElementById('past_due_181_365_s_amount');
    const pastDue181_365_RIAmount = document.getElementById('past_due_181_365_ri_amount');

    const pastDueOver365_DAmount = document.getElementById('past_due_over_365_d_amount');
    const pastDueOver365_OAmount = document.getElementById('past_due_over_365_o_amount');
    const pastDueOver365_SAmount = document.getElementById('past_due_over_365_s_amount');
    const pastDueOver365_RIAmount = document.getElementById('past_due_over_365_ri_amount');


    const loanBalancesStatus = document.getElementById('loan_balances_status');
    const loanBalancesError = document.getElementById('loan_balances_error');
    const loanBalancesNoData = document.getElementById('loan_balances_no_data');

    const depositStatus = document.getElementById('deposit_status');
    const depositError = document.getElementById('deposit_error');
    const depositNoData = document.getElementById('deposit_no_data');
    const depositTilesContainer = document.getElementById('deposit_liabilities_tiles');
    const regularSavingsAmount = document.getElementById('regular_savings_amount');
    const atmSavingsAmount = document.getElementById('atm_savings_amount');
    const shareCapitalAmount = document.getElementById('share_capital_amount');
    const timeDepositsAmount = document.getElementById('time_deposits_amount');
    const youthSavingsAmount = document.getElementById('youth_savings_amount');
    const specialDepositsAmount = document.getElementById('special_deposits_amount');
    
    const regularSavingsCount = document.getElementById('regular_savings_count');
    const atmSavingsCount = document.getElementById('atm_savings_count');
    const shareCapitalCount = document.getElementById('share_capital_count');
    const timeDepositsCount = document.getElementById('time_deposits_count');
    const youthSavingsCount = document.getElementById('youth_savings_count');
    const specialDepositsCount = document.getElementById('special_deposits_count');

    // NEW: DOSRI Type Breakdown elements for Deposit Liabilities
    const regularSavingsDAmount = document.getElementById('regular_savings_d_amount');
    const regularSavingsOAmount = document.getElementById('regular_savings_o_amount');
    const regularSavingsSAmount = document.getElementById('regular_savings_s_amount');
    const regularSavingsRIAmount = document.getElementById('regular_savings_ri_amount');

    const atmSavingsDAmount = document.getElementById('atm_savings_d_amount');
    const atmSavingsOAmount = document.getElementById('atm_savings_o_amount');
    const atmSavingsSAmount = document.getElementById('atm_savings_s_amount');
    const atmSavingsRIAmount = document.getElementById('atm_savings_ri_amount');

    const shareCapitalDAmount = document.getElementById('share_capital_d_amount');
    const shareCapitalOAmount = document.getElementById('share_capital_o_amount');
    const shareCapitalSAmount = document.getElementById('share_capital_s_amount');
    const shareCapitalRIAmount = document.getElementById('share_capital_ri_amount');

    const timeDepositsDAmount = document.getElementById('time_deposits_d_amount');
    const timeDepositsOAmount = document.getElementById('time_deposits_o_amount');
    const timeDepositsSAmount = document.getElementById('time_deposits_s_amount');
    const timeDepositsRIAmount = document.getElementById('time_deposits_ri_amount');

    const youthSavingsDAmount = document.getElementById('youth_savings_d_amount');
    const youthSavingsOAmount = document.getElementById('youth_savings_o_amount');
    const youthSavingsSAmount = document.getElementById('youth_savings_s_amount');
    const youthSavingsRIAmount = document.getElementById('youth_savings_ri_amount');

    const specialDepositsDAmount = document.getElementById('special_deposits_d_amount');
    const specialDepositsOAmount = document.getElementById('special_deposits_o_amount');
    const specialDepositsSAmount = document.getElementById('special_deposits_s_amount');
    const specialDepositsRIAmount = document.getElementById('special_deposits_ri_amount');


    const loanBalanceTableBody = document.getElementById('loan-balance-table-body');
    const loanBalanceSearchInput = document.getElementById('loanBalanceSearchInput');
    const copyLoanBalanceTableBtn = document.getElementById('copyLoanBalanceTableBtn');
    const downloadDosriExcelBtn = document.getElementById('downloadDosriExcelBtn'); // This button downloads ALL data (DOSRI and Former Emp)

    const depositLiabilitiesTableBody = document.getElementById('deposit-liabilities-table-body');
    const depositLiabilitiesSearchInput = document.getElementById('depositLiabilitiesSearchInput');
    const copyDepositLiabilitiesTableBtn = document.getElementById('copyDepositLiabilitiesTableBtn');

    // Store fetched detail data for searching/copying (DOSRI specific)
    let currentDosriLoanBalanceDetails = [];
    let currentDosriDepositLiabilitiesDetails = [];

    // Store fetched detail data for searching/copying (Former Employee specific)
    // These are exposed globally to allow operations_form_emp.js to update them.
    window.currentFormEmpLoanBalanceDetails = [];
    window.currentFormEmpDepositLiabilitiesDetails = [];

    // NEW: Get reference to the Generate Reports button and the new multi-select filter
    const generateReportsBtn = document.getElementById('generateReportsBtn');
    const dosriTypeMultiFilter = document.getElementById('dosriTypeMultiFilter'); // Multi-select for report generation
    const reportDateInput = document.getElementById('reportDate'); // NEW: Reference to the date input

    // Helper function to initialize breakdown sums
    function initializeBreakdownSums() {
        return {
            'director': 0.0,
            'officer': 0.0,
            'staff': 0.0,
            'related interest': 0.0
        };
    }

    // Helper function to update breakdown elements
    function updateBreakdownDisplay(prefix, sums) {
        document.getElementById(`${prefix}_d_amount`).innerText = window.formatCurrency(sums.director);
        document.getElementById(`${prefix}_o_amount`).innerText = window.formatCurrency(sums.officer);
        document.getElementById(`${prefix}_s_amount`).innerText = window.formatCurrency(sums.staff);
        document.getElementById(`${prefix}_ri_amount`).innerText = window.formatCurrency(sums['related interest']);
    }

    /**
     * Fetches the list of DOSRI members from the backend for summary reports,
     * optionally filtered by selected types.
     * @param {string[]} selectedTypes - An array of selected DOSRI types to filter by.
     * @returns {Promise<Array<Object>>} A promise that resolves to an array of DOSRI members.
     */
    window.fetchDosriListForSummary = async function(selectedTypes = []) {
        try {
            const params = new URLSearchParams();
            // Append each selected type as a separate query parameter
            selectedTypes.forEach(type => params.append('type_filter', type));
            
            const response = await fetch(`${API_BASE_URL}/api/dosri_list?${params.toString()}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return data.dosri_members || [];
        } catch (error) {
            console.error('Error fetching DOSRI list for summary:', error);
            window.showMessageBox('Error fetching DOSRI list for summary reports.', 'error');
            return [];
        }
    };

    /**
     * Fetches all DOSRI data for the list modal, with optional search and type filters.
     * @param {string} searchTerm - The search term to filter records.
     * @param {string} typeFilter - The single type filter for the DOSRI list modal.
     * @returns {Promise<Array<Object>>} A promise that resolves to an array of DOSRI members.
     */
    window.fetchDosriData = async function(searchTerm = '', typeFilter = '') {
        dosriTableBody.innerHTML = '<tr><td colspan="9" class="px-6 py-4 text-center text-gray-500">Loading DOSRI data...</td></tr>';

        const params = new URLSearchParams();
        if (searchTerm) {
            params.append('search_term', searchTerm);
        }
        if (typeFilter) {
            params.append('type_filter', typeFilter);
        }

        const url = `${API_BASE_URL}/api/dosri?${params.toString()}`;

        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            window.renderDosriTable(data.dosri_list);
            return data.dosri_list; // Return data for potential use in Excel download
        } catch (error) {
            console.error('Error fetching DOSRI data:', error);
            dosriTableBody.innerHTML = '<tr><td colspan="9" class="px-6 py-4 text-center text-red-500">Failed to load data. Please try again.</td></tr>';
            window.showMessageBox('Failed to load DOSRI data. Check server logs.', 'error');
            return []; // Return empty array on error
        }
    };

    /**
     * Renders the DOSRI list table with the provided data.
     * Expects DOSRI member objects to have lowercase properties (id, cid, branch, name, type, etc.).
     * @param {Array<Object>} dosriList - An array of DOSRI member objects.
     */
    window.renderDosriTable = function(dosriList) {
        dosriTableBody.innerHTML = '';
        if (dosriList.length === 0) {
            dosriTableBody.innerHTML = '<tr><td colspan="9" class="px-6 py-4 text-center text-gray-500">No DOSRI records found.</td></tr>';
            return;
        }

        dosriList.forEach(dosri => {
            const row = document.createElement('tr');
            row.classList.add('bg-white', 'border-b', 'dark:bg-gray-800', 'dark:border-gray-700', 'hover:bg-gray-50', 'dark:hover:bg-gray-600');
            row.innerHTML = `
                <td class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">${dosri.id || ''}</td>
                <td class="px-6 py-4">${dosri.cid || ''}</td>
                <td class="px-6 py-4">${dosri.branch || ''}</td>
                <td class="px-6 py-4">${dosri.name || ''}</td>
                <td class="px-6 py-4">${dosri.type || ''}</td>
                <td class="px-6 py-4">${dosri.position || ''}</td>
                <td class="px-6 py-4">${dosri.related_to || ''}</td>
                <td class="px-6 py-4">${dosri.relationship || ''}</td>
                <td class="px-6 py-4 flex space-x-2">
                    <button data-id="${dosri.id}" class="edit-btn font-medium text-blue-600 dark:text-blue-500 hover:underline">Edit</button>
                    <button data-id="${dosri.id}" class="delete-btn font-medium text-red-600 dark:text-red-500 hover:underline">Delete</button>
                </td>
            `;
            dosriTableBody.appendChild(row);
        });

        // Attach event listeners to newly created buttons
        document.querySelectorAll('#dosriListModal .edit-btn').forEach(button => {
            button.addEventListener('click', (event) => window.openEditModal(parseInt(event.target.dataset.id)));
        });

        document.querySelectorAll('#dosriListModal .delete-btn').forEach(button => {
            button.addEventListener('click', async (event) => {
                const confirmed = await window.customConfirm('Are you sure you want to delete this DOSRI record?');
                if (confirmed) {
                    window.deleteDosri(parseInt(event.target.dataset.id));
                }
            });
        });
    };

    /**
     * Opens or populates the Add/Edit DOSRI modal.
     * @param {number} [id] - The ID of the DOSRI record to edit. If null, opens for adding new.
     */
    window.openEditModal = async function(id) {
        dosriForm.reset();
        dosriIdInput.value = '';
        // Ensure required attributes are reset or set correctly
        nameInput.setAttribute('required', 'required');
        branchInput.setAttribute('required', 'required');
        typeInput.setAttribute('required', 'required');

        if (id) {
            modalTitle.textContent = 'Edit DOSRI Record';
            try {
                const response = await fetch(`${API_BASE_URL}/api/dosri/${id}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                const dosri = data.dosri_record;

                if (dosri) {
                    dosriIdInput.value = dosri.id;
                    cidInput.value = dosri.cid || '';
                    branchInput.value = dosri.branch || '';
                    nameInput.value = dosri.name || '';
                    typeInput.value = dosri.type || '';
                    positionInput.value = dosri.position || '';
                    relatedToInput.value = dosri.related_to || '';
                    relationshipInput.value = dosri.relationship || '';
                } else {
                    window.showMessageBox('DOSRI record not found.', 'error');
                    return;
                }
            } catch (error) {
                console.error('Error fetching DOSRI record for edit:', error);
                window.showMessageBox('Failed to load record for editing.', 'error');
                return;
            }
        } else {
            modalTitle.textContent = 'Add New DOSRI';
        }
        window.openModal(dosriModal);
    };

    // Event listener for DOSRI form submission (Add/Edit)
    dosriForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        const formData = {
            cid: cidInput.value ? cidInput.value : '',
            branch: branchInput.value,
            name: nameInput.value,
            type: typeInput.value,
            position: positionInput.value,
            related_to: relatedToInput.value,
            relationship: relationshipInput.value
        };

        const id = dosriIdInput.value;
        let url = `${API_BASE_URL}/api/dosri`;
        let method = 'POST';

        if (id) {
            url = `${API_BASE_URL}/api/dosri/${id}`;
            method = 'PUT';
        }

        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok) {
                window.showMessageBox(result.message, 'success');
                window.closeModal(dosriModal);
                // Refresh the list after successful operation
                window.fetchDosriData(dosriSearchInput.value, dosriTypeFilter.value);
                // No need to call initializeSummaryReport here, as the main button will trigger it
            } else {
                window.showMessageBox(result.error || 'Operation failed', 'error');
            }
        } catch (error) {
            console.error('Error submitting DOSRI form:', error);
            window.showMessageBox('An error occurred during submission.', 'error');
        }
    });

    /**
     * Deletes a DOSRI record from the backend.
     * @param {number} id - The ID of the DOSRI record to delete.
     */
    window.deleteDosri = async function(id) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/dosri/${id}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (response.ok) {
                window.showMessageBox(result.message, 'success');
                // Refresh the list after successful deletion
                window.fetchDosriData(dosriSearchInput.value, dosriTypeFilter.value);
                // No need to call initializeSummaryReport here, as the main button will trigger it
            } else {
                window.showMessageBox(result.error || 'Deletion failed', 'error');
            }
        } catch (error) {
            console.error('Error deleting DOSRI record:', error);
            window.showMessageBox('An error occurred during deletion.', 'error');
        }
    };

    // Event listener for DOSRI CSV upload form submission
    uploadCsvForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        const file = dosriCsvFileInput.files[0];
        if (!file) {
            window.showMessageBox('Please select a CSV file to upload.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('csv_file', file);
        formData.append('upload_option', overrideAllRadio.checked ? 'override' : 'append');

        try {
            window.showMessageBox('Uploading CSV, please wait...', 'info');
            const response = await fetch(`${API_BASE_URL}/api/dosri/upload_csv`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                window.showMessageBox(result.message, 'success');
                window.closeModal(uploadCsvModal);
                // Refresh the list after successful upload
                window.fetchDosriData(dosriSearchInput.value, dosriTypeFilter.value);
                // No need to call initializeSummaryReport here, as the main button will trigger it
            } else {
                window.showMessageBox(result.error || 'CSV upload failed', 'error');
            }
        } catch (error) {
            console.error('Error uploading CSV:', error);
            window.showMessageBox('An error occurred during CSV upload.', 'error');
        }
    });


    /**
     * Fetches and displays DOSRI Loan Balances summary and details.
     * @param {Array<Object>} dosriList - The list of DOSRI members to process.
     * @param {string} reportDate - The date to filter the loan data (YYYY-MM-DD format).
     */
    window.loadLoanBalances = async function(dosriList, reportDate) {
        // Show loading state
        loanBalancesStatus.classList.remove('hidden');
        loanBalancesError.classList.add('hidden');
        loanBalancesNoData.classList.add('hidden');
        loanBalancesSummaryTiles.classList.remove('hidden'); // Ensure tiles are visible even if no data initially

        // Clear previous data
        loanBalanceTableBody.innerHTML = '<tr><td colspan="10" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">Loading loan balance details...</td></tr>';
        loanCurrentBalanceAmount.innerText = '₱0.00';
        loanTotalPastDueAmount.innerText = '₱0.00';
        pastDue1_30DaysAmount.innerText = '₱0.00';
        pastDue31_60DaysAmount.innerText = '₱0.00';
        pastDue61_90DaysAmount.innerText = '₱0.00';
        pastDue91_120DaysAmount.innerText = '₱0.00';
        pastDue121_180DaysAmount.innerText = '₱0.00';
        pastDue181_365DaysAmount.innerText = '₱0.00';
        pastDueOver365DaysAmount.innerText = '₱0.00';

        // Reset DOSRI type breakdown amounts for loans
        loanCurrentDAmount.innerText = '₱0.00';
        loanCurrentOAmount.innerText = '₱0.00';
        loanCurrentSAmount.innerText = '₱0.00';
        loanCurrentRIAmount.innerText = '₱0.00';
        loanPastDueDAmount.innerText = '₱0.00';
        loanPastDueOAmount.innerText = '₱0.00';
        loanPastDueSAmount.innerText = '₱0.00';
        loanPastDueRIAmount.innerText = '₱0.00';
        pastDue1_30_DAmount.innerText = '₱0.00';
        pastDue1_30_OAmount.innerText = '₱0.00';
        pastDue1_30_SAmount.innerText = '₱0.00';
        pastDue1_30_RIAmount.innerText = '₱0.00';
        pastDue31_60_DAmount.innerText = '₱0.00';
        pastDue31_60_OAmount.innerText = '₱0.00';
        pastDue31_60_SAmount.innerText = '₱0.00';
        pastDue31_60_RIAmount.innerText = '₱0.00';
        pastDue61_90_DAmount.innerText = '₱0.00';
        pastDue61_90_OAmount.innerText = '₱0.00';
        pastDue61_90_SAmount.innerText = '₱0.00';
        pastDue61_90_RIAmount.innerText = '₱0.00';
        pastDue91_120_DAmount.innerText = '₱0.00';
        pastDue91_120_OAmount.innerText = '₱0.00';
        pastDue91_120_SAmount.innerText = '₱0.00';
        pastDue91_120_RIAmount.innerText = '₱0.00';
        pastDue121_180_DAmount.innerText = '₱0.00';
        pastDue121_180_OAmount.innerText = '₱0.00';
        pastDue121_180_SAmount.innerText = '₱00.00';
        pastDue121_180_RIAmount.innerText = '₱0.00';
        pastDue181_365_DAmount.innerText = '₱0.00';
        pastDue181_365_OAmount.innerText = '₱0.00';
        pastDue181_365_SAmount.innerText = '₱0.00';
        pastDue181_365_RIAmount.innerText = '₱0.00';
        pastDueOver365_DAmount.innerText = '₱0.00';
        pastDueOver365_OAmount.innerText = '₱0.00';
        pastDueOver365_SAmount.innerText = '₱0.00';
        pastDueOver365_RIAmount.innerText = '₱0.00';


        try {
            if (!dosriList || dosriList.length === 0) {
                loanBalancesStatus.classList.add('hidden');
                loanBalancesNoData.classList.remove('hidden');
                loanBalanceTableBody.innerHTML = '<tr><td colspan="10" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">No DOSRI members selected or found to process loan data.</td></tr>';
                currentDosriLoanBalanceDetails = [];
                return;
            }

            const response = await fetch(`${API_BASE_URL}/api/dosri/loan_balances`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ dosri_members: dosriList, report_date: reportDate }), // Pass reportDate
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.error || 'Unknown error'}`);
            }

            const data = await response.json();
            console.log("DOSRI Loan Balances API Response:", data);

            const currentBalance = data.current_balance || 0;
            const totalPastDueBalance = data.past_due_balance || 0;
            const pastDueBreakdown = data.past_due_breakdown || {};
            const loanBalanceDetails = data.loan_balance_details || [];

            currentDosriLoanBalanceDetails = loanBalanceDetails; // Store for searching/copying

            // Initialize breakdown sums for loans
            const loanCurrentBreakdown = initializeBreakdownSums();
            const loanPastDueBreakdown = initializeBreakdownSums();
            const pastDue1_30Breakdown = initializeBreakdownSums();
            const pastDue31_60Breakdown = initializeBreakdownSums();
            const pastDue61_90Breakdown = initializeBreakdownSums();
            const pastDue91_120Breakdown = initializeBreakdownSums();
            const pastDue121_180Breakdown = initializeBreakdownSums();
            const pastDue181_365Breakdown = initializeBreakdownSums();
            const pastDueOver365Breakdown = initializeBreakdownSums();


            // Calculate breakdown for loans
            loanBalanceDetails.forEach(loan => {
                const type = (loan.TYPE || '').toLowerCase();
                const balance = loan['PRINCIPAL BALANCE'] || 0;
                const aging = (loan.AGING || '').toUpperCase();

                if (type.includes('director')) {
                    if (aging === 'NOT YET DUE') loanCurrentBreakdown.director += balance;
                    else loanPastDueBreakdown.director += balance;
                } else if (type.includes('officer')) {
                    if (aging === 'NOT YET DUE') loanCurrentBreakdown.officer += balance;
                    else loanPastDueBreakdown.officer += balance;
                } else if (type.includes('staff')) {
                    if (aging === 'NOT YET DUE') loanCurrentBreakdown.staff += balance;
                    else loanPastDueBreakdown.staff += balance;
                } else if (type.includes('related interest')) {
                    if (aging === 'NOT YET DUE') loanCurrentBreakdown['related interest'] += balance;
                    else loanPastDueBreakdown['related interest'] += balance;
                }

                // Breakdown for specific aging buckets
                if (aging === '1-30 DAYS') {
                    if (type.includes('director')) pastDue1_30Breakdown.director += balance;
                    else if (type.includes('officer')) pastDue1_30Breakdown.officer += balance;
                    else if (type.includes('staff')) pastDue1_30Breakdown.staff += balance;
                    else if (type.includes('related interest')) pastDue1_30Breakdown['related interest'] += balance;
                } else if (aging === '31-60 DAYS' || aging === '31-60') {
                    if (type.includes('director')) pastDue31_60Breakdown.director += balance;
                    else if (type.includes('officer')) pastDue31_60Breakdown.officer += balance;
                    else if (type.includes('staff')) pastDue31_60Breakdown.staff += balance;
                    else if (type.includes('related interest')) pastDue31_60Breakdown['related interest'] += balance;
                } else if (aging === '61-90 DAYS' || aging === '61-90') {
                    if (type.includes('director')) pastDue61_90Breakdown.director += balance;
                    else if (type.includes('officer')) pastDue61_90Breakdown.officer += balance;
                    else if (type.includes('staff')) pastDue61_90Breakdown.staff += balance;
                    else if (type.includes('related interest')) pastDue61_90Breakdown['related interest'] += balance;
                } else if (aging === '91-120 DAYS' || aging === '91-120') {
                    if (type.includes('director')) pastDue91_120Breakdown.director += balance;
                    else if (type.includes('officer')) pastDue91_120Breakdown.officer += balance;
                    else if (type.includes('staff')) pastDue91_120Breakdown.staff += balance;
                    else if (type.includes('related interest')) pastDue91_120Breakdown['related interest'] += balance;
                } else if (aging === '121-180 DAYS' || aging === '121-180') {
                    if (type.includes('director')) pastDue121_180Breakdown.director += balance;
                    else if (type.includes('officer')) pastDue121_180Breakdown.officer += balance;
                    else if (type.includes('staff')) pastDue121_180Breakdown.staff += balance;
                    else if (type.includes('related interest')) pastDue121_180Breakdown['related interest'] += balance;
                } else if (aging === '181-365 DAYS' || aging === '181-365') {
                    if (type.includes('director')) pastDue181_365Breakdown.director += balance;
                    else if (type.includes('officer')) pastDue181_365Breakdown.officer += balance;
                    else if (type.includes('staff')) pastDue181_365Breakdown.staff += balance;
                    else if (type.includes('related interest')) pastDue181_365Breakdown['related interest'] += balance;
                } else if (aging === 'OVER 365 DAYS' || aging === 'OVER 365') {
                    if (type.includes('director')) pastDueOver365Breakdown.director += balance;
                    else if (type.includes('officer')) pastDueOver365Breakdown.officer += balance;
                    else if (type.includes('staff')) pastDueOver365Breakdown.staff += balance;
                    else if (type.includes('related interest')) pastDueOver365Breakdown['related interest'] += balance;
                }
            });


            if (currentBalance === 0 && totalPastDueBalance === 0 && loanBalanceDetails.length === 0) {
                loanBalancesStatus.classList.add('hidden');
                loanBalancesNoData.classList.remove('hidden');
                loanBalanceTableBody.innerHTML = '<tr><td colspan="10" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">No loan balance details found for DOSRI members.</td></tr>';
            } else {
                loanCurrentBalanceAmount.innerText = window.formatCurrency(currentBalance);
                loanTotalPastDueAmount.innerText = window.formatCurrency(totalPastDueBalance);

                // Populate past due breakdown tiles
                pastDue1_30DaysAmount.innerText = window.formatCurrency(pastDueBreakdown['1-30 DAYS'] || 0);
                pastDue31_60DaysAmount.innerText = window.formatCurrency(pastDueBreakdown['31-60 DAYS'] || 0);
                pastDue61_90DaysAmount.innerText = window.formatCurrency(pastDueBreakdown['61-90 DAYS'] || 0);
                pastDue91_120DaysAmount.innerText = window.formatCurrency(pastDueBreakdown['91-120 DAYS'] || 0);
                pastDue121_180DaysAmount.innerText = window.formatCurrency(pastDueBreakdown['121-180 DAYS'] || 0);
                pastDue181_365DaysAmount.innerText = window.formatCurrency(pastDueBreakdown['181-365 DAYS'] || 0);
                pastDueOver365DaysAmount.innerText = window.formatCurrency(pastDueBreakdown['OVER 365 DAYS'] || 0);

                // Update DOSRI type breakdown displays for loans
                updateBreakdownDisplay('loan_current', loanCurrentBreakdown);
                updateBreakdownDisplay('loan_past_due', loanPastDueBreakdown);
                updateBreakdownDisplay('past_due_1_30', pastDue1_30Breakdown);
                updateBreakdownDisplay('past_due_31_60', pastDue31_60Breakdown);
                updateBreakdownDisplay('past_due_61_90', pastDue61_90Breakdown);
                updateBreakdownDisplay('past_due_91_120', pastDue91_120Breakdown);
                updateBreakdownDisplay('past_due_121_180', pastDue121_180Breakdown);
                updateBreakdownDisplay('past_due_181_365', pastDue181_365Breakdown);
                updateBreakdownDisplay('past_due_over_365', pastDueOver365Breakdown);


                loanBalancesStatus.classList.add('hidden');
                window.renderLoanBalanceTable(currentDosriLoanBalanceDetails);
            }
        } catch (error) {
            console.error('Error loading DOSRI loan balances:', error);
            loanBalancesStatus.classList.add('hidden');
            loanBalancesError.classList.remove('hidden');
            loanBalanceTableBody.innerHTML = '<tr><td colspan="10" class="px-6 py-4 whitespace-nowrap text-center text-red-500">Error loading DOSRI loan balance details. ' + (error.message || '') + '</td></tr>';
            currentDosriLoanBalanceDetails = [];
            window.showMessageBox('Failed to load DOSRI loan reports. Check console for details.', 'error');
        }
    };

    /**
     * Renders or filters the DOSRI loan balance detail table.
     * @param {Array<Object>} details - The array of loan detail objects.
     * @param {string} [searchTerm=''] - The search term to filter the table.
     */
    window.renderLoanBalanceTable = function(details, searchTerm = '') {
        loanBalanceTableBody.innerHTML = '';
        let filteredDetails = details;

        if (searchTerm) {
            const lowerCaseSearchTerm = searchTerm.toLowerCase();
            filteredDetails = details.filter(row =>
                Object.values(row).some(value =>
                    String(value).toLowerCase().includes(lowerCaseSearchTerm)
                )
            );
        }

        if (filteredDetails.length > 0) {
            filteredDetails.forEach(row => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-gray-50';
                tr.innerHTML = `
                    <td class="px-6 py-4 whitespace-nowrap">${row['BRANCH'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['CID'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['NAME OF MEMBER'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['TYPE'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['LOAN ACCT.'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">${window.formatCurrency(row['PRINCIPAL BALANCE'])}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['PRODUCT'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['DISBDATE'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['DUE DATE'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['AGING'] || ''}</td>
                `;
                loanBalanceTableBody.appendChild(tr);
            });
        } else {
            loanBalanceTableBody.innerHTML = '<tr><td colspan="10" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">No matching loan balance details found.</td></tr>';
        }
    };


    /**
     * Fetches and displays DOSRI Deposit Liabilities summary and details.
     * @param {Array<Object>} dosriList - The list of DOSRI members to process.
     * @param {string} reportDate - The date to filter the deposit data (YYYY-MM-DD format).
     */
    window.loadDepositLiabilities = async function(dosriList, reportDate) {
        // Show loading state
        depositStatus.classList.remove('hidden');
        depositError.classList.add('hidden');
        depositNoData.classList.add('hidden');
        depositTilesContainer.classList.remove('hidden'); // Ensure tiles are visible even if no data initially

        // Clear previous data
        depositLiabilitiesTableBody.innerHTML = '<tr><td colspan="8" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">Loading deposit liabilities details...</td></tr>';
        regularSavingsAmount.innerText = '₱0.00';
        atmSavingsAmount.innerText = '₱0.00';
        shareCapitalAmount.innerText = '₱0.00';
        timeDepositsAmount.innerText = '₱0.00';
        youthSavingsAmount.innerText = '₱0.00';
        specialDepositsAmount.innerText = '₱0.00';
        
        // Ensure count elements exist before attempting to update them
        if (regularSavingsCount) regularSavingsCount.innerText = 'Accounts: 0';
        if (atmSavingsCount) atmSavingsCount.innerText = 'Accounts: 0';
        if (shareCapitalCount) shareCapitalCount.innerText = 'Accounts: 0';
        if (timeDepositsCount) timeDepositsCount.innerText = 'Accounts: 0';
        if (youthSavingsCount) youthSavingsCount.innerText = 'Accounts: 0';
        if (specialDepositsCount) specialDepositsCount.innerText = 'Accounts: 0';

        // Reset DOSRI type breakdown amounts for deposits
        regularSavingsDAmount.innerText = '₱0.00';
        regularSavingsOAmount.innerText = '₱0.00';
        regularSavingsSAmount.innerText = '₱0.00';
        regularSavingsRIAmount.innerText = '₱0.00';

        atmSavingsDAmount.innerText = '₱0.00';
        atmSavingsOAmount.innerText = '₱0.00';
        atmSavingsSAmount.innerText = '₱0.00';
        atmSavingsRIAmount.innerText = '₱0.00';

        shareCapitalDAmount.innerText = '₱0.00';
        shareCapitalOAmount.innerText = '₱0.00';
        shareCapitalSAmount.innerText = '₱0.00';
        shareCapitalRIAmount.innerText = '₱0.00';

        timeDepositsDAmount.innerText = '₱0.00';
        timeDepositsOAmount.innerText = '₱0.00';
        timeDepositsSAmount.innerText = '₱0.00';
        timeDepositsRIAmount.innerText = '₱0.00';

        youthSavingsDAmount.innerText = '₱0.00';
        youthSavingsOAmount.innerText = '₱0.00';
        youthSavingsSAmount.innerText = '₱0.00';
        youthSavingsRIAmount.innerText = '₱0.00';

        specialDepositsDAmount.innerText = '₱0.00';
        specialDepositsOAmount.innerText = '₱0.00';
        specialDepositsSAmount.innerText = '₱0.00';
        specialDepositsRIAmount.innerText = '₱0.00';


        try {
            if (!dosriList || dosriList.length === 0) {
                depositStatus.classList.add('hidden');
                depositNoData.classList.remove('hidden');
                depositLiabilitiesTableBody.innerHTML = '<tr><td colspan="8" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">No DOSRI members selected or found to process deposit data.</td></tr>';
                currentDosriDepositLiabilitiesDetails = [];
                // Reset counts as well
                if (regularSavingsCount) regularSavingsCount.innerText = 'Accounts: 0';
                if (atmSavingsCount) atmSavingsCount.innerText = 'Accounts: 0';
                if (shareCapitalCount) shareCapitalCount.innerText = 'Accounts: 0';
                if (timeDepositsCount) timeDepositsCount.innerText = 'Accounts: 0';
                if (youthSavingsCount) youthSavingsCount.innerText = 'Accounts: 0';
                if (specialDepositsCount) specialDepositsCount.innerText = 'Accounts: 0';
                return;
            }

            const response = await fetch(`${API_BASE_URL}/api/dosri/deposit_liabilities`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ dosri_members: dosriList, report_date: reportDate }), // Pass reportDate
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.error || 'Unknown error'}`);
            }

            const data = await response.json();
            console.log("DOSRI Deposit Liabilities API Response:", data);

            // Populate amount tiles
            regularSavingsAmount.innerText = window.formatCurrency(data.regular_savings || 0);
            atmSavingsAmount.innerText = window.formatCurrency(data.atm_savings || 0);
            shareCapitalAmount.innerText = window.formatCurrency(data.share_capital || 0);
            timeDepositsAmount.innerText = window.formatCurrency(data.time_deposits || 0);
            youthSavingsAmount.innerText = window.formatCurrency(data.youth_savings || 0);
            specialDepositsAmount.innerText = window.formatCurrency(data.special_deposits || 0);

            depositStatus.classList.add('hidden');

            const totalDeposits = (data.regular_savings || 0) + (data.share_capital || 0) +
                                   (data.time_deposits || 0) + (data.youth_savings || 0) +
                                   (data.atm_savings || 0) +
                                   (data.special_deposits || 0);

            // Show 'No Data' message if all sums and details are empty
            if (totalDeposits === 0 && Object.keys(data.deposit_accounts_count || {}).length === 0 && (data.deposit_liabilities_details || []).length === 0) {
                depositNoData.classList.remove('hidden');
                depositLiabilitiesTableBody.innerHTML = '<tr><td colspan="8" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">No deposit liabilities details found for DOSRI members.</td></tr>';
            }

            // Populate account counts, ensuring elements exist
            const counts = data.deposit_accounts_count || {};
            if (regularSavingsCount) regularSavingsCount.innerText = `Accounts: ${counts['REGULAR SAVINGS'] || 0}`;
            if (atmSavingsCount) atmSavingsCount.innerText = `Accounts: ${counts['ATM SAVINGS'] || 0}`;
            if (shareCapitalCount) shareCapitalCount.innerText = `Accounts: ${counts['SHARE CAPITAL'] || 0}`;
            
            // Calculate total time deposit accounts from breakdown
            let totalTimeDepositAccounts = 0;
            const timeDepositKeys = [
                'TIME DEPOSIT - MATURITY', 'TIME DEPOSIT - MONTHLY', 'TIME DEPOSIT -A',
                'TIME DEPOSIT -B', 'TIME DEPOSIT -C'
            ];
            timeDepositKeys.forEach(key => {
                totalTimeDepositAccounts += (counts[key] || 0);
            });
            if (timeDepositsCount) timeDepositsCount.innerText = `Accounts: ${totalTimeDepositAccounts}`;

            // Calculate special deposits count from breakdown
            const categorizedAccountTypesForCount = [
                'REGULAR SAVINGS',
                'SHARE CAPITAL',
                'YOUTH SAVINGS CLUB',
                'ATM SAVINGS'
            ].concat(timeDepositKeys);

            let totalSpecialDepositAccounts = 0;
            for (const accName in counts) {
                if (!categorizedAccountTypesForCount.includes(accName)) {
                    totalSpecialDepositAccounts += counts[accName];
                }
            }
            if (specialDepositsCount) specialDepositsCount.innerText = `Accounts: ${totalSpecialDepositAccounts}`;


            currentDosriDepositLiabilitiesDetails = data.deposit_liabilities_details || []; // Store for searching/copying

            // Initialize breakdown sums for deposits
            const regularSavingsBreakdown = initializeBreakdownSums();
            const atmSavingsBreakdown = initializeBreakdownSums();
            const shareCapitalBreakdown = initializeBreakdownSums();
            const timeDepositsBreakdown = initializeBreakdownSums();
            const youthSavingsBreakdown = initializeBreakdownSums();
            const specialDepositsBreakdown = initializeBreakdownSums();

            // Calculate breakdown for deposits
            currentDosriDepositLiabilitiesDetails.forEach(deposit => {
                const type = (deposit.TYPE || '').toLowerCase();
                const balance = deposit['BALANCE BAL'] || 0;
                const product = (deposit['PRODUCT ACCNAME'] || '').toUpperCase();

                if (balance === 0) return; // Only consider non-zero balances for breakdown

                let targetBreakdown = null;
                if (product === 'REGULAR SAVINGS') {
                    targetBreakdown = regularSavingsBreakdown;
                } else if (product === 'ATM SAVINGS') {
                    targetBreakdown = atmSavingsBreakdown;
                } else if (product === 'SHARE CAPITAL') {
                    targetBreakdown = shareCapitalBreakdown;
                } else if (timeDepositKeys.includes(product)) {
                    targetBreakdown = timeDepositsBreakdown;
                } else if (product === 'YOUTH SAVINGS CLUB') {
                    targetBreakdown = youthSavingsBreakdown;
                } else if (!categorizedAccountTypesForCount.includes(product)) { // Special Deposits
                    targetBreakdown = specialDepositsBreakdown;
                }

                if (targetBreakdown) {
                    if (type.includes('director')) targetBreakdown.director += balance;
                    else if (type.includes('officer')) targetBreakdown.officer += balance;
                    else if (type.includes('staff')) targetBreakdown.staff += balance;
                    else if (type.includes('related interest')) targetBreakdown['related interest'] += balance;
                }
            });

            // Update DOSRI type breakdown displays for deposits
            updateBreakdownDisplay('regular_savings', regularSavingsBreakdown);
            updateBreakdownDisplay('atm_savings', atmSavingsBreakdown);
            updateBreakdownDisplay('share_capital', shareCapitalBreakdown);
            updateBreakdownDisplay('time_deposits', timeDepositsBreakdown);
            updateBreakdownDisplay('youth_savings', youthSavingsBreakdown);
            updateBreakdownDisplay('special_deposits', specialDepositsBreakdown);

            window.renderDepositLiabilitiesTable(currentDosriDepositLiabilitiesDetails);
        } catch (error) {
            console.error('Error loading DOSRI deposit liabilities:', error);
            depositStatus.classList.add('hidden');
            depositError.classList.remove('hidden');
            // Reset counts to N/A or 0 on error
            if (regularSavingsCount) regularSavingsCount.innerText = 'Accounts: N/A';
            if (atmSavingsCount) atmSavingsCount.innerText = 'Accounts: N/A';
            if (shareCapitalCount) shareCapitalCount.innerText = 'Accounts: N/A';
            if (timeDepositsCount) timeDepositsCount.innerText = 'Accounts: N/A';
            if (youthSavingsCount) youthSavingsCount.innerText = 'Accounts: N/A';
            if (specialDepositsCount) specialDepositsCount.innerText = 'Accounts: N/A';

            // Reset DOSRI type breakdown amounts on error
            regularSavingsDAmount.innerText = '₱0.00';
            regularSavingsOAmount.innerText = '₱0.00';
            regularSavingsSAmount.innerText = '₱0.00';
            regularSavingsRIAmount.innerText = '₱0.00';

            atmSavingsDAmount.innerText = '₱0.00';
            atmSavingsOAmount.innerText = '₱0.00';
            atmSavingsSAmount.innerText = '₱0.00';
            atmSavingsRIAmount.innerText = '₱0.00';

            shareCapitalDAmount.innerText = '₱0.00';
            shareCapitalOAmount.innerText = '₱0.00';
            shareCapitalSAmount.innerText = '₱0.00';
            shareCapitalRIAmount.innerText = '₱0.00';

            timeDepositsDAmount.innerText = '₱0.00';
            timeDepositsOAmount.innerText = '₱0.00';
            timeDepositsSAmount.innerText = '₱0.00';
            timeDepositsRIAmount.innerText = '₱0.00';

            youthSavingsDAmount.innerText = '₱0.00';
            youthSavingsOAmount.innerText = '₱0.00';
            youthSavingsSAmount.innerText = '₱0.00';
            youthSavingsRIAmount.innerText = '₱0.00';

            specialDepositsDAmount.innerText = '₱0.00';
            specialDepositsOAmount.innerText = '₱0.00';
            specialDepositsSAmount.innerText = '₱0.00';
            specialDepositsRIAmount.innerText = '₱0.00';

            depositLiabilitiesTableBody.innerHTML = '<tr><td colspan="8" class="px-6 py-4 whitespace-nowrap text-center text-red-500">Error loading deposit liabilities details. ' + (error.message || '') + '</td></tr>';
            currentDosriDepositLiabilitiesDetails = [];
            window.showMessageBox('Failed to load DOSRI deposit reports. Check console for details.', 'error');
        }
    };

    /**
     * Renders or filters the DOSRI deposit liabilities detail table.
     * Filters out rows where 'BALANCE BAL' is 0 before rendering.
     * @param {Array<Object>} details - The array of deposit detail objects.
     * @param {string} [searchTerm=''] - The search term to filter the table.
     */
    window.renderDepositLiabilitiesTable = function(details, searchTerm = '') {
        depositLiabilitiesTableBody.innerHTML = '';
        
        // Filter out zero-balance entries first
        let filteredDetails = details.filter(row => row['BALANCE BAL'] !== 0);

        if (searchTerm) {
            const lowerCaseSearchTerm = searchTerm.toLowerCase();
            filteredDetails = filteredDetails.filter(row =>
                Object.values(row).some(value =>
                    String(value).toLowerCase().includes(lowerCaseSearchTerm)
                )
            );
        }

        if (filteredDetails.length > 0) {
            filteredDetails.forEach(row => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-gray-50';
                tr.innerHTML = `
                    <td class="px-6 py-4 whitespace-nowrap">${row['BRANCH'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['ACCOUNT ACC'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['NAME'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['TYPE'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['CID'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['PRODUCT ACCNAME'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['OPENED DOPEN'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">${window.formatCurrency(row['BALANCE BAL'])}</td>
                `;
                depositLiabilitiesTableBody.appendChild(tr);
            });
        } else {
            depositLiabilitiesTableBody.innerHTML = '<tr><td colspan="8" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">No matching deposit liabilities details found.</td></tr>';
        }
    };

    /**
     * Downloads all current DOSRI and Former Employee report data as a single Excel file.
     * This combines data from currentDosriLoanBalanceDetails, currentDosriDepositLiabilitiesDetails,
     * window.currentFormEmpLoanBalanceDetails, window.currentFormEmpDepositLiabilitiesDetails,
     * and the raw DOSRI/Former Employee lists.
     */
    window.downloadAllAsExcel = async function() {
        // Fetch raw DOSRI list and Former Employee list for dedicated sheets
        // Pass empty strings to fetch all records without search/filter
        const dosriListRaw = await window.fetchDosriData('', '');
        const formEmpListRaw = window.fetchFormEmpData ? await window.fetchFormEmpData('', '') : []; // fetchFormEmpData is in operations_form_emp.js

        if (currentDosriLoanBalanceDetails.length === 0 && currentDosriDepositLiabilitiesDetails.length === 0 &&
            window.currentFormEmpLoanBalanceDetails.length === 0 && window.currentFormEmpDepositLiabilitiesDetails.length === 0 &&
            dosriListRaw.length === 0 && formEmpListRaw.length === 0) {
            window.showMessageBox('No data available to download.', 'warning');
            return;
        }

        try {
            window.showMessageBox('Preparing Excel file for download...', 'info');
            const response = await fetch(`${API_BASE_URL}/api/dosri/download_excel`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    loan_details: currentDosriLoanBalanceDetails,
                    deposit_details: currentDosriDepositLiabilitiesDetails,
                    form_emp_loan_details: window.currentFormEmpLoanBalanceDetails,
                    form_emp_deposit_details: window.currentFormEmpDepositLiabilitiesDetails,
                    dosri_list_raw: dosriListRaw, // Add raw DOSRI list
                    form_emp_list_raw: formEmpListRaw // Add raw Former Employee list
                }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'DOSRI_and_Former_Employee_Report.xlsx'; // More descriptive filename
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            window.showMessageBox('Excel file downloaded successfully!', 'success');

        } catch (error) {
            console.error('Error downloading Excel:', error);
            window.showMessageBox(`Failed to download Excel file: ${error.message}`, 'error');
        }
    };


    /**
     * Initializes and generates the summary reports for both DOSRI and Former Employees.
     * This function is triggered by the "Generate Reports" button.
     */
    window.initializeSummaryReport = async function() {
        window.showMessageBox('Generating DOSRI and Former Employee reports...', 'info');
        // Get selected types from the new multi-select filter for DOSRI
        const selectedDosriTypes = Array.from(dosriTypeMultiFilter.selectedOptions).map(option => option.value);
        // Get the selected report date
        const reportDate = reportDateInput.value; // Get value in YYYY-MM-DD format

        // Validate report date
        if (!reportDate) {
            window.showMessageBox('Please select a Report Date.', 'error');
            return;
        }

        // Load DOSRI reports
        const dosriList = await window.fetchDosriListForSummary(selectedDosriTypes);
        window.loadLoanBalances(dosriList, reportDate); // Pass reportDate
        window.loadDepositLiabilities(dosriList, reportDate); // Pass reportDate

        // Load Former Employee reports if the function exists (from operations_form_emp.js)
        if (window.fetchFormEmpListForSummary && window.loadFormEmpLoanBalances && window.loadFormEmpDepositLiabilities) {
            const formEmpList = await window.fetchFormEmpListForSummary();
            window.loadFormEmpLoanBalances(formEmpList, reportDate); // Pass reportDate
            window.loadFormEmpDepositLiabilities(formEmpList, reportDate); // Pass reportDate
            window.showMessageBox('DOSRI and Former Employee reports generated successfully!', 'success');
        } else {
            console.warn('operations_form_emp.js functions not yet loaded or not exposed globally. Former Employee reports might not be generated.');
            window.showMessageBox('Former Employee report generation functions are not fully available. DOSRI reports generated.', 'warning');
        }
    };


    // --- Event Listeners (DOSRI Specific) ---

    let dosriSearchTimeout;
    // Event listener for search input in the DOSRI List modal (debounced)
    dosriSearchInput.addEventListener('keyup', () => {
        clearTimeout(dosriSearchTimeout);
        dosriSearchTimeout = setTimeout(() => {
            window.fetchDosriData(dosriSearchInput.value, dosriTypeFilter.value);
        }, 300); // Debounce to avoid too many requests
    });

    // Event listener for type filter in the DOSRI List modal
    dosriTypeFilter.addEventListener('change', () => {
        window.fetchDosriData(dosriSearchInput.value, dosriTypeFilter.value);
    });

    // Event listener for opening the DOSRI List modal
    if (openDosriListBtn) {
        openDosriListBtn.addEventListener('click', () => {
            window.openModal(dosriListModal);
            window.fetchDosriData(); // Fetch data when modal opens
        });
    }

    // Event listener for closing the DOSRI List modal
    if (closeDosriListModalBtn) {
        closeDosriListModalBtn.addEventListener('click', () => window.closeModal(dosriListModal));
    }

    // Event listener for opening the Add DOSRI modal
    if (addDosriBtn) {
        addDosriBtn.addEventListener('click', () => window.openEditModal());
    }

    // Event listeners for cancelling/closing the Add/Edit DOSRI form modal
    const cancelDosriBtnForm = document.getElementById('cancelDosriBtnForm');
    if (cancelDosriBtn) {
        cancelDosriBtn.addEventListener('click', () => window.closeModal(dosriModal));
    }
    if (cancelDosriBtnForm) {
        cancelDosriBtnForm.addEventListener('click', () => window.closeModal(dosriModal));
    }

    // Event listener for opening the CSV Upload modal
    if (uploadCsvBtn) {
        uploadCsvBtn.addEventListener('click', () => {
            uploadCsvForm.reset(); // Clear previous selection
            window.openModal(uploadCsvModal);
        });
    }

    // Event listeners for cancelling/closing the CSV Upload modal
    const cancelUploadCsvBtnForm = document.getElementById('cancelUploadCsvBtnForm');
    if (cancelUploadCsvBtn) {
        cancelUploadCsvBtn.addEventListener('click', () => window.closeModal(uploadCsvModal));
    }
    if (cancelUploadCsvBtnForm) {
        cancelUploadCsvBtnForm.addEventListener('click', () => window.closeModal(uploadCsvModal));
    }

    // Event listener for searching in the DOSRI Loan Balance table
    loanBalanceSearchInput.addEventListener('keyup', (event) => {
        window.renderLoanBalanceTable(currentDosriLoanBalanceDetails, event.target.value);
    });

    // Event listener for copying DOSRI Loan Balance table to clipboard
    copyLoanBalanceTableBtn.addEventListener('click', () => {
        window.copyTableToClipboard('loan-balance-table-body');
    });

    // Event listener for searching in the DOSRI Deposit Liabilities table
    depositLiabilitiesSearchInput.addEventListener('keyup', (event) => {
        window.renderDepositLiabilitiesTable(currentDosriDepositLiabilitiesDetails, event.target.value);
    });

    // Event listener for copying DOSRI Deposit Liabilities table to clipboard
    copyDepositLiabilitiesTableBtn.addEventListener('click', () => {
        window.copyTableToClipboard('deposit-liabilities-table-body');
    });

    // Event listener for downloading all reports as Excel
    downloadDosriExcelBtn.addEventListener('click', window.downloadAllAsExcel);

    // NEW: Event listener for the "Generate Reports" button
    if (generateReportsBtn) {
        generateReportsBtn.addEventListener('click', () => {
            window.initializeSummaryReport();
        });
    }

    // Removed this line to stop auto-generation on page load.
    // window.initializeSummaryReport(); 
});
