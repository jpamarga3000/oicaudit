<?php
// pages/journal_voucher.php
?>
<div id="journalVoucher">
    <p class="text-lg text-gray-600 text-center mb-10">
        Upload Journal Voucher DBF files for cleaning, conversion, and specific header mapping.
    </p>

    <div class="space-y-6">
        <div>
            <label for="journalVoucherBranch" class="input-label">
                1. Select Branch:
            </label>
            <select id="journalVoucherBranch" class="select-field w-auto min-w-[200px]">
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

        <div>
            <label for="journalVoucherInputFiles" class="input-label">
                2. Upload DBF Files (multiple allowed):
            </label>
            <input type="file" id="journalVoucherInputFiles" class="file-input" accept=".dbf" multiple>
            <button type="button" class="custom-file-button" onclick="document.getElementById('journalVoucherInputFiles').click()">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                Choose Files
            </button>
            <div id="journalVoucherFilesDisplay" class="file-display mt-2">No files selected.</div>
        </div>

        <div>
            <label for="journalVoucherOutputFolder" class="input-label">
                3. Enter Output Folder Path (to save converted CSV):
            </label>
            <input type="text" id="journalVoucherOutputFolder" class="text-input-field"
                   placeholder="e.g., C:\Users\YourName\Documents\ProcessedJournalVouchers">
            <p class="text-sm text-gray-500 mt-1">
                The folder will be created if it doesn't exist.
            </p>
        </div>
    </div>

    <div class="mt-8 text-center">
        <button id="processJournalVoucherButton" class="process-button" disabled>
            Process Journal Voucher
        </button>
    </div>

    <hr class="my-8 border-gray-200">

    <h4 class="text-xl font-semibold text-gray-700 mb-4 mt-8">Generated Report</h4>
    <div id="journalVoucherReportActions" class="mt-4 flex flex-col sm:flex-row justify-end items-center gap-4 hidden">
        <div class="relative w-full sm:w-1/2 md:w-1/3">
            <input type="text" id="journalVoucherSearchInput" class="text-input-field pr-10" placeholder="Search table...">
            <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
        </div>
        <button id="copyJournalVoucherTableButton" class="process-button w-full sm:w-auto" style="background-color: #4f46e5;">
            Copy Table
        </button>
    </div>
    <div id="journalVoucherReportTableContainer" class="mt-4 overflow-x-auto" style="min-height: 200px; background-color: #f0f9ff; border: 2px dashed #93c5fd;">
        <p class="text-gray-500 text-center">Journal Voucher report will appear here after generation.</p>
    </div>

<script src="js/tabs/journal_voucher.js" defer></script>
</div>
