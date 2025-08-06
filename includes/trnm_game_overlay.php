<?php
// audit_tool/includes/trnm_game_overlay.php
// This file contains the HTML structure for the TRNM combine loading game overlay.
?>
<!-- Game Loading Overlay -->
<div id="trnmGameLoadingOverlay" class="fixed inset-0 bg-gray-900 bg-opacity-90 flex flex-col items-center justify-center z-50 hidden">
    <h3 class="text-white text-3xl font-bold mb-4">Processing Data... Play a game!</h3>
    <div class="relative bg-gray-800 rounded-lg shadow-xl overflow-hidden" style="width: 600px; height: 400px;">
        <canvas id="trnmGameCanvas" width="600" height="400" class="block"></canvas>
        <div id="trnmGameScore" class="absolute top-2 left-2 text-white text-lg font-bold">Score: 0</div>
        <!-- Leaderboard Container (Initially Hidden) -->
        <div id="trnmLeaderboard" class="absolute inset-0 bg-gray-800 bg-opacity-95 flex flex-col items-center justify-center p-4 rounded-lg hidden">
            <h4 class="text-white text-2xl font-bold mb-4">Leaderboard</h4>
            <div class="w-full max-w-xs bg-white rounded-lg shadow overflow-hidden">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Name
                            </th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Score
                            </th>
                        </tr>
                    </thead>
                    <tbody id="leaderboardTableBody" class="bg-white divide-y divide-gray-200">
                        <!-- Leaderboard items will be inserted here by JavaScript -->
                    </tbody>
                </table>
            </div>
            <button id="closeLeaderboardBtn" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">Close Leaderboard</button>
        </div>
    </div>
    <p class="text-gray-300 mt-4">Move mouse left/right to catch profile pictures and avoid bombs!</p>
</div>
