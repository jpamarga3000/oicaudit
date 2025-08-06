// js/tabs/trnm_combine.js

// Ensure window.registerTabInitializer is available from main.js
if (window.registerTabInitializer) {
    (function() { // Start IIFE
        // Local array to store selected files for this tab, declared inside the IIFE
        let combineSelectedFiles = [];

        // Define the fixed base output directory (no longer used by game, but by backend)
        const FIXED_BASE_OUTPUT_DIR = "C:/xampp/htdocs/audit_tool/OPERATIONS/TRNM";

        // References to UI elements specific to trnm_combine.js
        let trnmCombineMessageDiv;
        // Game-related elements are now managed by game_logic.js directly via IDs

        /**
         * Displays a message in the trnmCombineMessageDiv.
         * @param {string} message - The message to display.
         * @param {string} type - The type of message ('success', 'error', 'loading', 'info').
         */
        function displayTrnmCombineMessage(message, type) {
            if (!trnmCombineMessageDiv) {
                trnmCombineMessageDiv = document.getElementById('trnmCombineMessage');
            }
            if (trnmCombineMessageDiv) {
                trnmCombineMessageDiv.textContent = message;
                // Clear previous classes
                trnmCombineMessageDiv.className = 'mt-4 text-sm font-medium';
                // Add new classes based on type
                if (type === 'success') {
                    trnmCombineMessageDiv.classList.add('text-green-600');
                } else if (type === 'error') {
                    trnmCombineMessageDiv.classList.add('text-red-600');
                } else if (type === 'loading') {
                    trnmCombineMessageDiv.classList.add('text-blue-600');
                } else if (type === 'info') {
                    trnmCombineMessageDiv.classList.add('text-gray-600');
                }
            }
        }

        /**
         * Removes a file from the combineSelectedFiles array and updates the UI.
         * This function needs to be accessible to renderSelectedFiles.
         * @param {number} indexToRemove - The index of the file to remove.
         */
        function removeCombineFile(indexToRemove) {
            combineSelectedFiles.splice(indexToRemove, 1);
            // Call renderSelectedFiles with the local remove function
            window.renderSelectedFiles(combineSelectedFiles, 'trnmFilesDisplay', removeCombineFile);
            updateTrnmCombineUI();
        }

        /**
         * Updates the state of the "Process Combine" button.
         */
        function updateTrnmCombineUI() {
            const combineBranchInput = document.getElementById('trnmBranch');
            const processCombineButton = document.getElementById('processTrnmButton');

            // Button is enabled if files are selected AND a branch is chosen
            const isCombineInputsValid = combineSelectedFiles.length > 0 &&
                                         combineBranchInput && combineBranchInput.value.trim();

            if (processCombineButton) {
                processCombineButton.disabled = !isCombineInputsValid;
            }
        }

        /**
         * Handles the processing request for TRNM Combine data.
         */
        async function processTrnmCombine() {
            const branch = document.getElementById('trnmBranch').value.trim();

            if (combineSelectedFiles.length === 0) {
                displayTrnmCombineMessage('Please select TRNM CSV files to process.', 'error');
                return;
            }
            if (!branch) {
                displayTrnmCombineMessage('Please select a branch.', 'error');
                return;
            }

            const processCombineButton = document.getElementById('processTrnmButton');
            if (processCombineButton) {
                processCombineButton.disabled = true;
            }
            displayTrnmCombineMessage('Processing files... Play the game!', 'loading');

            // Start the game using the generic gameLogic
            if (window.gameLogic && typeof window.gameLogic.startGame === 'function') {
                window.gameLogic.startGame('trnmGameCanvas', 'trnmGameScore', 'trnmGameLoadingOverlay');
            } else {
                console.error("Game logic not loaded or startGame function not found.");
            }

            const formData = new FormData();
            combineSelectedFiles.forEach(file => {
                formData.append('files', file);
            });
            formData.append('branch', branch);

            try {
                const response = await fetch(`${FLASK_API_BASE_URL}/process_trnm`, {
                    method: 'POST',
                    body: formData,
                });

                const result = await response.json();

                if (response.ok) {
                    displayTrnmCombineMessage(result.message, 'success');
                    // Optionally clear file input and reset display after successful processing
                    document.getElementById('trnmInputFiles').value = '';
                    document.getElementById('trnmFilesDisplay').textContent = 'No files selected.';
                    document.getElementById('trnmBranch').value = ''; // Reset branch selection
                    combineSelectedFiles = []; // Clear the selected files array
                } else {
                    displayTrnmCombineMessage(`Error: ${result.message}`, 'error');
                }
            } catch (error) {
                console.error('Fetch error:', error);
                displayTrnmCombineMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
            } finally {
                if (processCombineButton) {
                    processCombineButton.disabled = false;
                }
                updateTrnmCombineUI(); // Re-evaluate button state after processing
                
                // Stop the game and submit score/display leaderboard using the generic gameLogic
                if (window.gameLogic && typeof window.gameLogic.stopGame === 'function') {
                    window.gameLogic.stopGame();
                    // Submit the score from the game instance
                    console.log("TRNM Combine: Game stopped. Attempting to submit score and fetch leaderboard."); // Debug log
                    await window.gameLogic.submitAndFetchLeaderboard(window.gameLogic.score); 
                }
            }
        }

        /**
         * Event handler for the trnmInputFiles input change.
         * @param {Event} event - The change event.
         */
        function handleCombineFileInputChange(event) {
            Array.from(event.target.files).forEach(file => {
                // Ensure only unique files (by name) are added
                if (!combineSelectedFiles.some(existingFile => existingFile.name === file.name)) {
                    combineSelectedFiles.push(file);
                }
            });
            event.target.value = ''; // Clear the input to allow re-selection of same file(s)
            // Call renderSelectedFiles with the local remove function
            window.renderSelectedFiles(combineSelectedFiles, 'trnmFilesDisplay', removeCombineFile);
            updateTrnmCombineUI();
        }

        /**
         * Initializes the TRNM Combine sub-tab: attaches event listeners and performs initial UI update.
         * This function is called by main.js when the sub-tab is activated.
         */
        async function initTrnmCombineTab() { // Made async to await image loading
            console.log('Initializing TRNM Combine Tab...');

            trnmCombineMessageDiv = document.getElementById('trnmCombineMessage');
            // Game elements are now initialized and managed by game_logic.js directly

            const combineInputFilesInput = document.getElementById('trnmInputFiles');
            const combineBranchInput = document.getElementById('trnmBranch');
            const processCombineButton = document.getElementById('processTrnmButton');
            
            // Attach event listeners
            if (combineInputFilesInput && !combineInputFilesInput.dataset.listenerAttached) {
                combineInputFilesInput.addEventListener('change', handleCombineFileInputChange);
                combineInputFilesInput.dataset.listenerAttached = 'true';
            }
            if (combineBranchInput && !combineBranchInput.dataset.listenerAttached) {
                combineBranchInput.addEventListener('change', updateTrnmCombineUI);
                combineBranchInput.dataset.listenerAttached = 'true';
            }
            if (processCombineButton && !processCombineButton.dataset.listenerAttached) {
                processCombineButton.addEventListener('click', processTrnmCombine);
                processCombineButton.dataset.listenerAttached = 'true';
            }

            // Initial render and UI update
            // Call renderSelectedFiles with the local remove function during initialization
            window.renderSelectedFiles(combineSelectedFiles, 'trnmFilesDisplay', removeCombineFile);
            updateTrnmCombineUI();
            // Clear any previous messages when the tab is initialized
            displayTrnmCombineMessage('', 'info');

            // Hide leaderboard initially for this tab, it will be shown after game ends
            const leaderboardContainer = document.getElementById('leaderboardContainer');
            if (leaderboardContainer) {
                leaderboardContainer.classList.add('hidden');
            }
        }

        // Register this sub-tab's initializer with the main application logic
        window.registerTabInitializer('combine', initTrnmCombineTab);

    })(); // End IIFE
} else {
    console.error("trnm_combine.js: window.registerTabInitializer is not defined. Ensure main.js is loaded first.");
}
