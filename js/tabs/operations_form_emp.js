// This script handles all Former Employee related functionalities

document.addEventListener('DOMContentLoaded', function() {
    // Base URL for the Flask API backend.
    // IMPORTANT: This is now sourced from utils.js
    const API_BASE_URL = window.FLASK_API_BASE_URL;

    // --- Former Employees Elements ---
    const formerEmployeesListModal = document.getElementById('formerEmployeesListModal');
    const closeFormerEmployeesListModalBtn = document.getElementById('closeFormerEmployeesListModalBtn');
    const openFormerEmployeesListBtn = document.getElementById('openFormerEmployeesListBtn');
    const formEmpSearchInput = document.getElementById('formEmpSearchInput');
    const formEmpStatusFilter = document.getElementById('formEmpStatusFilter');
    const formerEmployeesListTableBody = document.getElementById('formerEmployeesListTableBody');
    const formEmpModal = document.getElementById('formEmpModal');
    const formEmpModalTitle = document.getElementById('formEmpModalTitle');
    const formEmpForm = document.getElementById('formEmpForm');
    const addFormEmpBtn = document.getElementById('addFormEmpBtn');
    const cancelFormEmpBtn = document.getElementById('cancelFormEmpBtn');
    const formEmpIdInput = document.getElementById('formEmpId');
    const formEmpBranchInput = document.getElementById('formEmpBranch');
    const formEmpNameInput = document.getElementById('formEmpName');
    const formEmpCidInput = document.getElementById('formEmpCid');
    const formEmpDateResignedInput = document.getElementById('formEmpDateResigned');
    const formEmpStatusInput = document.getElementById('formEmpStatus');
    const uploadFormEmpCsvBtn = document.getElementById('uploadFormEmpCsvBtn');
    const uploadFormEmpCsvModal = document.getElementById('uploadFormEmpCsvModal');
    const uploadFormEmpCsvForm = document.getElementById('uploadFormEmpCsvForm');
    const cancelUploadFormEmpCsvBtn = document.getElementById('cancelUploadFormEmpCsvBtn');
    const formEmpCsvFileInput = document.getElementById('formEmpCsvFile');
    const formEmpOverrideAllRadio = document.getElementById('formEmpOverrideAll');
    const formEmpAppendRadio = document.getElementById('formEmpAppend');

    // --- Former Employees Summary Report Elements ---
    const formEmpLoanSummaryTiles = document.getElementById('form_emp_loan_summary_tiles');
    const formEmpLoanCurrentBalanceAmount = document.getElementById('form_emp_loan_current_balance_amount');
    const formEmpLoanTotalPastDueAmount = document.getElementById('form_emp_loan_total_past_due_amount');
    const formEmpLoanPastDueBreakdownTiles = document.getElementById('form_emp_loan_past_due_breakdown_tiles');
    const formEmpPastDue1_30DaysAmount = document.getElementById('form_emp_past_due_1_30_days_amount');
    const formEmpPastDue31_60DaysAmount = document.getElementById('form_emp_past_due_31_60_days_amount');
    const formEmpPastDue61_90DaysAmount = document.getElementById('form_emp_past_due_61_90_days_amount');
    const formEmpPastDue91_120DaysAmount = document.getElementById('form_emp_past_due_91_120_days_amount');
    const formEmpPastDue121_180DaysAmount = document.getElementById('form_emp_past_due_121_180_days_amount');
    const formEmpPastDue181_365DaysAmount = document.getElementById('form_emp_past_due_181_365_days_amount');
    const formEmpPastDueOver365DaysAmount = document.getElementById('form_emp_past_due_over_365_days_amount');
    const formEmpLoanStatus = document.getElementById('form_emp_loan_status');
    const formEmpLoanError = document.getElementById('form_emp_loan_error');
    const formEmpLoanNoData = document.getElementById('form_emp_loan_no_data');

    const formEmpDepositLiabilitiesTiles = document.getElementById('form_emp_deposit_liabilities_tiles');
    const formEmpRegularSavingsAmount = document.getElementById('form_emp_regular_savings_amount');
    const formEmpAtmSavingsAmount = document.getElementById('form_emp_atm_savings_amount');
    const formEmpShareCapitalAmount = document.getElementById('form_emp_share_capital_amount');
    const formEmpTimeDepositsAmount = document.getElementById('form_emp_time_deposits_amount');
    const formEmpYouthSavingsAmount = document.getElementById('form_emp_youth_savings_amount');
    const formEmpSpecialDepositsAmount = document.getElementById('form_emp_special_deposits_amount');
    const formEmpRegularSavingsCount = document.getElementById('form_emp_regular_savings_count');
    const formEmpAtmSavingsCount = document.getElementById('form_emp_atm_savings_count');
    const formEmpShareCapitalCount = document.getElementById('form_emp_share_capital_count');
    const formEmpTimeDepositsCount = document.getElementById('form_emp_time_deposits_count');
    const formEmpYouthSavingsCount = document.getElementById('form_emp_youth_savings_count');
    const formEmpSpecialDepositsCount = document.getElementById('form_emp_special_deposits_count');
    const formEmpDepositStatus = document.getElementById('form_emp_deposit_status');
    const formEmpDepositError = document.getElementById('form_emp_deposit_error');
    const formEmpDepositNoData = document.getElementById('form_emp_deposit_no_data');

    // Elements for Former Employees Details Tables
    const formEmpLoanTableBody = document.getElementById('form-emp-loan-table-body');
    const formEmpLoanBalanceSearchInput = document.getElementById('formEmpLoanBalanceSearchInput');
    const copyFormEmpLoanBalanceTableBtn = document.getElementById('copyFormEmpLoanBalanceTableBtn');

    const formEmpDepositLiabilitiesTableBody = document.getElementById('form-emp-deposit-liabilities-table-body');
    const formEmpDepositLiabilitiesSearchInput = document.getElementById('formEmpDepositLiabilitiesSearchInput');
    const copyFormEmpDepositLiabilitiesTableBtn = document.getElementById('copyFormEmpDepositLiabilitiesTableBtn');

    // Store fetched detail data for searching/copying (Former Employee specific)
    let currentFormEmpLoanBalanceDetails = [];
    let currentFormEmpDepositLiabilitiesDetails = [];

    // --- Former Employees Data Handling Functions ---

    async function fetchFormEmpData(searchTerm = '', statusFilter = '') {
        formerEmployeesListTableBody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center">Loading former employee data...</td></tr>';

        const params = new URLSearchParams();
        if (searchTerm) {
            params.append('search_term', searchTerm);
        }
        if (statusFilter) {
            params.append('status_filter', statusFilter);
        }

        const url = `${API_BASE_URL}/api/form_emp?${params.toString()}`;

        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            renderFormEmpTable(data.form_emp_list);
        } catch (error) {
            console.error('Error fetching Former Employee data:', error);
            formerEmployeesListTableBody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center text-red-500">Failed to load data. Please try again.</td></tr>';
            window.showMessageBox('Failed to load Former Employee data. Check server logs.', 'error');
        }
    }

    function renderFormEmpTable(formEmpList) {
        formerEmployeesListTableBody.innerHTML = '';
        if (formEmpList.length === 0) {
            formerEmployeesListTableBody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center">No former employee records found.</td></tr>';
            return;
        }

        formEmpList.forEach(formEmp => {
            const row = document.createElement('tr');
            row.classList.add('bg-white', 'border-b', 'dark:bg-gray-800', 'dark:border-gray-700', 'hover:bg-gray-50', 'dark:hover:bg-gray-600');
            row.innerHTML = `
                <td class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">${formEmp.id || ''}</td>
                <td class="px-6 py-4">${formEmp.BRANCH || ''}</td>
                <td class="px-6 py-4">${formEmp.NAME || ''}</td>
                <td class="px-6 py-4">${formEmp.CID || ''}</td>
                <td class="px-6 py-4">${formEmp['DATE RESIGNED'] || ''}</td>
                <td class="px-6 py-4">${formEmp.STATUS || ''}</td>
                <td class="px-6 py-4 flex space-x-2">
                    <button data-id="${formEmp.id}" class="edit-form-emp-btn font-medium text-blue-600 dark:text-blue-500 hover:underline">Edit</button>
                    <button data-id="${formEmp.id}" class="delete-form-emp-btn font-medium text-red-600 dark:text-red-500 hover:underline">Delete</button>
                </td>
            `;
            formerEmployeesListTableBody.appendChild(row);
        });

        document.querySelectorAll('#formerEmployeesListModal .edit-form-emp-btn').forEach(button => {
            button.addEventListener('click', (event) => openEditFormEmpModal(event.target.dataset.id));
        });

        document.querySelectorAll('#formerEmployeesListModal .delete-form-emp-btn').forEach(button => {
            button.addEventListener('click', async (event) => {
                const confirmed = await window.customConfirm('Are you sure you want to delete this former employee record?');
                if (confirmed) {
                    deleteFormEmp(event.target.dataset.id);
                }
            });
        });
    }

    async function openEditFormEmpModal(id) {
        formEmpForm.reset();
        formEmpIdInput.value = '';
        formEmpBranchInput.removeAttribute('required');
        formEmpNameInput.removeAttribute('required');


        if (id) {
            formEmpModalTitle.textContent = 'Edit Former Employee Record';
            try {
                const response = await fetch(`${API_BASE_URL}/api/form_emp/${id}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                const formEmp = data.form_emp_record;

                if (formEmp) {
                    formEmpIdInput.value = formEmp.id;
                    formEmpBranchInput.value = formEmp.BRANCH || '';
                    formEmpNameInput.value = formEmp.NAME || '';
                    formEmpCidInput.value = formEmp.CID || '';
                    formEmpDateResignedInput.value = formEmp['DATE RESIGNED'] || '';
                    formEmpStatusInput.value = formEmp.STATUS || '';
                    formEmpBranchInput.setAttribute('required', 'required');
                    formEmpNameInput.setAttribute('required', 'required');
                } else {
                    window.showMessageBox('Former employee record not found.', 'error');
                    return;
                }
            } catch (error) {
                console.error('Error fetching Former Employee record for edit:', error);
                window.showMessageBox('Failed to load record for editing.', 'error');
                return;
            }
        } else {
            formEmpModalTitle.textContent = 'Add New Former Employee';
            formEmpBranchInput.setAttribute('required', 'required');
            formEmpNameInput.setAttribute('required', 'required');
        }
        window.openModal(formEmpModal);
    }

    formEmpForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        const formData = {
            BRANCH: formEmpBranchInput.value,
            NAME: formEmpNameInput.value,
            CID: formEmpCidInput.value ? formEmpCidInput.value : '',
            'DATE RESIGNED': formEmpDateResignedInput.value,
            STATUS: formEmpStatusInput.value
        };

        const id = formEmpIdInput.value;
        let url = `${API_BASE_URL}/api/form_emp`;
        let method = 'POST';

        if (id) {
            url = `${API_BASE_URL}/api/form_emp/${id}`;
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
                window.closeModal(formEmpModal);
                fetchFormEmpData(formEmpSearchInput.value, formEmpStatusFilter.value);
            } else {
                window.showMessageBox(result.error || 'Operation failed', 'error');
            }
        } catch (error) {
            console.error('Error submitting Former Employee form:', error);
            window.showMessageBox('An error occurred during submission.', 'error');
        }
    });

    async function deleteFormEmp(id) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/form_emp/${id}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (response.ok) {
                window.showMessageBox(result.message, 'success');
                fetchFormEmpData(formEmpSearchInput.value, formEmpStatusFilter.value);
            } else {
                window.showMessageBox(result.error || 'Deletion failed', 'error');
            }
        } catch (error) {
            console.error('Error deleting Former Employee record:', error);
            window.showMessageBox('An error occurred during deletion.', 'error');
        }
    }

    // --- Former Employees CSV Upload Handling ---

    uploadFormEmpCsvForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        const file = formEmpCsvFileInput.files[0];
        if (!file) {
            window.showMessageBox('Please select a CSV file to upload.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('csv_file', file);
        formData.append('upload_option', formEmpOverrideAllRadio.checked ? 'override' : 'append');

        try {
            const response = await fetch(`${API_BASE_URL}/api/form_emp/upload_csv`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                window.showMessageBox(result.message, 'success');
                window.closeModal(uploadFormEmpCsvModal);
                fetchFormEmpData(formEmpSearchInput.value, formEmpStatusFilter.value);
            } else {
                window.showMessageBox(result.error || 'CSV upload failed', 'error');
            }
        } catch (error) {
            console.error('Error uploading Former Employee CSV:', error);
            window.showMessageBox('An error occurred during CSV upload.', 'error');
        }
    });


    // --- Former Employees Summary Report Functions ---

    // Function to fetch Former Employees list for summary reports
    window.fetchFormEmpListForSummary = async function() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/form_emp_list`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const formEmpData = await response.json();
            return formEmpData.form_emp_list || [];
        } catch (error) {
            console.error('Error fetching Former Employees list for summary:', error);
            return [];
        }
    };


    // Function to fetch and display Former Employee Loan Balances
    window.loadFormEmpLoanBalances = async function(formEmpList) {
        formEmpLoanStatus.classList.remove('hidden');
        formEmpLoanError.classList.add('hidden');
        formEmpLoanNoData.classList.add('hidden');
        formEmpLoanSummaryTiles.classList.remove('hidden');

        formEmpLoanTableBody.innerHTML = '<tr><td colspan="9" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">Loading loan balance details...</td></tr>';

        formEmpLoanCurrentBalanceAmount.innerText = '₱0.00';
        formEmpLoanTotalPastDueAmount.innerText = '₱0.00';
        formEmpPastDue1_30DaysAmount.innerText = '₱0.00';
        formEmpPastDue31_60DaysAmount.innerText = '₱0.00';
        formEmpPastDue61_90DaysAmount.innerText = '₱0.00';
        formEmpPastDue91_120DaysAmount.innerText = '₱00.00';
        formEmpPastDue121_180DaysAmount.innerText = '₱0.00';
        formEmpPastDue181_365DaysAmount.innerText = '₱0.00';
        formEmpPastDueOver365DaysAmount.innerText = '₱0.00';

        try {
            if (!formEmpList || formEmpList.length === 0) {
                formEmpLoanStatus.classList.add('hidden');
                formEmpLoanNoData.classList.remove('hidden');
                formEmpLoanSummaryTiles.classList.add('hidden');
                formEmpLoanTableBody.innerHTML = '<tr><td colspan="9" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">No Former Employees to process loan data.</td></tr>';
                // Reset currentFormEmpLoanBalanceDetails through the global parent scope (operations_dosri.js)
                if (window.currentFormEmpLoanBalanceDetails) window.currentFormEmpLoanBalanceDetails = []; 
                return;
            }

            const response = await fetch(`${API_BASE_URL}/api/form_emp/loan_balances`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ form_emp_members: formEmpList }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log("Former Employee Loan Balances API Response:", data);

            const currentBalance = data.current_balance || 0;
            const totalPastDueBalance = data.past_due_balance || 0;
            const pastDueBreakdown = data.past_due_breakdown || {};
            const loanBalanceDetails = data.loan_balance_details || [];

            // Update currentFormEmpLoanBalanceDetails through the global parent scope
            if (window.currentFormEmpLoanBalanceDetails) window.currentFormEmpLoanBalanceDetails = loanBalanceDetails;

            if (currentBalance === 0 && totalPastDueBalance === 0 && loanBalanceDetails.length === 0) {
                formEmpLoanStatus.classList.add('hidden');
                formEmpLoanNoData.classList.remove('hidden');
                formEmpLoanSummaryTiles.classList.add('hidden');
                formEmpLoanTableBody.innerHTML = '<tr><td colspan="9" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">No loan balance details found for Former Employees.</td></tr>';
            } else {
                formEmpLoanCurrentBalanceAmount.innerText = window.formatCurrency(currentBalance);
                formEmpLoanTotalPastDueAmount.innerText = window.formatCurrency(totalPastDueBalance);

                formEmpPastDue1_30DaysAmount.innerText = window.formatCurrency(pastDueBreakdown['1-30 DAYS'] || 0);
                formEmpPastDue31_60DaysAmount.innerText = window.formatCurrency(pastDueBreakdown['31-60 DAYS'] || 0);
                formEmpPastDue61_90DaysAmount.innerText = window.formatCurrency(pastDueBreakdown['61-90 DAYS'] || 0);
                formEmpPastDue91_120DaysAmount.innerText = window.formatCurrency(pastDueBreakdown['91-120 DAYS'] || 0);
                formEmpPastDue121_180DaysAmount.innerText = window.formatCurrency(pastDueBreakdown['121-180 DAYS'] || 0);
                formEmpPastDue181_365DaysAmount.innerText = window.formatCurrency(pastDueBreakdown['181-365 DAYS'] || 0);
                formEmpPastDueOver365DaysAmount.innerText = window.formatCurrency(pastDueBreakdown['OVER 365 DAYS'] || 0);

                formEmpLoanStatus.classList.add('hidden');
                renderFormEmpLoanTable(loanBalanceDetails); // Pass local variable
            }
        } catch (error) {
            console.error('Error loading former employee loan balances:', error);
            formEmpLoanStatus.classList.add('hidden');
            formEmpLoanError.classList.remove('hidden');
            formEmpLoanSummaryTiles.classList.add('hidden');
            formEmpLoanTableBody.innerHTML = '<tr><td colspan="9" class="px-6 py-4 whitespace-nowrap text-center text-red-500">Error loading former employee loan balance details.</td></tr>';
            if (window.currentFormEmpLoanBalanceDetails) window.currentFormEmpLoanBalanceDetails = [];
        }
    };

    function renderFormEmpLoanTable(details, searchTerm = '') {
        formEmpLoanTableBody.innerHTML = '';
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
                    <td class="px-6 py-4 whitespace-nowrap">${row['LOAN ACCT.'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">${window.formatCurrency(row['PRINCIPAL BALANCE'])}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['PRODUCT'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['DISBDATE'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['DUE DATE'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['AGING'] || ''}</td>
                `;
                formEmpLoanTableBody.appendChild(tr);
            });
        } else {
            formEmpLoanTableBody.innerHTML = '<tr><td colspan="9" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">No matching loan balance details found for Former Employees.</td></tr>';
        }
    }

    // Function to fetch and display Former Employee Deposit Liabilities
    window.loadFormEmpDepositLiabilities = async function(formEmpList) {
        formEmpDepositStatus.classList.remove('hidden');
        formEmpDepositError.classList.add('hidden');
        formEmpDepositNoData.classList.add('hidden');
        formEmpDepositLiabilitiesTiles.classList.remove('hidden');

        formEmpDepositLiabilitiesTableBody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">Loading deposit liabilities details...</td></tr>'; 

        formEmpRegularSavingsAmount.innerText = '₱0.00';
        formEmpAtmSavingsAmount.innerText = '₱0.00';
        formEmpShareCapitalAmount.innerText = '₱0.00';
        formEmpTimeDepositsAmount.innerText = '₱0.00';
        formEmpYouthSavingsAmount.innerText = '₱0.00';
        formEmpSpecialDepositsAmount.innerText = '₱0.00';
        
        if (formEmpRegularSavingsCount) formEmpRegularSavingsCount.innerText = 'Accounts: 0';
        if (formEmpAtmSavingsCount) formEmpAtmSavingsCount.innerText = 'Accounts: 0';
        if (formEmpShareCapitalCount) formEmpShareCapitalCount.innerText = 'Accounts: 0';
        if (formEmpTimeDepositsCount) formEmpTimeDepositsCount.innerText = 'Accounts: 0';
        if (formEmpYouthSavingsCount) formEmpYouthSavingsCount.innerText = 'Accounts: 0';
        if (formEmpSpecialDepositsCount) formEmpSpecialDepositsCount.innerText = 'Accounts: 0';


        try {
            if (!formEmpList || formEmpList.length === 0) {
                formEmpDepositStatus.classList.add('hidden');
                formEmpDepositNoData.classList.remove('hidden');
                formEmpDepositLiabilitiesTiles.classList.add('hidden');
                formEmpDepositLiabilitiesTableBody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">No Former Employees to process deposit data.</td></tr>'; 
                
                if (formEmpRegularSavingsCount) formEmpRegularSavingsCount.innerText = 'Accounts: 0';
                if (formEmpAtmSavingsCount) formEmpAtmSavingsCount.innerText = 'Accounts: 0';
                if (formEmpShareCapitalCount) formEmpShareCapitalCount.innerText = 'Accounts: 0';
                if (formEmpTimeDepositsCount) formEmpTimeDepositsCount.innerText = 'Accounts: 0';
                if (formEmpYouthSavingsCount) formEmpYouthSavingsCount.innerText = 'Accounts: 0';
                if (formEmpSpecialDepositsCount) formEmpSpecialDepositsCount.innerText = 'Accounts: 0';
                if (window.currentFormEmpDepositLiabilitiesDetails) window.currentFormEmpDepositLiabilitiesDetails = [];
                return;
            }

            const response = await fetch(`${API_BASE_URL}/api/form_emp/deposit_liabilities`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ form_emp_members: formEmpList }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log("Former Employee Deposit Liabilities API Response:", data);

            formEmpRegularSavingsAmount.innerText = window.formatCurrency(data.regular_savings || 0);
            formEmpAtmSavingsAmount.innerText = window.formatCurrency(data.atm_savings || 0);
            formEmpShareCapitalAmount.innerText = window.formatCurrency(data.share_capital || 0);
            formEmpTimeDepositsAmount.innerText = window.formatCurrency(data.time_deposits || 0);
            formEmpYouthSavingsAmount.innerText = window.formatCurrency(data.youth_savings || 0);
            formEmpSpecialDepositsAmount.innerText = window.formatCurrency(data.special_deposits || 0);

            formEmpDepositStatus.classList.add('hidden');

            const totalDeposits = (data.regular_savings || 0) + (data.share_capital || 0) +
                                 (data.time_deposits || 0) + (data.youth_savings || 0) +
                                 (data.atm_savings || 0) +
                                 (data.special_deposits || 0);
            if (totalDeposits === 0 && Object.keys(data.deposit_accounts_count || {}).length === 0 && (data.deposit_liabilities_details || []).length === 0) {
                formEmpDepositNoData.classList.remove('hidden');
                formEmpDepositLiabilitiesTiles.classList.add('hidden');
            }


            if (formEmpRegularSavingsCount) formEmpRegularSavingsCount.innerText = `Accounts: ${data.deposit_accounts_count['REGULAR SAVINGS'] || 0}`;
            if (formEmpAtmSavingsCount) formEmpAtmSavingsCount.innerText = `Accounts: ${data.deposit_accounts_count['ATM SAVINGS'] || 0}`;
            if (formEmpShareCapitalCount) formEmpShareCapitalCount.innerText = `Accounts: ${data.deposit_accounts_count['SHARE CAPITAL'] || 0}`;
            
            let totalTimeDepositAccounts = 0;
            const timeDepositKeys = [
                'TIME DEPOSIT - MATURITY', 
                'TIME DEPOSIT - MONTHLY', 
                'TIME DEPOSIT -A', 
                'TIME DEPOSIT -B', 
                'TIME DEPOSIT -C'
            ];
            timeDepositKeys.forEach(key => {
                totalTimeDepositAccounts += (data.deposit_accounts_count[key] || 0);
            });
            if (formEmpTimeDepositsCount) formEmpTimeDepositsCount.innerText = `Accounts: ${totalTimeDepositAccounts}`;

            if (formEmpYouthSavingsCount) formEmpYouthSavingsCount.innerText = `Accounts: ${data.deposit_accounts_count['YOUTH SAVINGS CLUB'] || 0}`;
            
            const categorizedAccountTypesForCount = [
                'REGULAR SAVINGS',
                'SHARE CAPITAL',
                'YOUTH SAVINGS CLUB',
                'ATM SAVINGS'
            ].concat(timeDepositKeys);

            let totalSpecialDepositAccounts = 0;
            for (const accName in data.deposit_accounts_count) {
                if (!categorizedAccountTypesForCount.includes(accName)) {
                    totalSpecialDepositAccounts += data.deposit_accounts_count[accName];
                }
            }
            if (formEmpSpecialDepositsCount) formEmpSpecialDepositsCount.innerText = `Accounts: ${totalSpecialDepositAccounts}`;


            if (window.currentFormEmpDepositLiabilitiesDetails) window.currentFormEmpDepositLiabilitiesDetails = data.deposit_liabilities_details || [];
            renderFormEmpDepositTable(data.deposit_liabilities_details);


        } catch (error) {
            console.error('Error loading former employee deposit liabilities:', error);
            formEmpDepositStatus.classList.add('hidden');
            formEmpDepositError.classList.remove('hidden');
            formEmpDepositLiabilitiesTiles.classList.add('hidden');
            if (formEmpRegularSavingsCount) formEmpRegularSavingsCount.innerText = 'Accounts: N/A';
            if (formEmpAtmSavingsCount) formEmpAtmSavingsCount.innerText = 'Accounts: N/A';
            if (formEmpShareCapitalCount) formEmpShareCapitalCount.innerText = 'Accounts: N/A';
            if (formEmpTimeDepositsCount) formEmpTimeDepositsCount.innerText = 'Accounts: N/A';
            if (formEmpYouthSavingsCount) formEmpYouthSavingsCount.innerText = 'Accounts: N/A';
            if (formEmpSpecialDepositsCount) formEmpSpecialDepositsCount.innerText = 'Accounts: N/A';
            formEmpDepositLiabilitiesTableBody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 whitespace-nowrap text-center text-red-500">Error loading deposit liabilities details.</td></tr>'; 
            if (window.currentFormEmpDepositLiabilitiesDetails) window.currentFormEmpDepositLiabilitiesDetails = [];
        }
    };

    function renderFormEmpDepositTable(details, searchTerm = '') {
        formEmpDepositLiabilitiesTableBody.innerHTML = '';
        
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
                    <td class="px-6 py-4 whitespace-nowrap">${row['CID'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['PRODUCT ACCNAME'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${row['OPENED DOPEN'] || ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">${window.formatCurrency(row['BALANCE BAL'])}</td>
                `;
                formEmpDepositLiabilitiesTableBody.appendChild(tr);
            });
        } else {
            formEmpDepositLiabilitiesTableBody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">No matching deposit liabilities details found for Former Employees.</td></tr>'; 
        }
    }


    // --- Event Listeners (Former Employee Specific) ---

    let formEmpSearchTimeout;
    formEmpSearchInput.addEventListener('keyup', () => {
        clearTimeout(formEmpSearchTimeout);
        formEmpSearchTimeout = setTimeout(() => {
            fetchFormEmpData(formEmpSearchInput.value, formEmpStatusFilter.value);
        }, 300);
    });

    formEmpStatusFilter.addEventListener('change', () => {
        fetchFormEmpData(formEmpSearchInput.value, formEmpStatusFilter.value);
    });

    if (openFormerEmployeesListBtn) {
        openFormerEmployeesListBtn.addEventListener('click', () => {
            window.openModal(formerEmployeesListModal);
            fetchFormEmpData();
        });
    }

    if (closeFormerEmployeesListModalBtn) {
        closeFormerEmployeesListModalBtn.addEventListener('click', () => window.closeModal(formerEmployeesListModal));
    }

    if (addFormEmpBtn) {
        addFormEmpBtn.addEventListener('click', () => openEditFormEmpModal());
    }

    const cancelFormEmpBtnForm = document.getElementById('cancelFormEmpBtnForm');
    if (cancelFormEmpBtn) {
        cancelFormEmpBtn.addEventListener('click', () => window.closeModal(formEmpModal));
    }
    if (cancelFormEmpBtnForm) {
        cancelFormEmpBtnForm.addEventListener('click', () => window.closeModal(formEmpModal));
    }

    if (uploadFormEmpCsvBtn) {
        uploadFormEmpCsvBtn.addEventListener('click', () => {
            uploadFormEmpCsvForm.reset();
            window.openModal(uploadFormEmpCsvModal);
        });
    }

    const cancelUploadFormEmpCsvBtnForm = document.getElementById('cancelUploadFormEmpCsvBtnForm');
    if (cancelUploadFormEmpCsvBtn) {
        cancelUploadFormEmpCsvBtn.addEventListener('click', () => window.closeModal(uploadFormEmpCsvModal));
    }
    if (cancelUploadFormEmpCsvBtnForm) {
        cancelUploadFormEmpCsvBtnForm.addEventListener('click', () => window.closeModal(uploadFormEmpCsvModal));
    }

    formEmpLoanBalanceSearchInput.addEventListener('keyup', (event) => {
        renderFormEmpLoanTable(currentFormEmpLoanBalanceDetails, event.target.value);
    });

    copyFormEmpLoanBalanceTableBtn.addEventListener('click', () => {
        window.copyTableToClipboard('form-emp-loan-table-body');
    });

    formEmpDepositLiabilitiesSearchInput.addEventListener('keyup', (event) => {
        renderFormEmpDepositTable(currentFormEmpDepositLiabilitiesDetails, event.target.value);
    });

    copyFormEmpDepositLiabilitiesTableBtn.addEventListener('click', () => {
        window.copyTableToClipboard('form-emp-deposit-liabilities-table-body');
    });
});
