// audit_tool/js/tabs/trnm_convert.js

if (window.registerTabInitializer) {
    window.registerTabInitializer('convert', function() {
        console.log("trnm_convert.js: Initializing TRNM Convert Tab.");

        const convertDbfForm = document.getElementById('convertDbfForm');
        const dbfFilesInput = document.getElementById('dbfFiles');
        const convertDbfFilesDisplay = document.getElementById('convertDbfFilesDisplay');
        const loadingOverlay = document.getElementById('loadingOverlay');
        const convertButton = document.getElementById('convertButton'); // The "Convert" button
        const downloadSection = document.getElementById('downloadSection'); // The div containing the download button
        const downloadConvertedFilesButton = document.getElementById('downloadConvertedFilesButton'); // The "Download" button

        let selectedDbfFiles = [];
        let temporaryOutputDirectoryPath = null; // To store the temporary directory path returned by the backend

        // Function to show loading animation
        function showLoadingAnimation() {
            if (loadingOverlay) {
                loadingOverlay.classList.remove('hidden');
                document.body.style.overflow = 'hidden'; // Prevent scrolling
            }
        }

        // Function to hide loading animation
        function hideLoadingAnimation() {
            if (loadingOverlay) {
                loadingOverlay.classList.add('hidden');
                document.body.style.overflow = ''; // Re-enable scrolling
            }
        }

        // Function to remove a file from the selected list
        const removeDbfFile = (indexToRemove) => {
            selectedDbfFiles.splice(indexToRemove, 1);
            window.renderSelectedFiles(selectedDbfFiles, 'convertDbfFilesDisplay', removeDbfFile);
            updateConvertButtonState();
        };

        // Update the state of the Convert button
        function updateConvertButtonState() {
            if (convertButton) {
                convertButton.disabled = selectedDbfFiles.length === 0;
            }
        }

        // Event listener for file input change
        if (dbfFilesInput) {
            dbfFilesInput.addEventListener('change', (event) => {
                selectedDbfFiles = Array.from(event.target.files);
                window.renderSelectedFiles(selectedDbfFiles, 'convertDbfFilesDisplay', removeDbfFile);
                updateConvertButtonState();
            });
        }

        // Event listener for form submission (Convert button click)
        if (convertDbfForm) {
            convertDbfForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                window.hideMessage(); // Hide any previous messages
                downloadSection.classList.add('hidden'); // Hide download section initially
                temporaryOutputDirectoryPath = null; // Clear any previous path

                if (selectedDbfFiles.length === 0) {
                    window.showMessage('Please select at least one DBF file.', 'error');
                    return;
                }

                showLoadingAnimation(); // Show loading animation
                convertButton.disabled = true; // Disable convert button during processing

                const formData = new FormData();
                selectedDbfFiles.forEach(file => {
                    formData.append('files', file);
                });
                // No need to send output_dir from frontend, backend creates temp dir

                try {
                    const response = await fetch(`${window.FLASK_API_BASE_URL}/process_convert_dbf`, {
                        method: 'POST',
                        body: formData,
                    });

                    const result = await response.json(); // Always expect JSON response from this endpoint

                    if (response.ok) {
                        if (result.output_path) {
                            temporaryOutputDirectoryPath = result.output_path; // Store the temporary directory path
                            downloadSection.classList.remove('hidden'); // Show the download section
                            window.showMessage(result.message || 'Conversion complete. Ready for download.', 'success');
                        } else {
                            window.showMessage(result.message || 'Conversion completed, but no files to download.', 'info');
                        }
                    } else {
                        window.showMessage(result.message || 'Server error during conversion.', 'error');
                    }
                } catch (error) {
                    console.error('Error during DBF conversion:', error);
                    window.showMessage(`An unexpected error occurred: ${error.message}. Please ensure the Flask backend is running and accessible.`, 'error');
                } finally {
                    hideLoadingAnimation(); // Hide loading animation
                    convertButton.disabled = false; // Re-enable convert button
                    updateConvertButtonState(); // Re-evaluate button state
                }
            });
        }

        // Event listener for the "Download Converted Files" button
        if (downloadConvertedFilesButton) {
            downloadConvertedFilesButton.addEventListener('click', async () => {
                if (!temporaryOutputDirectoryPath) {
                    window.showMessage('No files available for download. Please convert files first.', 'error');
                    return;
                }

                showLoadingAnimation(); // Show loading animation for download
                downloadConvertedFilesButton.disabled = true; // Disable download button

                const formData = new FormData();
                // Send the temporary directory path to the backend for download
                formData.append('output_path', temporaryOutputDirectoryPath); 

                try {
                    // Call the backend endpoint for actual download
                    const response = await fetch(`${window.FLASK_API_BASE_URL}/download_converted_dbf`, {
                        method: 'POST',
                        body: formData,
                    });

                    if (response.ok) {
                        const contentType = response.headers.get('Content-Type');
                        const contentDisposition = response.headers.get('Content-Disposition');
                        let filename = 'converted_files.zip'; // Default for multiple files or if not specified

                        if (contentDisposition) {
                            const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                            if (filenameMatch && filenameMatch[1]) {
                                filename = filenameMatch[1];
                            }
                        } else if (contentType && contentType.includes('text/csv')) {
                            // If it's a single CSV and no content-disposition, try to infer filename
                            // This is a fallback and ideally backend should always provide download_name
                            filename = selectedDbfFiles.length > 0 ? selectedDbfFiles[0].name.replace(/\.dbf$/i, '.csv') : 'converted_file.csv';
                        }

                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = filename;
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                        window.URL.revokeObjectURL(url);

                        window.showMessage('Files downloaded successfully! Cleaning up temporary files...', 'success');

                        // After successful download, send another request to delete temporary files
                        await fetch(`${window.FLASK_API_BASE_URL}/delete_temp_converted_dbf`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ output_path: temporaryOutputDirectoryPath }) // Send the directory path
                        });
                        console.log('Temporary files deletion request sent.');
                        temporaryOutputDirectoryPath = null; // Clear the path
                        downloadSection.classList.add('hidden'); // Hide download section
                        window.showMessage('Temporary files cleaned up.', 'success'); // Update message
                    } else {
                        const errorData = await response.json();
                        window.showMessage(errorData.message || 'Failed to download files.', 'error');
                    }
                } catch (error) {
                    console.error('Error during download:', error);
                    window.showMessage(`An unexpected error occurred during download: ${error.message}.`, 'error');
                } finally {
                    hideLoadingAnimation(); // Hide loading animation
                    downloadConvertedFilesButton.disabled = false; // Re-enable download button
                }
            });
        }

        // Initial state update
        updateConvertButtonState();
        downloadSection.classList.add('hidden'); // Ensure download section is hidden on load
    });
} else {
    console.error("trnm_convert.js: window.registerTabInitializer is not defined. Ensure main.js is loaded first.");
}
