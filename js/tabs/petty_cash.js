// js/tabs/petty_cash.js

(function() { // Start IIFE
    // Local array to store selected files for this tab, declared inside the IIFE
    let pettySelectedFiles = [];

    /**
     * Removes a file from the pettySelectedFiles array and updates the UI.
     * This function is passed as a callback to renderSelectedFiles.
     * @param {number} indexToRemove - The index of the file to remove.
     */
    function removePettyFile(indexToRemove) {
        pettySelectedFiles.splice(indexToRemove, 1);
        // Re-render the file display and update the button state
        renderSelectedFiles(pettySelectedFiles, 'pettyFilesDisplay', removePettyFile);
        updatePettyCashUI();
    }

    /**
     * Updates the state of the "Process Petty Cash" button based on input validity.
     */
    function updatePettyCashUI() {
        const processPettyButton = document.getElementById('processPettyButton');
        const pettyOutputFolderInput = document.getElementById('pettyOutputFolder');

        if (processPettyButton && pettyOutputFolderInput) {
            // Button is enabled if files are selected AND an output folder path is provided
            processPettyButton.disabled = !(pettySelectedFiles.length > 0 && pettyOutputFolderInput.value.trim());
        }
    }

    /**
     * Handles the processing request for Petty Cash data.
     */
    async function processPettyCash() {
        const pettyOutputFolderInput = document.getElementById('pettyOutputFolder');
        const processPettyButton = document.getElementById('processPettyButton');
        const outputPath = pettyOutputFolderInput ? pettyOutputFolderInput.value.trim() : '';

        if (pettySelectedFiles.length === 0 || !outputPath) {
            showMessage('Please select Excel files and enter the output folder path.', 'error');
            return;
        }

        if (processPettyButton) {
            processPettyButton.disabled = true; // Disable button during processing
        }
        showMessage('Processing files... This may take a moment.', 'loading');

        const formData = new FormData();
        pettySelectedFiles.forEach(file => {
            formData.append('files', file);
        });
        formData.append('output_dir', outputPath);

        try {
            const response = await fetch(`${FLASK_API_BASE_URL}/process_petty_cash`, {
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
            if (processPettyButton) {
                processPettyButton.disabled = false; // Re-enable button
            }
        }
    }

    /**
     * Event handler for the pettyInputFiles input change.
     * @param {Event} event - The change event.
     */
    function handlePettyFileInputChange(event) {
        // Removed: Re-enable global click listener after file dialog interaction (no longer needed)

        Array.from(event.target.files).forEach(file => {
            // Add file only if it's not already in the list (by name)
            if (!pettySelectedFiles.some(existingFile => existingFile.name === file.name)) {
                pettySelectedFiles.push(file);
            }
        });
        event.target.value = ''; // Clear the input to allow selecting the same file(s) again
        renderSelectedFiles(pettySelectedFiles, 'pettyFilesDisplay', removePettyFile);
        updatePettyCashUI();
    }

    /**
     * Initializes the Petty Cash tab: attaches event listeners and performs initial UI update.
     * This function is called by main.js when the tab is activated.
     */
    function initPettyCashTab() {
        console.log('Initializing Petty Cash Tab...');

        const pettyInputFilesInput = document.getElementById('pettyInputFiles');
        const pettyOutputFolderInput = document.getElementById('pettyOutputFolder');
        const processPettyButton = document.getElementById('processPettyButton');
        const customFileButton = document.querySelector('#pettyCashSection .custom-file-button'); // Select the specific button

        // Attach event listener for file selection
        if (pettyInputFilesInput && !pettyInputFilesInput.dataset.listenerAttached) {
            pettyInputFilesInput.addEventListener('change', handlePettyFileInputChange);
            pettyInputFilesInput.dataset.listenerAttached = 'true';
        }
        // Attach event listener for output folder input
        if (pettyOutputFolderInput && !pettyOutputFolderInput.dataset.listenerAttached) {
            pettyOutputFolderInput.addEventListener('input', updatePettyCashUI);
            pettyOutputFolderInput.dataset.listenerAttached = 'true';
        }
        // Attach event listener for process button click
        if (processPettyButton && !processPettyButton.dataset.listenerAttached) {
            processPettyButton.addEventListener('click', processPettyCash);
            processPettyButton.dataset.listenerAttached = 'true';
        }

        // Removed: Add a click listener to the custom button that opens the file input (no longer needed for global listener)
        // if (customFileButton && !customFileButton.dataset.listenerAttached) {
        //     customFileButton.addEventListener('click', () => {
        //         if (typeof window.disableGlobalClickListener !== 'undefined') {
        //             window.disableGlobalClickListener = true;
        //             console.log('DEBUG: Global click listener temporarily disabled before file dialog (Petty Cash).');
        //         }
        //     });
        //     customFileButton.dataset.listenerAttached = 'true';
        // }

        // Initial render and UI update
        renderSelectedFiles(pettySelectedFiles, 'pettyFilesDisplay', removePettyFile);
        updatePettyCashUI();
    }

    // Register this tab's initializer with the main application logic
    registerTabInitializer('pettyCashSection', initPettyCashTab); // Use the section ID
})(); // End IIFE
