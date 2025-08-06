// js/tabs/audit_tool_tb.js

(function() { // Start IIFE
    // Local array to store selected files for this tab
    let auditToolTbSelectedFiles = [];

    /**
     * Removes a file from the auditToolTbSelectedFiles array and updates the UI.
     * @param {number} indexToRemove - The index of the file to remove.
     */
    function removeAuditToolTbFile(indexToRemove) {
        auditToolTbSelectedFiles.splice(indexToRemove, 1);
        // Assuming renderSelectedFiles is a global helper function from utils.js
        renderSelectedFiles(auditToolTbSelectedFiles, 'auditToolTbFilesDisplay', removeAuditToolTbFile);
        updateAuditToolTbUI();
    }

    /**
     * Updates the state of the "Process Trial Balance Files" button based on input validity.
     */
    function updateAuditToolTbUI() {
        const processButton = document.getElementById('processAuditToolTbButton');
        // const branchInput = document.getElementById('auditToolTbBranch'); // Branch input removed

        // Button is enabled if files are selected (no branch selection needed from UI)
        if (processButton) {
            processButton.disabled = !(auditToolTbSelectedFiles.length > 0);
        }
    }

    /**
     * Handles the processing request for Trial Balance data.
     */
    async function processAuditToolTb() {
        // const branchInput = document.getElementById('auditToolTbBranch'); // Branch input removed
        const processButton = document.getElementById('processAuditToolTbButton');

        // Branch value will now be derived from the files themselves in the backend
        // const branchValue = branchInput ? branchInput.value.trim().toUpperCase() : '';

        if (auditToolTbSelectedFiles.length === 0) {
            // Assuming showMessage is a global helper function from utils.js
            showMessage('Please select Excel/CSV files to process.', 'error');
            return;
        }
        // No need to check for branchValue here, as it's derived from files

        if (processButton) {
            processButton.disabled = true;
        }
        showMessage('Processing files... This may take a moment.', 'loading');

        const formData = new FormData();
        auditToolTbSelectedFiles.forEach(file => {
            formData.append('files', file);
        });
        // Removed appending branch from frontend, as it's derived from files in backend
        // formData.append('branch', branchValue);

        try {
            // New endpoint for Trial Balance file processing
            const response = await fetch(`${FLASK_API_BASE_URL}/process_audit_tool_tb_files`, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                showMessage(result.message, 'success', result.output_path);
                // Optionally clear selected files after successful processing
                auditToolTbSelectedFiles = [];
                renderSelectedFiles(auditToolTbSelectedFiles, 'auditToolTbFilesDisplay', removeAuditToolTbFile);
            } else {
                showMessage(`Error: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('Fetch error:', error);
            showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
        } finally {
            if (processButton) {
                processButton.disabled = false;
            }
            updateAuditToolTbUI();
        }
    }

    /**
     * Event handler for the auditToolTbInputFiles input change.
     * @param {Event} event - The change event.
     */
    function handleAuditToolTbFileInputChange(event) {
        Array.from(event.target.files).forEach(file => {
            if (!auditToolTbSelectedFiles.some(existingFile => existingFile.name === file.name)) {
                auditToolTbSelectedFiles.push(file);
            }
        });
        event.target.value = ''; // Clear the file input to allow selecting same files again
        renderSelectedFiles(auditToolTbSelectedFiles, 'auditToolTbFilesDisplay', removeAuditToolTbFile);
        updateAuditToolTbUI();
    }

    /**
     * Initializes the Trial Balance sub-tab: attaches event listeners and performs initial UI update.
     * This function is called by main.js when the sub-tab is activated.
     */
    function initAuditToolTbTab() {
        console.log('Initializing Trial Balance File Processing Tab...');

        const auditToolTbInputFilesInput = document.getElementById('auditToolTbInputFiles');
        // const auditToolTbBranchInput = document.getElementById('auditToolTbBranch'); // Branch input removed
        const processButton = document.getElementById('processAuditToolTbButton');

        // Attach event listeners
        if (auditToolTbInputFilesInput && !auditToolTbInputFilesInput.dataset.listenerAttached) {
            auditToolTbInputFilesInput.addEventListener('change', handleAuditToolTbFileInputChange);
            auditToolTbInputFilesInput.dataset.listenerAttached = 'true';
        }
        // Removed branch input change listener
        // if (auditToolTbBranchInput && !auditToolTbBranchInput.dataset.listenerAttached) {
        //     auditToolTbBranchInput.addEventListener('change', updateAuditToolTbUI);
        //     auditToolTbBranchInput.dataset.listenerAttached = 'true';
        // }
        if (processButton && !processButton.dataset.listenerAttached) {
            processButton.addEventListener('click', processAuditToolTb);
            processButton.dataset.listenerAttached = 'true';
        }

        // Initial render and UI update
        renderSelectedFiles(auditToolTbSelectedFiles, 'auditToolTbFilesDisplay', removeAuditToolTbFile);
        updateAuditToolTbUI();
    }

    // Register this sub-tab's initializer with the main application logic
    // Assuming 'registerTabInitializer' is available globally from main.js
    registerTabInitializer('auditToolTbSection', initAuditToolTbTab); // Register with the section ID
})(); // End IIFE
