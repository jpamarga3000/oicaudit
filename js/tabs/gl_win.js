// js/tabs/gl_win.js

(function() { // Start IIFE
    // Local array to store selected files for this tab, declared inside the IIFE
    let glWinSelectedFiles = [];

    // Fixed output directory path (matches the backend)
    const FIXED_BASE_OUTPUT_DIR = "C:\\xampp\\htdocs\\audit_tool\\ACCOUTNING\\GENERAL LEDGER";

    /**
     * Removes a file from the glWinSelectedFiles array and updates the UI.
     * @param {number} indexToRemove - The index of the file to remove.
     */
    function removeGlWinFile(indexToRemove) {
        glWinSelectedFiles.splice(indexToRemove, 1);
        renderSelectedFiles(glWinSelectedFiles, 'glWinFilesDisplay', removeGlWinFile);
        updateGlWinUI();
    }

    /**
     * Updates the state of the "Process GL WIN Files" button based on input validity.
     */
    function updateGlWinUI() {
        const processGlWinButton = document.getElementById('processGlWinButton');
        const glWinBranchInput = document.getElementById('glWinBranch');

        // Button is enabled if files are selected AND a branch is chosen
        if (processGlWinButton && glWinBranchInput) {
            processGlWinButton.disabled = !(glWinSelectedFiles.length > 0 && glWinBranchInput.value.trim());
        }
    }

    /**
     * Handles the processing request for GL WIN data.
     */
    async function processGlWin() {
        const glWinBranchInput = document.getElementById('glWinBranch');
        const processGlWinButton = document.getElementById('processGlWinButton');

        const branchValue = glWinBranchInput ? glWinBranchInput.value.trim().toUpperCase() : '';

        if (glWinSelectedFiles.length === 0) {
            showMessage('Please select CSV files to process.', 'error');
            return;
        }
        if (!branchValue) {
            showMessage('Please select a branch.', 'error');
            return;
        }

        if (processGlWinButton) {
            processGlWinButton.disabled = true;
        }
        showMessage('Processing files... This may take a moment.', 'loading');

        const formData = new FormData();
        glWinSelectedFiles.forEach(file => {
            formData.append('files', file);
        });
        formData.append('branch', branchValue);
        // output_dir is now fixed in the backend and derived from branch

        try {
            const response = await fetch(`${FLASK_API_BASE_URL}/process_gl_win`, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                // The backend now returns the actual output path, so we can display it
                showMessage(result.message, 'success', result.output_path);
            } else {
                showMessage(`Error: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('Fetch error:', error);
            showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
        } finally {
            if (processGlWinButton) {
                processGlWinButton.disabled = false;
            }
        }
    }

    /**
     * Event handler for the glWinInputFiles input change.
     * @param {Event} event - The change event.
     */
    function handleGlWinFileInputChange(event) {
        Array.from(event.target.files).forEach(file => {
            if (!glWinSelectedFiles.some(existingFile => existingFile.name === file.name)) {
                glWinSelectedFiles.push(file);
            }
        });
        event.target.value = ''; // Clear the file input to allow selecting same files again
        renderSelectedFiles(glWinSelectedFiles, 'glWinFilesDisplay', removeGlWinFile);
        updateGlWinUI();
    }

    /**
     * Initializes the GL WIN sub-tab: attaches event listeners and performs initial UI update.
     * This function is called by main.js when the sub-tab is activated.
     */
    function initGlWinTab() {
        console.log('Initializing GL WIN Tab...');

        const glWinInputFilesInput = document.getElementById('glWinInputFiles');
        const glWinBranchInput = document.getElementById('glWinBranch');
        const processGlWinButton = document.getElementById('processGlWinButton');

        // Attach event listeners
        if (glWinInputFilesInput && !glWinInputFilesInput.dataset.listenerAttached) {
            glWinInputFilesInput.addEventListener('change', handleGlWinFileInputChange);
            glWinInputFilesInput.dataset.listenerAttached = 'true';
        }
        if (glWinBranchInput && !glWinBranchInput.dataset.listenerAttached) {
            glWinBranchInput.addEventListener('change', updateGlWinUI);
            glWinBranchInput.dataset.listenerAttached = 'true';
        }
        if (processGlWinButton && !processGlWinButton.dataset.listenerAttached) {
            processGlWinButton.addEventListener('click', processGlWin);
            processGlWinButton.dataset.listenerAttached = 'true';
        }

        // Initial render and UI update
        renderSelectedFiles(glWinSelectedFiles, 'glWinFilesDisplay', removeGlWinFile);
        updateGlWinUI();
    }

    // Register this sub-tab's initializer with the main application logic
    registerTabInitializer('glWin', initGlWinTab);
})(); // End IIFE
