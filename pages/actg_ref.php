<?php
// pages/actg_ref.php (Full implementation for Reference Report)
?>
<div id="actgRef">
    <div class="dashboard-grid">
        <div class="dashboard-card card-span-full">
            <h3 class="card-title">Reference Report Criteria</h3>
            <div class="flex flex-wrap items-end gap-4 pb-4">
                <div class="input-group">
                    <label for="actgRefBranch" class="input-label">Branch:</label>
                    <select id="actgRefBranch" class="select-field">
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

                <div class="input-group">
                    <label for="actgRefFromDate" class="input-label">From Date (MM/DD/YYYY):</label>
                    <input type="tel" id="actgRefFromDate" class="text-input-field"
                           placeholder="MM/DD/YYYY" maxlength="10">
                </div>
                <div class="input-group">
                    <label for="actgRefToDate" class="input-label">To Date (MM/DD/YYYY):</label>
                    <input type="tel" id="actgRefToDate" class="text-input-field"
                           placeholder="MM/DD/YYYY" maxlength="10">
                </div>

                <div class="input-group">
                    <label for="actgRefInput" class="input-label">Reference:</label>
                    <input type="text" id="actgRefInput" class="text-input-field"
                           placeholder="e.g., CV123">
                </div>
                <div class="input-group">
                    <label for="actgRefMatchType" class="input-label">Match:</label>
                    <select id="actgRefMatchType" class="select-field">
                        <option value="exact">Exact</option>
                        <option value="approximate">Approximate</option>
                    </select>
                </div>
                <div class="input-group">
                    <button id="processActgRefButton" class="process-button" disabled>
                        Generate Report
                    </button>
                </div>
            </div>

            <div id="actgRefReportActions" class="mt-4 flex flex-col sm:flex-row justify-end items-center gap-4 hidden">
                <div class="relative w-full sm:w-1/2 md:w-1/3">
                    <input type="text" id="actgRefSearchInput" class="text-input-field pr-10" placeholder="Search table...">
                    <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                </div>
                <button id="copyActgRefTableButton" class="process-button w-full sm:w-auto" style="background-color: #4f46e5;">
                    Copy Table
                </button>
            </div>
            <div id="actgRefReportContainer" class="mt-4 overflow-x-auto">
                <p class="text-gray-500 text-center">Reference report will appear here after generation.</p>
            </div>
        </div>
    </div>
<script src="js/tabs/actg_ref.js" defer></script>
</div>