// js/tabs/svacc_win.js (Modified: Hardcoded output path and updated UI logic)

(function() { // Start IIFE
    // Local arrays to store selected files for this tab, declared inside the IIFE
    let svaccWinSelectedFiles = [];
    let svaccWinLnhistFiles = []; // For the optional LNHIST file

    // Hardcoded output path as requested
    const HARDCODED_OUTPUT_PATH = "C:\\xampp\\htdocs\\audit_tool\\OPERATIONS\\SVACC";

    /**
     * Removes a file from the appropriate array and updates the UI.
     * @param {number} indexToRemove - The index of the file to remove.
     * @param {string} fileType - 'main' or 'lnhist' to distinguish which array to modify.
     */
    function removeSvaccWinFile(indexToRemove, fileType) {
        if (fileType === 'main') {
            svaccWinSelectedFiles.splice(indexToRemove, 1);
            renderSelectedFiles(svaccWinSelectedFiles, 'svaccWinFilesDisplay', (idx) => removeSvaccWinFile(idx, 'main'));
        } else if (fileType === 'lnhist') {
            svaccWinLnhistFiles.splice(indexToRemove, 1);
            renderSelectedFiles(svaccWinLnhistFiles, 'svaccWinLnhistFilesDisplay', (idx) => removeSvaccWinFile(idx, 'lnhist'));
        }
        updateSvaccWinUI();
    }

    /**
     * Updates the state of the "Process SVACC WIN Files" button based on input validity.
     * The output folder path input is no longer considered as it's hardcoded.
     */
    function updateSvaccWinUI() {
        const processSvaccWinButton = document.getElementById('processSvaccWinButton');
        // const svaccWinOutputFolderInput = document.getElementById('svaccWinOutputFolder'); // Removed
        const svaccWinBranchInput = document.getElementById('svaccWinBranch');

        if (processSvaccWinButton && svaccWinBranchInput) {
            // const isOutputFolderValid = svaccWinOutputFolderInput.value.trim() !== ''; // Removed
            const isMainFilesSelected = svaccWinSelectedFiles.length > 0;
            const isBranchSelected = svaccWinBranchInput.value.trim() !== '';

            // Button is enabled if main files are selected AND a branch is selected.
            processSvaccWinButton.disabled = !(isMainFilesSelected && isBranchSelected);
        }
    }

    /**
     * Handles the processing request for SVACC WIN data.
     */
    async function processSvaccWin() {
        // const svaccWinOutputFolderInput = document.getElementById('svaccWinOutputFolder'); // Removed
        const svaccWinBranchInput = document.getElementById('svaccWinBranch');
        const processSvaccWinButton = document.getElementById('processSvaccWinButton');
        // const svaccWinLnhistFilesInput = document.getElementById('svaccWinLnhistFiles'); // No longer needed for value

        // Use the hardcoded path directly
        const outputPath = HARDCODED_OUTPUT_PATH;
        const selectedBranch = svaccWinBranchInput ? svaccWinBranchInput.value.trim() : '';

        if (svaccWinSelectedFiles.length === 0 || !selectedBranch) {
            showMessage('Please select SVACC CSV files and select a branch.', 'error');
            return;
        }

        if (processSvaccWinButton) {
            processSvaccWinButton.disabled = true;
        }
        showMessage('Processing files... This may take a moment.', 'loading');

        const formData = new FormData();
        svaccWinSelectedFiles.forEach(file => {
            formData.append('files', file);
        });
        // Removed: formData.append('output_dir', outputPath); // Output directory is now hardcoded in backend
        formData.append('selected_branch', selectedBranch);

        // Add LNHIST file if selected
        if (svaccWinLnhistFiles.length > 0) {
            formData.append('lnhist_file', svaccWinLnhistFiles[0]); // Assuming only one LNHIST file
        }

        try {
            const response = await fetch(`${FLASK_API_BASE_URL}/process_svacc_win`, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                // Pass the hardcoded outputPath to showMessage for display purposes
                showMessage(result.message, 'success', outputPath); 
            } else {
                showMessage(`Error: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('Fetch error:', error);
            showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
        } finally {
            if (processSvaccWinButton) {
                processSvaccWinButton.disabled = false;
            }
        }
    }

    /**
     * Event handler for the svaccWinInputFiles input change.
     * @param {Event} event - The change event.
     */
    function handleSvaccWinFileInputChange(event) {
        Array.from(event.target.files).forEach(file => {
            if (!svaccWinSelectedFiles.some(existingFile => existingFile.name === file.name)) {
                svaccWinSelectedFiles.push(file);
            }
        });
        event.target.value = '';
        renderSelectedFiles(svaccWinSelectedFiles, 'svaccWinFilesDisplay', (idx) => removeSvaccWinFile(idx, 'main'));
        updateSvaccWinUI();
    }

    /**
     * Event handler for the svaccWinLnhistFiles input change.
     * @param {Event} event - The change event.
     */
    function handleSvaccWinLnhistFileInputChange(event) {
        // Only allow one file for LNHIST
        svaccWinLnhistFiles = [];
        if (event.target.files.length > 0) {
            svaccWinLnhistFiles.push(event.target.files[0]);
        }
        event.target.value = ''; // Clear input to allow re-selection of same file
        renderSelectedFiles(svaccWinLnhistFiles, 'svaccWinLnhistFilesDisplay', (idx) => removeSvaccWinFile(idx, 'lnhist'));
        updateSvaccWinUI();
    }

    /**
     * Initializes the SVACC WIN sub-tab: attaches event listeners and performs initial UI update.
     * This function is called by main.js when the sub-tab is activated.
     */
    function initSvaccWinTab() {
        console.log('Initializing SVACC WIN Tab...');

        const svaccWinInputFilesInput = document.getElementById('svaccWinInputFiles');
        // const svaccWinOutputFolderInput = document.getElementById('svaccWinOutputFolder'); // Removed
        const svaccWinLnhistFilesInput = document.getElementById('svaccWinLnhistFiles');
        const svaccWinBranchInput = document.getElementById('svaccWinBranch');
        const processSvaccWinButton = document.getElementById('processSvaccWinButton');
        // const customMainFileButton = document.querySelector('#svaccWin .custom-file-button:first-of-type'); // Removed
        // const customLnhistFileButton = document.querySelector('#svaccWin .custom-file-button:last-of-type'); // Removed


        // Attach event listeners for main files
        if (svaccWinInputFilesInput && !svaccWinInputFilesInput.dataset.listenerAttached) {
            svaccWinInputFilesInput.addEventListener('change', handleSvaccWinFileInputChange);
            svaccWinInputFilesInput.dataset.listenerAttached = 'true';
        }
        // Attach event listener for LNHIST file
        if (svaccWinLnhistFilesInput && !svaccWinLnhistFilesInput.dataset.listenerAttached) {
            svaccWinLnhistFilesInput.addEventListener('change', handleSvaccWinLnhistFileInputChange);
            svaccWinLnhistFilesInput.dataset.listenerAttached = 'true';
        }
        // Removed: Output folder input listener no longer needed
        // if (svaccWinOutputFolderInput && !svaccWinOutputFolderInput.dataset.listenerAttached) {
        //     svaccWinOutputFolderInput.addEventListener('input', updateSvaccWinUI);
        //     svaccWinOutputFolderInput.dataset.listenerAttached = 'true';
        // }
        // Attach event listener for branch selection
        if (svaccWinBranchInput && !svaccWinBranchInput.dataset.listenerAttached) {
            svaccWinBranchInput.addEventListener('change', updateSvaccWinUI);
            svaccWinBranchInput.dataset.listenerAttached = 'true';
        }
        // Attach event listener for process button click
        if (processSvaccWinButton && !processSvaccWinButton.dataset.listenerAttached) {
            processSvaccWinButton.addEventListener('click', processSvaccWin);
            processSvaccWinButton.dataset.listenerAttached = 'true';
        }

        // Initial render and UI update
        renderSelectedFiles(svaccWinSelectedFiles, 'svaccWinFilesDisplay', (idx) => removeSvaccWinFile(idx, 'main'));
        renderSelectedFiles(svaccWinLnhistFiles, 'svaccWinLnhistFilesDisplay', (idx) => removeSvaccWinFile(idx, 'lnhist'));
        updateSvaccWinUI();
    }

    // Register this sub-tab's initializer with the main application logic
    registerTabInitializer('svaccWin', initSvaccWinTab);
})(); // End IIFE
