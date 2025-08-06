// audit_tool/js/tabs/lnacc_win.js

// Ensure window.registerTabInitializer is available from main.js
if (window.registerTabInitializer) {
    (function() { // Start IIFE
        const lnaccWinInputFiles = document.getElementById('lnaccWinInputFiles');
        const lnaccWinFilesDisplay = document.getElementById('lnaccWinFilesDisplay');
        const lnaccWinCidRefFiles = document.getElementById('lnaccWinCidRefFiles');
        const lnaccWinCidRefFilesDisplay = document.getElementById('lnaccWinCidRefFilesDisplay');
        const lnaccWinBranch = document.getElementById('lnaccWinBranch');
        const processLnaccWinButton = document.getElementById('processLnaccWinButton');
        // Removed lnaccWinOutputFolder as it's no longer displayed or needed from frontend

        // Reference to the message display element
        let lnaccWinMessageDiv; // Declared here, initialized in initLnaccWinTab

        /**
         * Displays a message in the lnaccWinMessageDiv.
         * @param {string} message - The message to display.
         * @param {string} type - The type of message ('success', 'error', 'loading', 'info').
         */
        function displayLnaccWinMessage(message, type) {
            if (!lnaccWinMessageDiv) {
                lnaccWinMessageDiv = document.getElementById('lnaccWinMessage');
            }
            if (lnaccWinMessageDiv) {
                lnaccWinMessageDiv.textContent = message;
                // Clear previous classes
                lnaccWinMessageDiv.className = 'mt-4 text-sm font-medium';
                // Add new classes based on type
                if (type === 'success') {
                    lnaccWinMessageDiv.classList.add('text-green-600');
                } else if (type === 'error') {
                    lnaccWinMessageDiv.classList.add('text-red-600');
                } else if (type === 'loading') {
                    lnaccWinMessageDiv.classList.add('text-blue-600');
                } else if (type === 'info') {
                    lnaccWinMessageDiv.classList.add('text-gray-600');
                }
            }
        }

        function updateProcessButtonState() {
            // Enable button only if LNACC files are selected and a branch is chosen
            processLnaccWinButton.disabled = !(lnaccWinInputFiles.files.length > 0 && lnaccWinBranch.value.trim() !== '');
        }

        /**
         * Event handler for the lnaccWinInputFiles input change.
         * @param {Event} event - The change event.
         */
        function handleLnaccWinFileInputChange(event) {
            const files = event.target.files;
            if (files.length > 0) {
                let fileNames = Array.from(files).map(file => file.name).join(', ');
                lnaccWinFilesDisplay.textContent = `Selected Files: ${fileNames}`;
            } else {
                lnaccWinFilesDisplay.textContent = 'No files selected.';
            }
            updateProcessButtonState();
        }

        /**
         * Event handler for the lnaccWinCidRefFiles input change.
         * @param {Event} event - The change event.
         */
        function handleLnaccWinCidRefFilesChange(event) {
            const file = event.target.files[0];
            if (file) {
                lnaccWinCidRefFilesDisplay.textContent = `Selected File: ${file.name}`;
            } else {
                lnaccWinCidRefFilesDisplay.textContent = 'No file selected.';
            }
            // CID reference file does not affect button state directly, but good to update display.
        }

        /**
         * Handles the processing request for LNACC WIN data.
         */
        async function processLnaccWin() {
            console.log("LNACC WIN: Process button clicked."); // Debug log
            const lnaccFiles = lnaccWinInputFiles.files;
            const cidRefFile = lnaccWinCidRefFiles.files[0];
            const branch = lnaccWinBranch.value.trim();

            if (lnaccFiles.length === 0) {
                displayLnaccWinMessage('Please select LNACC CSV files to process.', 'error');
                console.log("LNACC WIN: Validation failed - No LNACC files selected."); // Debug log
                return;
            }
            if (!branch) {
                displayLnaccWinMessage('Please select a branch.', 'error');
                console.log("LNACC WIN: Validation failed - No branch selected."); // Debug log
                return;
            }

            // Disable button and show loading indicator
            processLnaccWinButton.disabled = true;
            processLnaccWinButton.textContent = 'Processing...';
            // Assuming showLoading is a global utility, if not, implement a local one or remove
            if (typeof showLoading === 'function') {
                showLoading(true);
            }
            displayLnaccWinMessage('Processing files... This may take a moment.', 'loading');
            console.log("LNACC WIN: Starting file processing request..."); // Debug log

            const formData = new FormData();
            for (let i = 0; i < lnaccFiles.length; i++) {
                formData.append('files', lnaccFiles[i]);
            }
            if (cidRefFile) {
                formData.append('cid_ref_file', cidRefFile);
            }
            formData.append('selected_branch', branch);

            // Debug log: Inspect FormData content (for debugging only, avoid in production for large files)
            console.log("LNACC WIN: FormData prepared:");
            for (let pair of formData.entries()) {
                console.log(pair[0]+ ', ' + pair[1]); 
            }

            try {
                // CORRECTED API ENDPOINT URL: Removed '.py' and 'routes' subdirectory from the path
                const url = `${window.FLASK_API_BASE_URL}/process_lnacc_win`;
                console.log(`LNACC WIN: Sending POST request to: ${url}`); // Debug log

                const response = await fetch(url, {
                    method: 'POST',
                    body: formData
                });

                console.log("LNACC WIN: Received response from backend."); // Debug log
                
                // Check if response is OK before trying to parse JSON
                if (!response.ok) {
                    const errorText = await response.text(); // Get response as text to see HTML
                    console.error('LNACC WIN: Backend response not OK. Status:', response.status, 'Text:', errorText);
                    displayLnaccWinMessage(`Error: Server responded with status ${response.status}. Check console for details.`, 'error');
                    return; // Exit here if response is not OK
                }

                const result = await response.json(); // Now safe to parse as JSON
                console.log("LNACC WIN: Backend response (JSON):", result); // Debug log

                if (result.success) { // Use result.success as per Flask jsonify
                    displayLnaccWinMessage(result.message, 'success');
                    // Optionally clear file inputs and reset display after successful processing
                    lnaccWinInputFiles.value = '';
                    lnaccWinFilesDisplay.textContent = 'No files selected.';
                    lnaccWinCidRefFiles.value = '';
                    lnaccWinCidRefFilesDisplay.textContent = 'No file selected.';
                    lnaccWinBranch.value = ''; // Reset branch selection
                } else {
                    displayLnaccWinMessage(result.message || 'An unknown error occurred.', 'error'); // Use result.message for error
                }
            } catch (error) {
                console.error('LNACC WIN: Fetch error or JSON parsing error:', error); // Detailed error log
                displayLnaccWinMessage('Network error or server is unreachable, or response was not valid JSON. Check browser console for details.', 'error');
            } finally {
                processLnaccWinButton.disabled = false;
                processLnaccWinButton.textContent = 'Process LNACC WIN Files';
                if (typeof showLoading === 'function') {
                    showLoading(false);
                }
                updateProcessButtonState(); // Re-evaluate button state after processing
                console.log("LNACC WIN: Processing finished (finally block executed)."); // Debug log
            }
        }

        /**
         * Initializes the LNACC WIN sub-tab: attaches event listeners and performs initial UI update.
         * This function is called by main.js when the sub-tab is activated.
         */
        function initLnaccWinTab() {
            console.log('Initializing LNACC WIN Tab...');

            // Get message div reference
            lnaccWinMessageDiv = document.getElementById('lnaccWinMessage');

            // Attach event listeners
            // Check if listener is already attached to prevent duplicates
            if (lnaccWinInputFiles && !lnaccWinInputFiles.dataset.listenerAttached) {
                lnaccWinInputFiles.addEventListener('change', handleLnaccWinFileInputChange);
                lnaccWinInputFiles.dataset.listenerAttached = 'true';
            }
            if (lnaccWinCidRefFiles && !lnaccWinCidRefFiles.dataset.listenerAttached) {
                lnaccWinCidRefFiles.addEventListener('change', handleLnaccWinCidRefFilesChange);
                lnaccWinCidRefFiles.dataset.listenerAttached = 'true';
            }
            if (lnaccWinBranch && !lnaccWinBranch.dataset.listenerAttached) {
                lnaccWinBranch.addEventListener('change', updateProcessButtonState);
                lnaccWinBranch.dataset.listenerAttached = 'true';
            }
            if (processLnaccWinButton && !processLnaccWinButton.dataset.listenerAttached) {
                processLnaccWinButton.addEventListener('click', processLnaccWin);
                processLnaccWinButton.dataset.listenerAttached = 'true';
            }

            // Initial UI update and message clearing
            updateProcessButtonState();
            displayLnaccWinMessage('', 'info'); // Clear message on initial load
        }

        // Register this sub-tab's initializer with the main application logic
        window.registerTabInitializer('lnaccWin', initLnaccWinTab);

    })(); // End IIFE
} else {
    console.error("lnacc_win.js: window.registerTabInitializer is not defined. Ensure main.js is loaded first.");
}
