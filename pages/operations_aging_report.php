<?php
// pages/operations_aging_report.php
?>
<div id="operationsAgingReport">
    <div class="dashboard-card card-span-full">
        <h3 class="card-title">Operations Aging Report <span id="agingReportAsOfDate" class="text-gray-500 text-base font-normal ml-2"></span></h3>

        <h4 class="text-xl font-semibold text-gray-700 mb-4">Report Criteria</h4>
        <!-- Changed flex-nowrap to flex-wrap to allow items to move to the next row -->
        <div class="flex flex-wrap items-end gap-4 pb-4">
            <!-- Removed flex-shrink-0 to allow input groups to be more flexible -->
            <div class="input-group">
                <label for="agingArea" class="input-label">AREA:</label>
                <select id="agingArea" class="select-field">
                    <option value="">Select Area</option>
                    <option value="Consolidated">Consolidated (All Branches)</option>
                    <option value="Area 1">Area 1</option>
                    <option value="Area 2">Area 2</option>
                    <option value="Area 3">Area 3</option>
                </select>
            </div>
            <!-- Removed flex-shrink-0 to allow input groups to be more flexible -->
            <div class="input-group"> <label for="agingBranch" class="input-label">Branch:</label>
                <select id="agingBranch" class="select-field" disabled>
                    <option value="">Select Branch</option>
                    <option value="AGLAYAN">AGLAYAN</option>
                    <option value="AGORA">AGORA</option>
                    <option value="BALINGASAG">BALINGASAG</option>
                    <option value="BAUNGON">BAUNGON</option>
                    <option value="BULUA">BULUA</option>
                    <option value="BUTUAN">BUTUAN</option>
                    <option value="CARMEN">CARMEN</option>
                    <option value="COGON">COGON</option>
                    <option value="DON CARLOS">DON CARLOS</option>
                    <option value="EL SALVADOR">EL SALVADOR</option>
                    <option value="GINGOOG">GINGOOG</option>
                    <option value="ILIGAN">ILIGAN</option>
                    <option value="ILUSTRE">ILUSTRE</option>
                    <option value="MANOLO">MANOLO</option>
                    <option value="MARAMAG">MARAMAG</option>
                    <option value="PUERTO">PUERTO</option>
                    <option value="TAGBILARAN">TAGBILARAN</option>
                    <option value="TALAKAG">TALAKAG</option>
                    <option value="TORIL">TORIL</option>
                    <option value="TUBIGON">TUBIGON</option>
                    <option value="UBAY">UBAY</option>
                    <option value="VALENCIA">VALENCIA</option>
                    <option value="YACAPIN">YACAPIN</option>
                </select>
            </div>
            <!-- NEW: Date selection dropdown -->
            <div class="input-group">
                <label for="agingDate" class="input-label">Date:</label>
                <select id="agingDate" class="select-field" disabled>
                    <option value="">Select Date</option>
                </select>
            </div>
        </div>

        <hr class="my-8 border-gray-200">

        <h4 class="text-xl font-semibold text-gray-700 mb-4">Summary Totals <span id="agingSummaryAsOfDate" class="text-gray-500 text-base font-normal ml-2"></span></h4>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="summary-tile bg-green-100 border-green-400 text-green-800">
                <div class="tile-label">TOTAL CURRENT BALANCE</div>
                <div class="tile-value" id="totalCurrentBalance">0.00</div>
                <div class="tile-sub-label text-sm mt-1" id="currentAccountsCount">Accounts: 0</div>
            </div>
            <div class="summary-tile bg-red-100 border-red-400 text-red-800">
                <div class="tile-label">TOTAL PAST DUE</div>
                <div class="tile-value" id="totalPastDue">0.00</div>
                <div class="tile-sub-label text-sm mt-1" id="pastDueAccountsCount">Accounts: 0</div>
            </div>
            <div class="summary-tile bg-blue-100 border-blue-400 text-blue-800">
                <div class="tile-label">TOTAL BOTH CURRENT & PAST DUE</div>
                <div class="tile-value" id="totalBothDue">0.00</div>
                <div class="tile-sub-label text-sm mt-1" id="totalAccountsCount">Accounts: 0</div>
            </div>
            <div class="summary-tile bg-purple-100 border-purple-400 text-purple-800">
                <div class="tile-label">DELINQUENCY RATE (%)</div>
                <div class="tile-value" id="delinquencyRate">0.00%</div>
                <div class="tile-sub-label text-sm mt-1" id="totalProvisions">Total Provisions: 0.00</div>
            </div>
            <div class="summary-tile bg-yellow-100 border-yellow-400 text-yellow-800">
                <div class="tile-label">PROVISION (1-365 DAYS)</div>
                <div class="tile-value" id="provision1To365DaysBalance">0.00</div>
                <div class="tile-sub-label text-sm mt-1" id="provision1To365DaysAccountsCount">Accounts: 0</div>
            </div>
            <div class="summary-tile bg-orange-100 border-orange-400 text-orange-800">
                <div class="tile-label">PROVISION (OVER 365 DAYS)</div>
                <div class="tile-value" id="provisionOver365DaysBalance">0.00</div>
                <div class="tile-sub-label text-sm mt-1" id="provisionOver365DaysAccountsCount">Accounts: 0</div>
            </div>
        </div>

        <hr class="my-8 border-gray-200">

        <h4 class="text-xl font-semibold text-gray-700 mb-4 mt-8">Top Borrowers</h4>
        <!-- Changed flex-nowrap to flex-wrap to allow items to move to the next row -->
        <div class="flex flex-wrap items-end gap-4 pb-4">
            <!-- Removed flex-shrink-0 to allow input groups to be more flexible -->
            <div class="input-group">
                <label for="topBorrowersStatus" class="input-label">STATUS:</label>
                <select id="topBorrowersStatus" class="select-field">
                    <option value="">Select Status</option>
                    <option value="CURRENT">CURRENT</option>
                    <option value="PAST DUE">PAST DUE</option>
                </select>
            </div>
            <!-- Removed flex-shrink-0 to allow input groups to be more flexible -->
            <div class="input-group">
                <button id="generateTopBorrowersReportButton" class="process-button" disabled>
                    Generate Top Borrowers Report
                </button>
            </div>
        </div>

        <div id="topBorrowersReportActions" class="mt-4 flex flex-col sm:flex-row justify-end items-center gap-4 hidden">
            <div class="relative w-full sm:w-1/2 md:w-1/3">
                <input type="text" id="topBorrowersSearchInput" class="text-input-field pr-10" placeholder="Search table...">
                <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
            </div>
            <button id="copyTopBorrowersTableButton" class="process-button w-full sm:w-auto" style="background-color: #4f46e5;">
                Copy Table
            </button>
        </div>

        <div class="table-scroll-wrapper">
            <div id="topBorrowersTableContainer" class="mt-4 overflow-x-auto" style="min-height: 200px; background-color: #f0f9ff; border: 2px dashed #93c5fd;">
                <h5 class="text-lg font-semibold text-gray-700 mb-2 p-2">TOP BORROWERS</h5>
                <p class="text-gray-500 text-center">Top Borrowers report will appear here.</p>
            </div>
        </div>
        <hr class="my-8 border-gray-200">

        <h4 class="text-xl font-semibold text-gray-700 mb-4 mt-8">New Loans with Past due Credit History</h4>
        <!-- Changed flex-nowrap to flex-wrap to allow items to move to the next row -->
        <div class="flex flex-wrap items-end gap-4 pb-4">
            <!-- Removed flex-shrink-0 to allow input groups to be more flexible -->
            <div class="input-group">
                <label for="newLoansYear" class="input-label">Year Release of New Loan:</label>
                <select id="newLoansYear" class="select-field">
                    <option value="">Select Year</option>
                </select>
            </div>
            <!-- Removed flex-shrink-0 to allow input groups to be more flexible -->
            <div class="input-group">
                <button id="generateNewLoansReportButton" class="process-button" disabled>
                    Generate Report
                </button>
            </div>
        </div>

        <div id="newLoansReportActions" class="mt-4 flex flex-col sm:flex-row justify-end items-center gap-4 hidden">
            <div class="relative w-full sm:w-1/2 md:w-1/3">
                <input type="text" id="newLoansSearchInput" class="text-input-field pr-10" placeholder="Search table...">
                <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
            </div>
            <button id="copyNewLoansTableButton" class="process-button w-full sm:w-auto" style="background-color: #4f46e5;">
                Copy Table
            </button>
        </div>

        <div class="table-scroll-wrapper">
            <div id="newLoansTableContainer" class="mt-4 overflow-x-auto" style="min-height: 200px; background-color: #f0f9ff; border: 2px dashed #93c5fd;">
                <p class="text-gray-500 text-center">New Loans with Past Due Credit History report will appear here.</p>
            </div>
        </div>

        <hr class="my-8 border-gray-200">

        <h4 class="text-xl font-semibold text-gray-700 mb-4 mt-8">ACCOUNTS CONTRIBUTE TO PROVISIONS</h4>
        <!-- Changed flex-nowrap to flex-wrap to allow items to move to the next row -->
        <div class="flex flex-wrap items-end gap-4 pb-4">
            <!-- Removed flex-shrink-0 to allow input groups to be more flexible -->
            <div class="input-group">
                <label for="provisionMonth" class="input-label">Month:</label>
                <select id="provisionMonth" class="select-field">
                    <option value="">Select Month</option>
                    <option value="1">January</option>
                    <option value="2">February</option>
                    <option value="3">March</option>
                    <option value="4">April</option>
                    <option value="5">May</option>
                    <option value="6">June</option>
                    <option value="7">July</option>
                    <option value="8">August</option>
                    <option value="9">September</option>
                    <option value="10">October</option>
                    <option value="11">November</option>
                    <option value="12">December</option>
                </select>
            </div>
            <!-- Removed flex-shrink-0 to allow input groups to be more flexible -->
            <div class="input-group">
                <label for="provisionYear" class="input-label">Year:</label>
                <select id="provisionYear" class="select-field">
                    <option value="">Select Year</option>
                    </select>
            </div>
            <!-- Removed flex-shrink-0 to allow input groups to be more flexible -->
            <div class="input-group">
                <label for="provisionAging" class="input-label">Aging:</label>
                <select id="provisionAging" class="select-field">
                    <option value="">Select Aging</option>
                    <option value="30-365 DAYS">30-365 DAYS</option>
                    <option value="OVER 365">OVER 365 DAYS</option>
                    <option value="30_TO_OVER_365_DAYS">30 DAYS to OVER 365 DAYS</option>
                </select>
            </div>
            <!-- Removed flex-shrink-0 to allow input groups to be more flexible -->
            <div class="input-group">
                <button id="generateProvisionsReportButton" class="process-button" disabled>
                    Generate Provisions Report
                </button>
            </div>
        </div>

        <div id="provisionsReportActions" class="mt-4 flex flex-col sm:flex-row justify-end items-center gap-4 hidden">
            <div class="relative w-full sm:w-1/2 md:w-1/3">
                <input type="text" id="provisionsSearchInput" class="text-input-field pr-10" placeholder="Search tables...">
                <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
            </div>
            <button id="copyProvisionsReportTablesButton" class="process-button w-full sm:w-auto" style="background-color: #4f46e5;">
                Copy All Tables
            </button>
        </div>

        <div class="table-scroll-wrapper">
            <div id="perAccountsTableContainer" class="mt-4 overflow-x-auto" style="min-height: 200px; background-color: #f0f9ff; border: 2px dashed #93c5fd;">
                <h5 class="text-lg font-semibold text-gray-700 mb-2 p-2">PER ACCOUNTS</h5>
                <p class="text-gray-500 text-center">Per Accounts report will appear here.</p>
            </div>
        </div>

        <div class="table-scroll-wrapper">
            <div id="perMemberTableContainer" class="mt-8 overflow-x-auto" style="min-height: 150px; background-color: #f0f9ff; border: 2px dashed #93c5fd;">
                <h5 class="text-lg font-semibold text-gray-700 mb-2 p-2">PER MEMBER</h5>
                <p class="text-gray-500 text-center">Per Member report will appear here.</p>
            </div>
        </div>
        <hr class="my-8 border-gray-200">

        <h4 class="text-xl font-semibold text-gray-700 mb-4 mt-8">Aging History per Member's Loan</h4>
        <!-- Changed flex-nowrap to flex-wrap to allow items to move to the next row -->
        <div id="agingReportControls" class="flex flex-wrap items-end gap-4 pb-4">
            <!-- Removed flex-shrink-0 to allow input groups to be more flexible -->
            <div class="input-group">
                <label for="agingName" class="input-label">Name:</label>
                <input type="text" id="agingName" class="text-input-field"
                       placeholder="Type Name" list="agingNamesDatalist">
                <datalist id="agingNamesDatalist"></datalist>
            </div>
            
            <!-- Removed flex-shrink-0 to allow input groups to be more flexible -->
            <div class="input-group">
                <label for="agingCid" class="input-label">CID:</label>
                <input type="text" id="agingCid" class="text-input-field"
                       placeholder="Autofilled CID" readonly>
            </div>

            <!-- Removed flex-shrink-0 to allow input groups to be more flexible -->
            <div class="input-group">
                <button id="processAgingReportButton" class="process-button" disabled>
                    Generate Report
                </button>
            </div>

            <div class="flex-grow hidden sm:block"></div>

            <div id="agingReportSearchCopy" class="flex flex-grow sm:flex-grow-0 items-center gap-4 hidden">
                <div class="relative w-full sm:w-1/2 md:w-1/3">
                    <input type="text" id="agingSearchInput" class="text-input-field pr-10" placeholder="Search table...">
                    <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                </div>
                <button id="copyAgingReportTableButton" class="process-button w-full sm:w-auto" style="background-color: #4f46e5;">
                    Copy Table
                </button>
            </div>
        </div>
        <div id="agingLegendContainer" class="mt-4 p-4 bg-gray-50 rounded-lg shadow-inner">
            <h5 class="text-lg font-semibold text-gray-700 mb-2">Aging Categories Legend:</h5>
            <div id="agingLegendItems" class="flex flex-wrap gap-x-4 gap-y-2 text-sm">
                </div>
        </div>
        <div id="agingReportTableContainer" class="mt-4 overflow-x-auto" style="background-color: #f0f9ff; border: 2px dashed #93c5fd;">
            <p class="text-gray-500 text-center">Aging report will appear here after generation.</p>
        </div>
    </div>
<!-- NEW: Include all split JavaScript files -->
<script src="js/tabs/operations_aging_report.js" defer></script>
<script src="js/tabs/operations_aging_report_aging_history.js" defer></script>
<script src="js/tabs/operations_aging_report_provisions.js" defer></script>
<script src="js/tabs/operations_aging_report_top_borrowers.js" defer></script>
<script src="js/tabs/operations_aging_report_new_loans.js" defer></script>

<!-- New Loans Details Modal Structure -->
<div id="newLoansDetailsModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 hidden justify-center items-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Modal Header -->
        <div class="flex justify-between items-center p-4 border-b border-gray-200">
            <h3 id="newLoansDetailsModalTitle" class="text-xl font-semibold text-gray-800">Loan Details</h3>
            <button id="newLoansDetailsModalCloseButton" class="text-gray-500 hover:text-gray-700 text-2xl leading-none">&times;</button>
        </div>
        
        <!-- Modal Actions (Search & Copy) -->
        <div class="flex flex-col sm:flex-row justify-end items-center gap-4 p-4 border-b border-gray-200">
            <div class="relative w-full sm:w-1/2 md:w-1/3">
                <input type="text" id="newLoansDetailsModalSearchInput" class="text-input-field pr-10" placeholder="Search details...">
                <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
            </div>
            <button id="newLoansDetailsModalCopyButton" class="process-button w-full sm:w-auto" style="background-color: #4f46e5;">
                Copy Table
            </button>
        </div>

        <!-- Modal Body (Table Container) -->
        <div id="newLoansDetailsModalTableContainer" class="p-4 overflow-auto flex-grow">
            <!-- Table will be rendered here by JavaScript -->
            <p class="text-gray-500 text-center">Details will appear here.</p>
        </div>
    </div>
</div>

