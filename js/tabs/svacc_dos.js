// js/tabs/svacc_dos.js (Modified: Hardcoded output path and updated UI logic)

(function() { // Start IIFE
    // Local array to store selected files for this tab, declared inside the IIFE
    let svaccDosSelectedFiles = [];

    // Hardcoded output path as requested
    const HARDCODED_OUTPUT_PATH = "C:\\xampp\\htdocs\\audit_tool\\OPERATIONS\\SVACC";

    // Reference to the message display element
    let svaccDosMessageDiv;

    /**
     * Displays a message in the svaccDosMessageDiv.
     * @param {string} message - The message to display.
     * @param {string} type - The type of message ('success', 'error', 'loading', 'info').
     */
    function displaySvaccDosMessage(message, type) {
        if (!svaccDosMessageDiv) {
            svaccDosMessageDiv = document.getElementById('svaccDosMessage');
        }
        if (svaccDosMessageDiv) {
            svaccDosMessageDiv.textContent = message;
            // Clear previous classes
            svaccDosMessageDiv.className = 'mt-4 text-sm font-medium';
            // Add new classes based on type
            if (type === 'success') {
                svaccDosMessageDiv.classList.add('text-green-600');
            } else if (type === 'error') {
                svaccDosMessageDiv.classList.add('text-red-600');
            } else if (type === 'loading') {
                svaccDosMessageDiv.classList.add('text-blue-600');
            } else if (type === 'info') {
                svaccDosMessageDiv.classList.add('text-gray-600');
            }
        }
    }


    /**
     * Removes a file from the svaccDosSelectedFiles array and updates the UI.
     * @param {number} indexToRemove - The index of the file to remove.
     */
    function removeSvaccDosFile(indexToRemove) {
        svaccDosSelectedFiles.splice(indexToRemove, 1);
        renderSelectedFiles(svaccDosSelectedFiles, 'svaccDosFilesDisplay', removeSvaccDosFile);
        updateSvaccDosUI();
    }

    /**
     * Updates the state of the "Process SVACC DOS Files" button based on input validity.
     * The output folder path input is no longer considered as it's hardcoded.
     */
    function updateSvaccDosUI() {
        const processSvaccDosButton = document.getElementById('processSvaccDosButton');
        const svaccDosBranchInput = document.getElementById('svaccDosBranch');

        if (processSvaccDosButton && svaccDosBranchInput) {
            // Button is enabled if files are selected AND a branch is selected.
            processSvaccDosButton.disabled = !(svaccDosSelectedFiles.length > 0 && svaccDosBranchInput.value.trim());
        }
    }

    /**
     * Handles the processing request for SVACC DOS data.
     */
    async function processSvaccDos() {
        const svaccDosBranchInput = document.getElementById('svaccDosBranch');
        const processSvaccDosButton = document.getElementById('processSvaccDosButton');

        // Use the hardcoded path directly
        const outputPath = HARDCODED_OUTPUT_PATH;
        const selectedBranch = svaccDosBranchInput ? svaccDosBranchInput.value.trim() : '';

        if (svaccDosSelectedFiles.length === 0 || !selectedBranch) {
            displaySvaccDosMessage('Please select DBF files and select a branch.', 'error');
            return;
        }

        if (processSvaccDosButton) {
            processSvaccDosButton.disabled = true;
        }
        displaySvaccDosMessage('Processing files... This may take a moment.', 'loading');

        const formData = new FormData();
        svaccDosSelectedFiles.forEach(file => {
            formData.append('files', file);
        });
        formData.append('selected_branch', selectedBranch);

        try {
            const response = await fetch(`${FLASK_API_BASE_URL}/process_svacc_dos`, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                displaySvaccDosMessage(result.message, 'success'); 
            } else {
                displaySvaccDosMessage(`Error: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('Fetch error:', error);
            displaySvaccDosMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
        } finally {
            if (processSvaccDosButton) {
                processSvaccDosButton.disabled = false;
            }
        }
    }

    /**
     * Event handler for the svaccDosInputFiles input change.
     * @param {Event} event - The change event.
     */
    function handleSvaccDosFileInputChange(event) {
        Array.from(event.target.files).forEach(file => {
            if (!svaccDosSelectedFiles.some(existingFile => existingFile.name === file.name)) {
                svaccDosSelectedFiles.push(file);
            }
        });
        event.target.value = '';
        renderSelectedFiles(svaccDosSelectedFiles, 'svaccDosFilesDisplay', removeSvaccDosFile);
        updateSvaccDosUI();
    }

    /**
     * Initializes the SVACC DOS sub-tab: attaches event listeners and performs initial UI update.
     * This function is called by main.js when the sub-tab is activated.
     */
    function initSvaccDosTab() {
        console.log('Initializing SVACC DOS Tab...');

        const svaccDosInputFilesInput = document.getElementById('svaccDosInputFiles');
        const svaccDosBranchInput = document.getElementById('svaccDosBranch');
        const processSvaccDosButton = document.getElementById('processSvaccDosButton');
        
        // Initialize the message div reference
        svaccDosMessageDiv = document.getElementById('svaccDosMessage');

        // Attach event listeners
        if (svaccDosInputFilesInput && !svaccDosInputFilesInput.dataset.listenerAttached) {
            svaccDosInputFilesInput.addEventListener('change', handleSvaccDosFileInputChange);
            svaccDosInputFilesInput.dataset.listenerAttached = 'true';
        }
        if (svaccDosBranchInput && !svaccDosBranchInput.dataset.listenerAttached) {
            svaccDosBranchInput.addEventListener('change', updateSvaccDosUI);
            svaccDosBranchInput.dataset.listenerAttached = 'true';
        }
        if (processSvaccDosButton && !processSvaccDosButton.dataset.listenerAttached) {
            processSvaccDosButton.addEventListener('click', processSvaccDos);
            processSvaccDosButton.dataset.listenerAttached = 'true';
        }

        // Initial render and UI update
        renderSelectedFiles(svaccDosSelectedFiles, 'svaccDosFilesDisplay', removeSvaccDosFile);
        updateSvaccDosUI();
        // Clear any previous messages when the tab is initialized
        displaySvaccDosMessage('', 'info'); 
    }

    // Register this sub-tab's initializer with the main application logic
    registerTabInitializer('svaccDos', initSvaccDosTab);
})(); // End IIFE
