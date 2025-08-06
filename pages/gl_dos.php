<?php
// pages/gl_dos.php (Fixed: Removed tab-content class and inline display style)
// The content below will now be directly included within a <div> in gl_main.php
?>
<div id="glDos">
    <p class="text-lg text-gray-600 text-center mb-10">
        Upload multiple GL DOS DBF files for processing and combination into a single CSV.
    </p>

    <div class="space-y-6">
        <div>
            <label for="glDosInputFiles" class="input-label">
                1. Upload DBF Files (multiple allowed):
            </label>
            <input type="file" id="glDosInputFiles" class="file-input" accept=".dbf" multiple>
            <button type="button" class="custom-file-button" onclick="document.getElementById('glDosInputFiles').click()">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                Choose Files
            </button>
            <div id="glDosFilesDisplay" class="file-display mt-2">No files selected.</div>
        </div>

        <div>
            <label for="glDosBranch" class="input-label">
                2. Select Branch (for output folder and filename):
            </label>
            <select id="glDosBranch" class="select-field w-auto min-w-[200px]">
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
            <label for="glDosOutputFolder" class="input-label">
                3. Enter Output Folder Path (to save combined CSV):
            </label>
            <input type="text" id="glDosOutputFolder" class="text-input-field"
                   placeholder="e.g., C:\Users\YourName\Documents\ProcessedGLDOS">
            <p class="text-sm text-gray-500 mt-1">
                The folder will be created if it doesn't exist.
            </p>
        </div> -->
    </div>

    <div class="mt-8 text-center">
        <button id="processGlDosButton" class="process-button" disabled>
            Process GL DOS Files
        </button>
    </div>

<script src="js/tabs/gl_dos.js" defer></script>
</div>
