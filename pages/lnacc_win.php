<?php
// pages/lnacc_win.php (Fixed: Removed tab-content class and inline display style, Added message display area)
// The content below will now be directly included within a <div> in lnacc_main.php
?>
<div id="lnaccWin">
    <p class="text-lg text-gray-600 text-center mb-10">
        Upload multiple LNACC WIN CSV files for processing and combination.
    </p>

    <div class="space-y-6">
        <div>
            <label for="lnaccWinInputFiles" class="input-label">
                1. Upload CSV Files (multiple allowed):
            </label>
            <input type="file" id="lnaccWinInputFiles" class="file-input" accept=".csv" multiple>
            <button type="button" class="custom-file-button" onclick="document.getElementById('lnaccWinInputFiles').click()">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                Choose File
            </button>
            <div id="lnaccWinFilesDisplay" class="file-display mt-2">No files selected.</div>
        </div>

        <div>
            <label for="lnaccWinCidRefFiles" class="input-label">
                2. Upload CID Reference CSV File (Optional, single file):
            </label>
            <input type="file" id="lnaccWinCidRefFiles" class="file-input" accept=".csv">
            <button type="button" class="custom-file-button" onclick="document.getElementById('lnaccWinCidRefFiles').click()">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 0 003 3h10a3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                Choose File
            </button>
            <div id="lnaccWinCidRefFilesDisplay" class="file-display mt-2">No file selected.</div>
            <p class="text-sm text-gray-500 mt-1">
                This file should contain 'ACC', 'Chd', 'CID', and 'Type' headers. 'Type' value must be '10'.
            </p>
        </div>

        <div>
            <label for="lnaccWinBranch" class="input-label">
                3. Select Branch:
            </label>
            <select id="lnaccWinBranch" class="select-field w-auto min-w-[200px]">
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
    </div>

    <div class="mt-8 text-center">
        <button id="processLnaccWinButton" class="process-button" disabled>
            Process LNACC WIN Files
        </button>
        <!-- Message display area -->
        <div id="lnaccWinMessage" class="mt-4 text-sm font-medium"></div>
    </div>

<script src="js/tabs/lnacc_win.js" defer></script>
</div>
