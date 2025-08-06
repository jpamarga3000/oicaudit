// js/tabs/trnm_win.js

(function() { // Start IIFE
    // Local array to store selected files for this tab, declared inside the IIFE
    let winSelectedFiles = [];

    // Define the fixed base output directory
    const FIXED_BASE_OUTPUT_DIR = "C:\\xampp\\htdocs\\audit_tool\\OPERATIONS\\TRNM";

    /**
     * Removes a file from the winSelectedFiles array and updates the UI.
     * @param {number} indexToRemove - The index of the file to remove.
     */
    function removeWinFile(indexToRemove) {
        winSelectedFiles.splice(indexToRemove, 1);
        renderSelectedFiles(winSelectedFiles, 'winFilesDisplay', removeWinFile);
        updateTrnmWinUI();
        console.log('DEBUG: File removed. Current winSelectedFiles:', winSelectedFiles);
    }

    /**
     * Updates the state of the "Process WIN Files" button based on input validity.
     */
    function updateTrnmWinUI() {
        const processWinButton = document.getElementById('processWinButton');
        const winBranchInput = document.getElementById('winBranch'); // Get the branch input

        // Button is enabled if files are selected AND a branch is chosen
        if (processWinButton && winBranchInput) {
            processWinButton.disabled = !(winSelectedFiles.length > 0 && winBranchInput.value.trim());
            console.log('DEBUG: updateTrnmWinUI - Button disabled status:', processWinButton.disabled);
        }
    }

    /**
     * Handles the processing request for WIN data.
     */
    async function processTrnmWin() {
        console.log('DEBUG: processTrnmWin function started.'); // New log to confirm function execution

        const branch = document.getElementById('winBranch').value.trim(); // Get the branch value

        if (winSelectedFiles.length === 0) {
            showMessage('Please select CSV files to process.', 'error');
            console.log('DEBUG: No files selected. Aborting processTrnmWin.');
            return;
        }
        if (!branch) {
            showMessage('Please select a branch.', 'error');
            console.log('DEBUG: No branch selected. Aborting processTrnmWin.');
            return;
        }

        const processWinButton = document.getElementById('processWinButton');
        if (processWinButton) {
            processWinButton.disabled = true;
        }
        showMessage('Processing files... This may take a moment.', 'loading');
        console.log('DEBUG: UI updated to loading state.');

        const formData = new FormData();
        winSelectedFiles.forEach(file => {
            formData.append('files', file);
        });
        formData.append('branch', branch); // Append the branch to form data
        console.log('DEBUG: FormData prepared with files and branch:', { filesCount: winSelectedFiles.length, branch: branch });

        try {
            console.log('DEBUG: Initiating fetch request to /process_win.'); // New log before fetch
            const response = await fetch(`${FLASK_API_BASE_URL}/process_win`, {
                method: 'POST',
                body: formData,
            });
            console.log('DEBUG: Fetch request completed. Response status:', response.status);

            const result = await response.json();
            console.log('DEBUG: Response JSON parsed:', result);

            if (response.ok) {
                showMessage(result.message, 'success', result.output_path);
                // Optionally clear file input and reset display after successful processing
                document.getElementById('winInputFiles').value = '';
                document.getElementById('winFilesDisplay').textContent = 'No files selected.';
                document.getElementById('winBranch').value = ''; // Reset branch selection
                winSelectedFiles = []; // Clear the internal array
                console.log('DEBUG: Processing successful. UI reset.');
            } else {
                showMessage(result.error || 'An unknown error occurred.', 'error');
                console.error('DEBUG: Processing failed. Server response:', result);
            }
        } catch (error) {
            console.error('Fetch error:', error);
            showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
        } finally {
            if (processWinButton) {
                processWinButton.disabled = false;
            }
            updateTrnmWinUI(); // Re-evaluate button state after processing
            console.log('DEBUG: Finally block executed. Button re-enabled.');
        }
    }

    /**
     * Event handler for the winInputFiles input change.
     * @param {Event} event - The change event.
     */
    function handleWinFileInputChange(event) {
        console.log('DEBUG: handleWinFileInputChange triggered.');
        Array.from(event.target.files).forEach(file => {
            if (!winSelectedFiles.some(existingFile => existingFile.name === file.name)) {
                winSelectedFiles.push(file);
                console.log('DEBUG: Added file:', file.name);
            } else {
                console.log('DEBUG: File already exists, skipping:', file.name);
            }
        });
        event.target.value = ''; // Clear the input to allow re-selection of same file(s)
        console.log('DEBUG: Current winSelectedFiles after change:', winSelectedFiles);
        renderSelectedFiles(winSelectedFiles, 'winFilesDisplay', removeWinFile);
        updateTrnmWinUI();
    }

    /**
     * Initializes the TRNM WIN sub-tab: attaches event listeners and performs initial UI update.
     * This function is called by main.js when the sub-tab is activated.
     */
    function initTrnmWinTab() {
        console.log('Initializing TRNM WIN Tab...');

        const winInputFilesInput = document.getElementById('winInputFiles');
        const winBranchInput = document.getElementById('winBranch'); // Get the branch input
        const processWinButton = document.getElementById('processWinButton');

        // Attach event listeners
        if (winInputFilesInput && !winInputFilesInput.dataset.listenerAttached) {
            winInputFilesInput.addEventListener('change', handleWinFileInputChange);
            winInputFilesInput.dataset.listenerAttached = 'true';
            console.log('DEBUG: Change listener attached to winInputFilesInput.');
        }
        // Attach listener for branch input
        if (winBranchInput && !winBranchInput.dataset.listenerAttached) {
            winBranchInput.addEventListener('change', updateTrnmWinUI);
            winBranchInput.dataset.listenerAttached = 'true';
            console.log('DEBUG: Change listener attached to winBranchInput.');
        }
        if (processWinButton && !processWinButton.dataset.listenerAttached) {
            processWinButton.addEventListener('click', processTrnmWin);
            processWinButton.dataset.listenerAttached = 'true';
            console.log('DEBUG: Click listener attached to processWinButton.');
        }

        // Initial render and UI update
        renderSelectedFiles(winSelectedFiles, 'winFilesDisplay', removeWinFile);
        updateTrnmWinUI();
        console.log('DEBUG: Initial render and UI update complete for TRNM WIN tab.');
    }

    // Register this sub-tab's initializer with the main application logic
    registerTabInitializer('win', initTrnmWinTab);

})(); // End IIFE
