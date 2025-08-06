// audit_tool/js/tabs/lnacc_dos.js

document.addEventListener('DOMContentLoaded', function() {
    const lnaccDosInputFiles = document.getElementById('lnaccDosInputFiles');
    const lnaccDosFilesDisplay = document.getElementById('lnaccDosFilesDisplay');
    const lnaccDosBranch = document.getElementById('lnaccDosBranch');
    const processLnaccDosButton = document.getElementById('processLnaccDosButton');
    const lnaccDosLoadingOverlay = document.getElementById('lnaccDosLoadingOverlay'); // Get the new loading overlay
    
    // Reference to the message display element
    let lnaccDosMessageDiv = document.getElementById('lnaccDosMessage'); // Get reference on load

    /**
     * Displays a message in the lnaccDosMessageDiv.
     * @param {string} message - The message to display.
     * @param {string} type - The type of message ('success', 'error', 'loading', 'info').
     */
    function displayLnaccDosMessage(message, type) {
        if (!lnaccDosMessageDiv) {
            lnaccDosMessageDiv = document.getElementById('lnaccDosMessage'); // Re-get if somehow null
        }
        if (lnaccDosMessageDiv) {
            lnaccDosMessageDiv.textContent = message;
            // Clear previous classes
            lnaccDosMessageDiv.className = 'mt-4 text-sm font-medium';
            // Add new classes based on type
            if (type === 'success') {
                lnaccDosMessageDiv.classList.add('text-green-600');
            } else if (type === 'error') {
                lnaccDosMessageDiv.classList.add('text-red-600');
            } else if (type === 'loading') {
                lnaccDosMessageDiv.classList.add('text-blue-600');
            } else if (type === 'info') {
                lnaccDosMessageDiv.classList.add('text-gray-600');
            }
        }
    }

    function updateProcessButtonState() {
        // Enable button only if files are selected and a branch is chosen
        processLnaccDosButton.disabled = !(lnaccDosInputFiles.files.length > 0 && lnaccDosBranch.value !== '');
    }

    /**
     * Shows the custom logo loading animation.
     */
    function showLogoAnimation() {
        if (lnaccDosLoadingOverlay) {
            lnaccDosLoadingOverlay.classList.add('active');
            document.body.style.overflow = 'hidden'; // Prevent scrolling
        }
    }

    /**
     * Hides the custom logo loading animation.
     */
    function hideLogoAnimation() {
        if (lnaccDosLoadingOverlay) {
            lnaccDosLoadingOverlay.classList.remove('active');
            document.body.style.overflow = ''; // Restore scrolling
        }
    }

    // Attach event listeners only once
    lnaccDosInputFiles.addEventListener('change', function() {
        const files = this.files;
        if (files.length > 0) {
            let fileNames = Array.from(files).map(file => file.name).join(', ');
            lnaccDosFilesDisplay.textContent = `Selected Files: ${fileNames}`;
        } else {
            lnaccDosFilesDisplay.textContent = 'No files selected.';
        }
        updateProcessButtonState();
    });

    lnaccDosBranch.addEventListener('change', updateProcessButtonState);

    // Use a flag to prevent multiple submissions if the button is clicked rapidly
    let isProcessing = false; 

    processLnaccDosButton.addEventListener('click', async function() {
        if (isProcessing) { // Prevent multiple clicks while processing
            return;
        }

        const files = lnaccDosInputFiles.files;
        const branch = lnaccDosBranch.value;

        // --- DEBUG LOGGING ---
        console.log('LNACC DOS Frontend: Files selected count:', files.length);
        console.log('LNACC DOS Frontend: Branch value before sending:', branch);
        // --- END DEBUG LOGGING ---

        if (files.length === 0) {
            displayLnaccDosMessage('Please select DBF/CSV/XLSX files to process.', 'error');
            return;
        }
        if (!branch) {
            displayLnaccDosMessage('Please select a branch.', 'error');
            return;
        }

        isProcessing = true; // Set flag to true
        processLnaccDosButton.disabled = true;
        processLnaccDosButton.textContent = 'Processing...';
        showLogoAnimation();
        displayLnaccDosMessage('Processing files... This may take a moment.', 'loading');

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }
        formData.append('branch', branch);

        try {
            const response = await fetch(`${window.FLASK_API_BASE_URL}/process_lnacc_dos`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                displayLnaccDosMessage(result.message, 'success');
                lnaccDosInputFiles.value = '';
                lnaccDosFilesDisplay.textContent = 'No files selected.';
                lnaccDosBranch.value = '';
            } else {
                displayLnaccDosMessage(result.error || 'An unknown error occurred.', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            displayLnaccDosMessage('Network error or server is unreachable.', 'error');
        } finally {
            isProcessing = false; // Reset flag
            processLnaccDosButton.disabled = false;
            processLnaccDosButton.textContent = 'Process LNACC DOS Files';
            hideLogoAnimation();
            updateProcessButtonState();
        }
    });

    // Initial state check and clear message
    updateProcessButtonState();
    displayLnaccDosMessage('', 'info'); // Clear message on initial load
});
    