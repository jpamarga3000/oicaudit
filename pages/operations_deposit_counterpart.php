<?php
// pages/operations_deposit_counterpart.php
?>
<div id="operationsDepositCounterpart">
    <div class="dashboard-card card-span-full">
        <h3 class="card-title">
            Deposit Counterpart Requirements
        </h3>
        <p class="text-gray-600 mb-4" id="depositRequirementsDescription">
            Define the deposit requirements for each loan product. These settings will be saved for future use.
        </p>
        <div id="depositRequirementsContent" class="collapsible-content">
            <div class="mt-4 flex flex-col md:flex-row gap-4" id="depositRequirementsTablesWrapper">
                <!-- Table Column 1 -->
                <div class="w-full md:w-1/2 flex flex-col" id="depositRequirementsTableCol1">
                    <p class="text-gray-500 text-center py-8">Loading deposit requirements...</p>
                </div>
                <!-- Table Column 2 -->
                <div class="w-full md:w-1/2 flex flex-col" id="depositRequirementsTableCol2">
                    <!-- This column will also be populated by JS -->
                </div>
            </div>
            <div class="mt-4 flex flex-col sm:flex-row justify-end items-center gap-4">
                <button id="addRequirementRowButton" class="process-button w-full sm:w-auto">
                    <i class="fas fa-plus-circle mr-2"></i> Add New Requirement
                </button>
                <button id="saveDepositRequirementsButton" class="process-button w-full sm:w-auto"
                    style="background-color: #4f46e5;">
                    <i class="fas fa-save mr-2"></i> Save Requirements
                </button>
            </div>
        </div>
    </div>

    <!-- Deposit Counterpart Report Section -->
    <div class="dashboard-card card-span-full mt-8">
        <h3 class="card-title">Deposit Counterpart Report</h3>

        <h4 class="text-xl font-semibold text-gray-700 mb-4">Report Criteria</h4>
        <div class="flex flex-wrap items-end gap-4 pb-4">
            <!-- NEW: Area Dropdown -->
            <div class="input-group">
                <label for="depositReportArea" class="input-label">Area:</label>
                <select id="depositReportArea" class="select-field">
                    <option value="">Select Area</option>
                    <option value="Area 1">Area 1</option>
                    <option value="Area 2">Area 2</option>
                    <option value="Area 3">Area 3</option>
                    <option value="Consolidated">Consolidated</option>
                </select>
            </div>

            <div class="input-group">
                <label for="depositReportBranch" class="input-label">Branch:</label>
                <select id="depositReportBranch" class="select-field" disabled>
                    <option value="">Select Branch</option>
                    <!-- Branches will be populated by JavaScript -->
                </select>
            </div>

            <!-- Date Input (changed from select to text input) -->
            <div class="input-group">
                <label for="depositReportDate" class="input-label">Date (MM/DD/YYYY):</label>
                <input type="text" id="depositReportDate" class="text-input-field" placeholder="MM/DD/YYYY">
            </div>
            
            <div class="input-group">
                <button id="generateDepositReportButton" class="process-button" disabled>
                    Generate Report
                </button>
            </div>
        </div>

        <hr class="my-8 border-gray-200">

        <!-- Combined Actions for Member-Borrowers and Details Reports -->
        <div id="depositReportOverallActions" class="mt-4 flex flex-col sm:flex-row justify-end items-center gap-4 hidden">
            <div class="relative w-full sm:w-1/2 md:w-1/3">
                <input type="text" id="depositReportSearchInput" class="text-input-field pr-10" placeholder="Search all tables...">
                <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
            </div>
            <button id="copyAllDepositTablesButton" class="process-button w-full sm:w-auto" style="background-color: #4f46e5;">
                Copy All Tables
            </button>
            <button id="downloadDepositReportExcelButton" class="process-button w-full sm:w-auto" style="background-color: #10b981;">
                Download as Excel
            </button>
        </div>

        <h4 class="text-lg font-semibold text-gray-700 mb-2 mt-8">Member-Borrowers Report</h4>
        <div class="table-scroll-wrapper">
            <div id="memberBorrowersReportTableContainer" class="mt-4 overflow-x-auto" style="min-height: 200px; background-color: #f0f9ff; border: 2px dashed #93c5fd;">
                <p class="text-gray-500 text-center">Member-Borrower report will appear here after generation.</p>
            </div>
        </div>

        <h4 class="text-lg font-semibold text-gray-700 mb-2 mt-8">Details Report</h4>
        <div class="table-scroll-wrapper">
            <div id="detailsReportTableContainer" class="mt-4 overflow-x-auto" style="min-height: 200px; background-color: #f0f9ff; border: 2px dashed #93c5fd;">
                <p class="text-gray-500 text-center">Details report will appear here after generation.</p>
            </div>
        </div>
    </div>
</div>
<script type="module" src="js/tabs/operations_deposit_counterpart.js" defer></script>
<link rel="stylesheet" href="css/operations_dc.css">
