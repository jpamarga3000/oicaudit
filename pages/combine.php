<?php
// pages/combine.php (Revised for simplified TRNM Combine - Added game canvas and score display, and leaderboard)
// The content below will now be directly included within a <div> in trnm_main.php
?>
<div id="combine">
    <p class="text-lg text-gray-600 text-center mb-10">
        Upload multiple TRNM CSV files for processing and combination.
    </p>

    <div class="space-y-6">
        <div>
            <label for="trnmInputFiles" class="input-label">
                1. Upload TRNM CSV Files (multiple allowed):
            </label>
            <input type="file" id="trnmInputFiles" class="file-input" accept=".csv" multiple>
            <button type="button" class="custom-file-button" onclick="document.getElementById('trnmInputFiles').click()">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                Choose Files
            </button>
            <div id="trnmFilesDisplay" class="file-display mt-2">No files selected.</div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
                <label for="trnmBranch" class="input-label">2. Select Branch:</label>
                <select id="trnmBranch" class="select-field">
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
    </div>

    <div class="mt-8 text-center">
        <button id="processTrnmButton" class="process-button" disabled>
            Process Combine
        </button>
        <!-- Message display area -->
        <div id="trnmCombineMessage" class="mt-4 text-sm font-medium"></div>
    </div>

    <!-- Game Loading Overlay -->
    <div id="trnmGameLoadingOverlay" class="fixed inset-0 bg-gray-900 bg-opacity-90 flex flex-col items-center justify-center z-50 hidden">
        <h3 class="text-white text-3xl font-bold mb-4">Processing Data... Play a game!</h3>
        <div class="relative bg-gray-800 rounded-lg shadow-xl overflow-hidden" style="width: 600px; height: 400px;">
            <canvas id="trnmGameCanvas" width="600" height="400" class="block"></canvas>
            <div id="trnmGameScore" class="absolute top-2 left-2 text-white text-lg font-bold">Score: 0</div>
        </div>
        <p class="text-gray-300 mt-4">Move mouse left/right to catch profile pictures and avoid bombs!</p>
    </div>

    <!-- Leaderboard Display -->
    <div id="leaderboardContainer" class="mt-8 p-4 bg-white shadow-md rounded-lg hidden">
        <h3 class="text-xl font-bold mb-4 text-center">Leaderboard</h3>
        <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Score</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200" id="leaderboardTableBody">
                    <!-- Leaderboard data will be loaded here by JavaScript -->
                </tbody>
            </table>
        </div>
    </div>

<script src="js/tabs/trnm_combine.js" defer></script>
<script src="js/game_logic.js" defer></script> <!-- Load generic game logic -->
</div>
