<?php
// pages/actg_tb.php
?>
<div id="actgTb">
    <div class="dashboard-grid">
        <div class="dashboard-card card-span-full">
            <h3 class="card-title">Trial Balance Report</h3>
            <div class="flex flex-wrap items-end gap-4 pb-4"> <div class="input-group">
                    <label for="actgTbBranch" class="input-label">Branch:</label>
                    <select id="actgTbBranch" class="select-field">
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
                    <label for="actgTbAsOfDate" class="input-label">As Of Date:</label>
                    <select id="actgTbAsOfDate" class="select-field" disabled>
                        <option value="">Select Date</option>
                    </select>
                </div>
                <div class="input-group"> <button id="processActgTbButton" class="process-button" disabled>
                        Generate Report
                    </button>
                </div>
            </div>

            <div id="actgTbReportActions" class="mt-4 flex flex-col sm:flex-row justify-end items-center gap-4 hidden"> <div class="relative w-full sm:w-1/2 md:w-1/3">
                    <input type="text" id="actgTbSearchInput" class="text-input-field pr-10" placeholder="Search table...">
                    <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                </div>
                <button id="copyActgTbTableButton" class="process-button w-full sm:w-auto" style="background-color: #4f46e5;">
                    Copy Table
                </button>
            </div>
            <div id="actgTbReportContainer" class="mt-4 overflow-x-auto">
                <p class="text-gray-500 text-center">Trial Balance report will appear here after generation.</p>
            </div>
        </div>
    </div>
<script src="js/tabs/actg_tb.js" defer></script>
</div>