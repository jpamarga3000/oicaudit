<?php
// pages/audit_tool_tb.php - Revised for Trial Balance File Processing (Upload and Save)
// This content will be included in audit_tool_main_page.php
?>
<div id="auditToolTb">
    <p class="text-lg text-gray-600 text-center mb-10">
        Upload multiple Trial Balance Excel/CSV files for processing and saving into branch-specific folders.
        The branch will be determined from the 'BRANCH' column within your uploaded files.
    </p>

    <div class="space-y-6">
        <div>
            <label for="auditToolTbInputFiles" class="input-label">
                1. Upload Excel/CSV Files (multiple allowed):
            </label>
            <input type="file" id="auditToolTbInputFiles" class="file-input" accept=".csv, .xlsx, .xls" multiple>
            <button type="button" class="custom-file-button" onclick="document.getElementById('auditToolTbInputFiles').click()">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                Choose Files
            </button>
            <div id="auditToolTbFilesDisplay" class="file-display mt-2">No files selected.</div>
        </div>

        <!-- REMOVED: Branch selection dropdown as branch will be derived from uploaded files -->
        <!--
        <div>
            <label for="auditToolTbBranch" class="input-label">
                2. Select Target Branch (for output folder):
            </label>
            <select id="auditToolTbBranch" class="select-field w-auto min-w-[200px]">
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
        -->
    </div>

    <div class="mt-8 text-center">
        <button id="processAuditToolTbButton" class="process-button" disabled>
            Process Trial Balance Files
        </button>
    </div>

    <!-- Message display area -->
    <div id="message-container" class="mt-4"></div>

<script src="js/tabs/audit_tool_tb.js" defer></script>
</div>
