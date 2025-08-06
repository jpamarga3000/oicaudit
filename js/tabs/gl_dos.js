// js/tabs/gl_dos.js

(function() { // Start IIFE
    // Local array to store selected files for this tab, declared inside the IIFE
    let glDosSelectedFiles = [];

    // Fixed output directory path (matches the backend)
    const FIXED_BASE_OUTPUT_DIR = "C:\\xampp\\htdocs\\audit_tool\\ACCOUTNING\\GENERAL LEDGER";

    /**
     * Removes a file from the glDosSelectedFiles array and updates the UI.
     * @param {number} indexToRemove - The index of the file to remove.
     */
    function removeGlDosFile(indexToRemove) {
        glDosSelectedFiles.splice(indexToRemove, 1);
        renderSelectedFiles(glDosSelectedFiles, 'glDosFilesDisplay', removeGlDosFile);
        updateGlDosUI();
    }

    /**
     * Updates the state of the "Process GL DOS Files" button based on input validity.
     */
    function updateGlDosUI() {
        const processGlDosButton = document.getElementById('processGlDosButton');
        const glDosBranchInput = document.getElementById('glDosBranch');

        // Button is enabled if files are selected AND a branch is chosen
        if (processGlDosButton && glDosBranchInput) {
            processGlDosButton.disabled = !(glDosSelectedFiles.length > 0 && glDosBranchInput.value.trim());
        }
    }

    /**
     * Handles the processing request for GL DOS data.
     */
    async function processGlDos() {
        const glDosBranchInput = document.getElementById('glDosBranch');
        const processGlDosButton = document.getElementById('processGlDosButton');

        const branchValue = glDosBranchInput ? glDosBranchInput.value.trim().toUpperCase() : '';

        if (glDosSelectedFiles.length === 0) {
            showMessage('Please select DBF files to process.', 'error');
            return;
        }
        if (!branchValue) {
            showMessage('Please select a branch.', 'error');
            return;
        }

        if (processGlDosButton) {
            processGlDosButton.disabled = true;
        }
        showMessage('Processing files... This may take a moment.', 'loading');

        const formData = new FormData();
        glDosSelectedFiles.forEach(file => {
            formData.append('files', file);
        });
        formData.append('branch', branchValue);
        // output_dir is now fixed in the backend and derived from branch

        try {
            const response = await fetch(`${FLASK_API_BASE_URL}/process_gl_dos`, {
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
            if (processGlDosButton) {
                processGlDosButton.disabled = false;
            }
        }
    }

    /**
     * Event handler for the glDosInputFiles input change.
     * @param {Event} event - The change event.
     */
    function handleGlDosFileInputChange(event) {
        Array.from(event.target.files).forEach(file => {
            if (!glDosSelectedFiles.some(existingFile => existingFile.name === file.name)) {
                glDosSelectedFiles.push(file);
            }
        });
        event.target.value = ''; // Clear the file input to allow selecting same files again
        renderSelectedFiles(glDosSelectedFiles, 'glDosFilesDisplay', removeGlDosFile);
        updateGlDosUI();
    }

    /**
     * Initializes the GL DOS sub-tab: attaches event listeners and performs initial UI update.
     * This function is called by main.js when the sub-tab is activated.
     */
    function initGlDosTab() {
        console.log('Initializing GL DOS Tab...');

        const glDosInputFilesInput = document.getElementById('glDosInputFiles');
        const glDosBranchInput = document.getElementById('glDosBranch');
        const processGlDosButton = document.getElementById('processGlDosButton');

        // Attach event listeners
        if (glDosInputFilesInput && !glDosInputFilesInput.dataset.listenerAttached) {
            glDosInputFilesInput.addEventListener('change', handleGlDosFileInputChange);
            glDosInputFilesInput.dataset.listenerAttached = 'true';
        }
        if (glDosBranchInput && !glDosBranchInput.dataset.listenerAttached) {
            glDosBranchInput.addEventListener('change', updateGlDosUI);
            glDosBranchInput.dataset.listenerAttached = 'true';
        }
        if (processGlDosButton && !processGlDosButton.dataset.listenerAttached) {
            processGlDosButton.addEventListener('click', processGlDos);
            processGlDosButton.dataset.listenerAttached = 'true';
        }

        // Initial render and UI update
        renderSelectedFiles(glDosSelectedFiles, 'glDosFilesDisplay', removeGlDosFile);
        updateGlDosUI();
    }

    // Register this sub-tab's initializer with the main application logic
    registerTabInitializer('glDos', initGlDosTab);
})(); // End IIFE
