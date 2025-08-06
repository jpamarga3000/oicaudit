<?php
// pages/actg_trend.php (New implementation for Trend Report with Canvas for Chart.js)
?>
<div id="actgTrend">
    <div class="dashboard-card card-span-full">
        <h3 class="card-title">Trend Report</h3>

        <h4 class="text-xl font-semibold text-gray-700 mb-4">Report Criteria</h4>
        <div class="flex flex-wrap items-end gap-4 pb-4">
            <div class="input-group">
                <label for="trendBranch" class="input-label">Branch:</label>
                <select id="trendBranch" class="select-field">
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
                <label for="trendFromDate" class="input-label">From Date (MM/DD/YYYY):</label>
                <input type="tel" id="trendFromDate" class="text-input-field"
                       placeholder="MM/DD/YYYY" maxlength="10">
            </div>
            <div class="input-group">
                <label for="trendToDate" class="input-label">To Date (MM/DD/YYYY):</label>
                <input type="tel" id="trendToDate" class="text-input-field"
                       placeholder="MM/DD/YYYY" maxlength="10">
            </div>

            <div class="input-group">
                <label for="trendGlName" class="input-label">GL Name:</label>
                <input type="text" id="trendGlName" class="text-input-field"
                       placeholder="e.g., Cash in Bank" list="trendGlNamesDatalist">
                <datalist id="trendGlNamesDatalist"></datalist>
            </div>
            <div class="input-group">
                <label for="trendGlCode" class="input-label">GL Code:</label>
                <input type="text" id="trendGlCode" class="text-input-field"
                       placeholder="e.g., 10000">
            </div>
            <div class="input-group">
                <label for="trendFrequency" class="input-label">Frequency:</label>
                <select id="trendFrequency" class="select-field">
                    <option value="">Select Frequency</option>
                    <option value="daily">Daily</option>
                    <option value="monthly">Monthly</option>
                    <option value="semi-annually">Semi-Annually</option>
                    <option value="annually">Annually</option>
                </select>
            </div>
            <div class="input-group">
                <label for="trendChartDisplayBy" class="input-label">Display Chart By:</label>
                <select id="trendChartDisplayBy" class="select-field">
                    <option value="BALANCE">Balance</option>
                    <option value="CHANGE">Change</option>
                </select>
            </div>
            <div class="input-group">
                <button id="processTrendButton" class="process-button" disabled>
                    Generate Report
                </button>
            </div>
        </div>

        <hr class="my-8 border-gray-200">

        <h4 class="text-xl font-semibold text-gray-700 mb-4 mt-8">Generated Report</h4>
        <div id="trendReportActions" class="mt-4 flex flex-col sm:flex-row justify-end items-center gap-4 hidden">
            <div class="relative w-full sm:w-1/2 md:w-1/3">
                <input type="text" id="trendSearchInput" class="text-input-field pr-10" placeholder="Search table...">
                <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
            </div>
            <button id="copyTrendTableButton" class="process-button w-full sm:w-auto" style="background-color: #4f46e5;">
                Copy Table
            </button>
        </div>

        <div id="trendChartContainer" class="mt-4 p-4 bg-gray-50 rounded-lg shadow-inner" style="min-height: 800px; display: flex; align-items: center; justify-content: center; color: #6b7280;">
            <canvas id="trendChart"></canvas> <p id="chartPlaceholderText">Chart will appear here (requires a charting library).</p> </div>

        <div id="trendReportTableContainer" class="mt-4 overflow-x-auto" style="min-height: 200px; background-color: #f0f9ff; border: 2px dashed #93c5fd;">
            <p class="text-gray-500 text-center">Report table will appear here after generation.</p>
        </div>
    </div>
<script src="js/tabs/actg_trend.js" defer></script>
</div>