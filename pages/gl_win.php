<?php
// pages/gl_win.php (Fixed: Removed tab-content class)
// The content below will now be directly included within a <div> in gl_main.php
?>
<div id="glWin"> <p class="text-lg text-gray-600 text-center mb-10">
        1. Upload multiple GL WIN CSV files for processing and categorization.
    </p>

    <p class="text-xl font-bold text-blue-600 text-center" style="background-color: lightblue;">
        GL WIN CONTENT IS HERE!
    </p>
    <div class="space-y-6">
        <div>
            <label for="glWinInputFiles" class="input-label">
                1. Upload CSV Files (multiple allowed):
            </label>
            <input type="file" id="glWinInputFiles" class="file-input" accept=".csv" multiple>
            <button type="button" class="custom-file-button" onclick="document.getElementById('glWinInputFiles').click()">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                Choose Files
            </button>
            <div id="glWinFilesDisplay" class="file-display mt-2">No files selected.</div>
        </div>

        <div>
            <label for="glWinBranch" class="input-label">
                2. Select Branch (for output folder and filename):
            </label>
            <select id="glWinBranch" class="select-field w-auto min-w-[200px]">
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

        <!-- Output Folder Path field removed as it's now fixed and not user-editable -->
        <!-- <div>
            <label for="glWinOutputFolder" class="input-label">
                3. Enter Output Folder Path (to save processed CSVs):
            </label>
            <input type="text" id="glWinOutputFolder" class="text-input-field"
                   placeholder="e.g., C:\Users\YourName\Documents\ProcessedGLWIN">
            <p class="text-sm text-gray-500 mt-1">
                The folder will be created if it doesn't exist.
            </p>
        </div> -->
    </div>

    <div class="mt-8 text-center">
        <button id="processGlWinButton" class="process-button" disabled>
            Process GL WIN Files
        </button>
    </div>

<script src="js/tabs/gl_win.js" defer></script>
</div>
