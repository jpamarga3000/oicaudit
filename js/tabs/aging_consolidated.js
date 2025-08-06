// js/tabs/aging_consolidated.js

(function() { // Start IIFE
    // Local array to store selected files for this tab, declared inside the IIFE
    let agingSelectedFiles = [];

    /**
     * Removes a file from the agingSelectedFiles array and updates the UI.
     * This function is passed as a callback to renderSelectedFiles.
     * @param {number} indexToRemove - The index of the file to remove.
     */
    function removeAgingFile(indexToRemove) {
        agingSelectedFiles.splice(indexToRemove, 1);
        // Re-render the file display and update the button state
        renderSelectedFiles(agingSelectedFiles, 'agingFilesDisplay', removeAgingFile);
        updateAgingConsolidatedUI();
    }

    /**
     * Updates the state of the "Process Aging Consolidated" button based on input validity.
     */
    function updateAgingConsolidatedUI() {
        const processAgingButton = document.getElementById('processAgingButton');
        const agingOutputFolderInput = document.getElementById('agingOutputFolder');

        if (processAgingButton && agingOutputFolderInput) {
            // Button is enabled if files are selected AND an output folder path is provided
            processAgingButton.disabled = !(agingSelectedFiles.length > 0 && agingOutputFolderInput.value.trim());
        }
    }

    /**
     * Handles the processing request for Aging Consolidated data.
     */
    async function processAgingConsolidated() {
        const agingOutputFolderInput = document.getElementById('agingOutputFolder');
        const processAgingButton = document.getElementById('processAgingButton');
        const outputPath = agingOutputFolderInput ? agingOutputFolderInput.value.trim() : '';

        if (agingSelectedFiles.length === 0 || !outputPath) {
            showMessage('Please select Excel files and enter the output folder path.', 'error');
            return;
        }

        if (processAgingButton) {
            processAgingButton.disabled = true; // Disable button during processing
        }
        showMessage('Processing files... This may take a moment.', 'loading');

        const formData = new FormData();
        agingSelectedFiles.forEach(file => {
            formData.append('files', file);
        });
        formData.append('output_dir', outputPath);

        try {
            const response = await fetch(`${FLASK_API_BASE_URL}/process_aging_consolidated`, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                showMessage(result.message, 'success', outputPath); // Pass outputPath
            } else {
                showMessage(`Error: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('Fetch error:', error);
            showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
        } finally {
            if (processAgingButton) {
                processAgingButton.disabled = false; // Re-enable button
            }
        }
    }

    /**
     * Event handler for the agingInputFiles input change.
     * @param {Event} event - The change event.
     */
    function handleAgingFileInputChange(event) {
        // Removed: Re-enable global click listener after file dialog interaction (no longer needed)

        Array.from(event.target.files).forEach(file => {
            // Add file only if it's not already in the list (by name)
            if (!agingSelectedFiles.some(existingFile => existingFile.name === file.name)) {
                agingSelectedFiles.push(file);
            }
        });
        event.target.value = ''; // Clear the input to allow selecting the same file(s) again
        renderSelectedFiles(agingSelectedFiles, 'agingFilesDisplay', removeAgingFile);
        updateAgingConsolidatedUI();
    }

    /**
     * Initializes the Aging Consolidated tab: attaches event listeners and performs initial UI update.
     * This function is called by main.js when the tab is activated.
     */
    function initAgingConsolidatedTab() {
        console.log('Initializing Aging Consolidated Tab...');

        const agingInputFilesInput = document.getElementById('agingInputFiles');
        const agingOutputFolderInput = document.getElementById('agingOutputFolder');
        const processAgingButton = document.getElementById('processAgingButton');
        const customFileButton = document.querySelector('#agingConsolidatedSection .custom-file-button'); // Select the specific button

        // Attach event listener for file selection
        // Ensure event listeners are only attached once to prevent multiple triggers
        if (agingInputFilesInput && !agingInputFilesInput.dataset.listenerAttached) {
            agingInputFilesInput.addEventListener('change', handleAgingFileInputChange);
            agingInputFilesInput.dataset.listenerAttached = 'true';
        }
        // Attach event listener for output folder input
        if (agingOutputFolderInput && !agingOutputFolderInput.dataset.listenerAttached) {
            agingOutputFolderInput.addEventListener('input', updateAgingConsolidatedUI);
            agingOutputFolderInput.dataset.listenerAttached = 'true';
        }
        // Attach event listener for process button click
        if (processAgingButton && !processAgingButton.dataset.listenerAttached) {
            processAgingButton.addEventListener('click', processAgingConsolidated);
            processAgingButton.dataset.listenerAttached = 'true';
        }

        // Removed: Add a click listener to the custom button that opens the file input (no longer needed for global listener)
        // if (customFileButton && !customFileButton.dataset.listenerAttached) {
        //     customFileButton.addEventListener('click', () => {
        //         if (typeof window.disableGlobalClickListener !== 'undefined') {
        //             window.disableGlobalClickListener = true;
        //             console.log('DEBUG: Global click listener temporarily disabled before file dialog (Aging).');
        //         }
        //     });
        //     customFileButton.dataset.listenerAttached = 'true';
        // }


        // Initial render and UI update
        renderSelectedFiles(agingSelectedFiles, 'agingFilesDisplay', removeAgingFile);
        updateAgingConsolidatedUI();
    }

    // Register this tab's initializer with the main application logic
    registerTabInitializer('agingConsolidatedSection', initAgingConsolidatedTab); // Use the section ID
})(); // End IIFE
