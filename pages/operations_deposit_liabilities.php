<?php
// pages/operations_deposit_liabilities.php
?>
<div id="operationsDepositLiabilities">
    <div class="dashboard-card card-span-full">
        <h3 class="card-title">
            Deposit Liabilities Report
        </h3>

        <h4 class="text-xl font-semibold text-gray-700 mb-4">Report Criteria</h4>
        <!-- Changed flex-nowrap to flex-wrap to allow items to move to the next row -->
        <div class="flex flex-wrap items-end gap-4 pb-4">
            <!-- Removed flex-shrink-0 to allow input groups to be more flexible -->
            <div class="input-group">
                <label for="depositLiabilitiesArea" class="input-label">AREA:</label>
                <select id="depositLiabilitiesArea" class="select-field">
                    <option value="">Select Area</option>
                    <option value="Consolidated">Consolidated (All Branches)</option>
                    <option value="Area 1">Area 1</option>
                    <option value="Area 2">Area 2</option>
                    <option value="Area 3">Area 3</option>
                </select>
            </div>
            <!-- Removed flex-shrink-0 to allow input groups to be more flexible -->
            <div class="input-group">
                <label for="depositLiabilitiesBranch" class="input-label">Branch:</label>
                <select id="depositLiabilitiesBranch" class="select-field" disabled>
                    <option value="">Select Branch</option>
                    <!-- Options populated by JS based on Area selection -->
                </select>
            </div>
            <!-- NEW: Month and Year Selectors -->
            <!-- Removed flex-shrink-0 to allow input groups to be more flexible -->
            <div class="input-group">
                <label for="depositLiabilitiesMonth" class="input-label">Month:</label>
                <select id="depositLiabilitiesMonth" class="select-field">
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
                <label for="depositLiabilitiesYear" class="input-label">Year:</label>
                <select id="depositLiabilitiesYear" class="select-field">
                    <option value="">Select Year</option>
                    <?php
                        // Dynamically generate years from 2021 to 2030
                        for ($year = 2021; $year <= 2030; $year++) {
                            echo '<option value="' . $year . '">' . $year . '</option>';
                        }
                    ?>
                </select>
            </div>
            <!-- END NEW: Month and Year Selectors -->
            <!-- Removed flex-shrink-0 to allow input groups to be more flexible -->
            <div class="input-group">
                <button id="generateDepositLiabilitiesButton" class="process-button" disabled>
                    Generate Report
                </button>
            </div>
        </div>

        <hr class="my-8 border-gray-200">

        <!-- NEW: Maturity and Interest Buttons -->
        <h4 class="text-xl font-semibold text-gray-700 mb-4 mt-8">Configuration</h4>
        <!-- Changed flex-nowrap to flex-wrap to allow items to move to the next row -->
        <div class="flex flex-wrap items-end gap-4 pb-4">
            <div class="input-group">
                <button id="openMaturityModalButton" class="process-button" style="background-color: #3b82f6;">
                    Maturity Configuration
                </button>
            </div>
            <div class="input-group">
                <button id="openInterestModalButton" class="process-button" style="background-color: #f97316;">
                    Interest Rate Configuration
                </button>
            </div>
        </div>
        <!-- END NEW: Maturity and Interest Buttons -->

        <hr class="my-8 border-gray-200">

        <h4 class="text-xl font-semibold text-gray-700 mb-4 mt-8">Deposit Products Summary</h4>
        <div id="depositProductsSummaryContainer" class="mt-4">
            <p class="text-gray-500 text-center col-span-full">Deposit product summaries will appear here after generation.</p>
        </div>

        <!-- NEW: Matured Deposits Report Section -->
        <hr class="my-8 border-gray-200">
        <h4 class="text-xl font-semibold text-gray-700 mb-4 mt-8">Matured Deposits Report <span id="maturedDepositsYearSpan" class="text-gray-500 text-base font-normal ml-2"></span></h4>
        <div id="maturedDepositsReportActions" class="mt-4 flex flex-col sm:flex-row justify-end items-center gap-4 hidden">
            <div class="relative w-full sm:w-1/2 md:w-1/3">
                <input type="text" id="maturedDepositsSearchInput" class="text-input-field pr-10" placeholder="Search table...">
                <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
            </div>
            <button id="copyMaturedDepositsTableButton" class="process-button w-full sm:w-auto" style="background-color: #4f46e5;">
                Copy Table
            </button>
        </div>
        <div class="table-scroll-wrapper">
            <div id="maturedDepositsReportTableContainer" class="mt-4 overflow-x-auto" style="min-height: 200px; background-color: #f0f9ff; border: 2px dashed #93c5fd;">
                <p class="text-gray-500 text-center">Matured Deposits report will appear here.</p>
            </div>
        </div>

        <!-- NEW: Wrong Application of Interest Report Section -->
        <hr class="my-8 border-gray-200">
        <h4 class="text-xl font-semibold text-gray-700 mb-4 mt-8">Wrong Application of Interest Report <span id="wrongInterestYearSpan" class="text-gray-500 text-base font-normal ml-2"></span></h4>
        <div id="wrongInterestReportActions" class="mt-4 flex flex-col sm:flex-row justify-end items-center gap-4 hidden">
            <div class="relative w-full sm:w-1/2 md:w-1/3">
                <input type="text" id="wrongInterestSearchInput" class="text-input-field pr-10" placeholder="Search table...">
                <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
            </div>
            <button id="copyWrongInterestTableButton" class="process-button w-full sm:w-auto" style="background-color: #4f46e5;">
                Copy Table
            </button>
        </div>
        <div class="table-scroll-wrapper">
            <div id="wrongInterestReportTableContainer" class="mt-4 overflow-x-auto" style="min-height: 200px; background-color: #f0f9ff; border: 2px dashed #93c5fd;">
                <p class="text-gray-500 text-center">Wrong Application of Interest report will appear here.</p>
            </div>
        </div>

    </div>
</div>
<script type="module" src="js/tabs/operations_deposit_liabilities.js" defer></script>
<link rel="stylesheet" href="css/operations_dc.css">

<!-- Maturity Details Modal -->
<div id="maturityModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 hidden justify-center items-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Modal Header -->
        <div class="flex justify-between items-center p-4 border-b border-gray-200">
            <h3 id="maturityModalTitle" class="text-xl font-semibold text-gray-800">Maturity Requirements</h3>
            <button id="closeMaturityModalButton" class="text-gray-500 hover:text-gray-700 text-2xl leading-none">&times;</button>
        </div>
        
        <!-- Modal Body (Table Container) -->
        <div class="p-4 overflow-auto flex-grow">
            <div id="maturityTableContainer" class="min-h-[150px] bg-gray-50 p-4 rounded-lg border border-gray-200">
                <p class="text-gray-500 text-center">Loading maturity data...</p>
            </div>
            <div class="mt-4 flex justify-end items-center gap-4">
                <button id="addMaturityRowButton" class="process-button">
                    <i class="fas fa-plus-circle mr-2"></i> Add Row
                </button>
                <button id="saveMaturityButton" class="process-button" style="background-color: #4f46e5;">
                    <i class="fas fa-save mr-2"></i> Save
                </button>
            </div>
        </div>
    </div>
</div>

<!-- Interest Details Modal -->
<div id="interestModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 hidden justify-center items-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Modal Header -->
        <div class="flex justify-between items-center p-4 border-b border-gray-200">
            <h3 id="interestModalTitle" class="text-xl font-semibold text-gray-800">Interest Rates</h3>
            <button id="closeInterestModalButton" class="text-gray-500 hover:text-gray-700 text-2xl leading-none">&times;</button>
        </div>
        
        <!-- Modal Body (Table Container) -->
        <div class="p-4 overflow-auto flex-grow">
            <div id="interestTableContainer" class="min-h-[150px] bg-gray-50 p-4 rounded-lg border border-gray-200">
                <p class="text-gray-500 text-center">Loading interest data...</p>
            </div>
            <div class="mt-4 flex justify-end items-center gap-4">
                <button id="addInterestRowButton" class="process-button">
                    <i class="fas fa-plus-circle mr-2"></i> Add Row
                </button>
                <button id="saveInterestButton" class="process-button" style="background-color: #4f46e5;">
                    <i class="fas fa-save mr-2"></i> Save
                </button>
            </div>
        </div>
    </div>
</div>
