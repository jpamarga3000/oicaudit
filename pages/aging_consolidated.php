<?php
// aging_consolidated.php (Fixed: Removed tab-content class and inline display style)
// The content below will now be directly included within a <section> in audit_tool_main_page.php
?>
    <p class="text-lg text-gray-600 text-center mb-10">
        Upload multiple Excel files and manually enter the output folder path for Aging Consolidated data.
    </p>

    <div class="space-y-6">
        <div>
            <label for="agingInputFiles" class="input-label">
                1. Upload Excel Files (multiple allowed):
            </label>
            <input type="file" id="agingInputFiles" class="file-input" accept=".xls,.xlsx" multiple>
            <button type="button" class="custom-file-button" onclick="document.getElementById('agingInputFiles').click()">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                Choose Files
            </button>
            <div id="agingFilesDisplay" class="file-display mt-2">No files selected.</div>
        </div>

        <div>
            <label for="agingOutputFolder" class="input-label">
                2. Enter Output Folder Path (to save CSVs):
            </label>
            <input type="text" id="agingOutputFolder" class="text-input-field"
                   placeholder="e.g., C:\Users\YourName\Documents\ProcessedAgingCSVs">
            <p class="text-sm text-gray-500 mt-1">
                The folder will be created if it doesn't exist.
            </p>
        </div>
    </div>

    <div class="mt-8 text-center">
        <button id="processAgingButton" class="process-button" disabled>
            Process Aging Consolidated
        </button>
    </div>

<script src="js/tabs/aging_consolidated.js" defer></script>
