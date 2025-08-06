<?php
// pages/svacc_win.php (Modified: Removed output folder path input)
// The content below will now be directly included within a <div> in svacc_main.php
?>
<div id="svaccWin">
    <p class="text-lg text-gray-600 text-center mb-10">
        Upload SVACC CSV files for processing and combination, with an optional LNHIST CID reference file.
    </p>

    <div class="space-y-6">
        <div>
            <label for="svaccWinInputFiles" class="input-label">
                1. Upload SVACC CSV Files (multiple allowed):
            </label>
            <input type="file" id="svaccWinInputFiles" class="file-input" accept=".csv" multiple>
            <button type="button" class="custom-file-button" onclick="document.getElementById('svaccWinInputFiles').click()">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                Choose Files
            </button>
            <div id="svaccWinFilesDisplay" class="file-display mt-2">No files selected.</div>
        </div>

        <div>
            <label for="svaccWinLnhistFiles" class="input-label">
                2. Upload LNHIST CID Reference CSV File (Optional, single file):
            </label>
            <input type="file" id="svaccWinLnhistFiles" class="file-input" accept=".csv">
            <button type="button" class="custom-file-button" onclick="document.getElementById('svaccWinLnhistFiles').click()">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                Choose File
            </button>
            <div id="svaccWinLnhistFilesDisplay" class="file-display mt-2">No file selected.</div>
            <p class="text-sm text-gray-500 mt-1">
                This file should contain 'ACC', 'Chd', 'CID', and 'Type' headers. 'Type' value must be '10'.
            </p>
        </div>

        <div>
            <label for="svaccWinBranch" class="input-label">
                3. Select Branch:
            </label>
            <select id="svaccWinBranch" class="select-field w-auto min-w-[200px]">
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
        <!-- Removed: Output Folder Path Input Field -->
    </div>

    <div class="mt-8 text-center">
        <button id="processSvaccWinButton" class="process-button" disabled>
            Process SVACC WIN Files
        </button>
    </div>

<script src="js/tabs/svacc_win.js" defer></script>
</div>
