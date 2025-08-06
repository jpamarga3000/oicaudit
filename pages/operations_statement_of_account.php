<?php
// pages/operations_statement_of_account.php
?>
<div id="operationsStatementOfAccount">
    <div class="dashboard-card card-span-full">
        <h3 class="card-title">Statement Of Account</h3>

        <h4 class="text-xl font-semibold text-gray-700 mb-4">Report Criteria</h4>
        <!-- Changed flex-nowrap to flex-wrap to allow items to move to the next row -->
        <div class="flex flex-wrap items-end gap-4 pb-4">
            <div class="input-group">
                <label for="soaBranch" class="input-label">Branch:</label>
                <select id="soaBranch" class="select-field">
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

            <!-- Removed the Type dropdown -->
            
            <!-- Removed the Category dropdown -->
            <!-- <div class="input-group">
                <label for="soaCategory" class="input-label">Category:</label>
                <select id="soaCategory" class="select-field">
                    <option value="">Select Category</option>
                    <option value="All">All</option>
                    <option value="40-45">40-45</option>
                    <option value="46-49">46-49</option>
                    <option value="50-70">50-70</option>
                    <option value="71">71</option>
                    <option value="72-73">72-73</option>
                    <option value="74-79">74-79</option>
                    <option value=">=80">>=80</option>
                </select>
            </div> -->

            <!-- Changed width to be more flexible, e.g., w-full sm:w-auto or flex-grow -->
            <div class="input-group flex-grow">
                <label for="soaFromDate" class="input-label">From Date (MM/DD/YYYY):</label>
                <input type="tel" id="soaFromDate" class="text-input-field"
                       placeholder="MM/DD/YYYY" maxlength="10">
            </div>
            <!-- Changed width to be more flexible, e.g., w-full sm:w-auto or flex-grow -->
            <div class="input-group flex-grow">
                <label for="soaToDate" class="input-label">To Date (MM/DD/YYYY):</label>
                <input type="tel" id="soaToDate" class="text-input-field"
                       placeholder="MM/DD/YYYY" maxlength="10">
            </div>

            <!-- Changed width to be more flexible, e.g., w-full sm:w-auto or flex-grow -->
            <div class="input-group flex-grow">
                <label for="soaAccount" class="input-label">Account Number:</label>
                <input type="text" id="soaAccount" class="text-input-field"
                       placeholder="e.g., 40-00001-0">
            </div>

            <!-- Changed width to be more flexible, e.g., w-full sm:w-auto or flex-grow -->
            <div class="input-group flex-grow">
                <label for="soaCode" class="input-label">Code (2-digit):</label>
                <input type="text" id="soaCode" class="text-input-field"
                       placeholder="e.g., 11" maxlength="2">
            </div>
        </div>

        <!-- This is the new row for Description, TRN Type, Match Type, and Generate Button -->
        <!-- Changed flex-nowrap to flex-wrap to allow items to move to the next row -->
        <div class="flex flex-wrap items-end gap-4 pb-4 mt-4">
            <div class="input-group flex-grow"> <!-- Description field -->
                <label for="soaDescription" class="input-label">Description (contains):</label>
                <input type="text" id="soaDescription" class="text-input-field"
                       placeholder="e.g., loan payment">
            </div>
            <div class="input-group flex-grow"> <!-- TRN Type field -->
                <label for="soaTrnType" class="input-label">TRN Type (contains):</label>
                <input type="text" id="soaTrnType" class="text-input-field"
                       placeholder="e.g., 21">
            </div>
            <div class="input-group">
                <label for="soaMatchType" class="input-label">Match Type:</label>
                <select id="soaMatchType" class="select-field">
                    <option value="approximate">Approximate</option>
                    <option value="exact">Exact</option>
                </select>
            </div>
            <div class="input-group">
                <button id="processSoaButton" class="process-button" disabled>
                    Generate Report
                </button>
            </div>
        </div>

        <hr class="my-8 border-gray-200">

        <h4 class="text-xl font-semibold text-gray-700 mb-4 mt-8">Generated Report</h4>
        <!-- Adjusted flex classes for single row on all screen sizes -->
        <div id="soaReportActions" class="mt-4 flex justify-end items-center gap-4 hidden">
            <!-- Search input now takes available space, but not full width -->
            <div class="relative flex-grow max-w-xs"> 
                <input type="text" id="soaSearchInput" class="text-input-field pr-10" placeholder="Search table...">
                <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
            </div>
            <!-- Copy button retains auto width -->
            <button id="copySoaTableButton" class="process-button" style="background-color: #4f46e5;">
                Copy Table
            </button>
        </div>
        <div id="soaReportTableContainer" class="mt-4 overflow-x-auto" style="min-height: 200px; background-color: #f0f9ff; border: 2px dashed #93c5fd;">
            <p class="text-gray-500 text-center">Statement of Account report will appear here after generation.</p>
        </div>
    </div>
</div>
<script src="js/tabs/operations_statement_of_account.js" defer></script>
<link rel="stylesheet" href="css/operations_soa.css">
