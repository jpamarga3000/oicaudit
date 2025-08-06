// js/tabs/admin_set.js

// This script handles the functionality for the Admin Settings (adminSet.php) page.

document.addEventListener('DOMContentLoaded', function() {
    // Register the initializer for the 'adminSet' tab
    window.registerTabInitializer('adminSet', initializeAdminSetTab);

    // Get references to the toggle buttons and message div
    const toggleBiometricLogin = document.getElementById('toggleBiometricLogin');
    const toggleOtpVerification = document.getElementById('toggleOtpVerification');
    const saveAdminSettingsBtn = document.getElementById('saveAdminSettingsBtn');
    const adminSetMessageDiv = document.getElementById('adminSetMessage'); // Inline message box for this specific tab
    const adminSettingsContent = document.getElementById('adminSettingsContent'); // Reference to the content wrapper

    // NEW: Reference to the Access Denied Modal elements
    const accessDeniedModal = document.getElementById('accessDeniedModal');
    const accessDeniedMessageDiv = document.getElementById('accessDeniedMessage'); // Message inside the modal
    const closeAccessDeniedModalBtn = document.getElementById('closeAccessDeniedModalBtn');


    // Function to initialize the Admin Settings tab
    function initializeAdminSetTab() {
        console.log("Initializing Admin Settings tab...");
        // Ensure access denied modal is hidden initially
        if (accessDeniedModal) {
            accessDeniedModal.style.display = 'none';
        }
        // Hide content immediately when the tab is initialized
        if (adminSettingsContent) {
            adminSettingsContent.classList.add('hidden');
        }
        
        // Frontend check for access code (soft check for immediate UI feedback)
        const userAccessCode = window.userAccessCode || ''; // Get from global variable set by PHP
        console.log(`DEBUG admin_set.js: userAccessCode from PHP: '${userAccessCode}'`);

        if (userAccessCode !== 'AH') {
            console.log("DEBUG admin_set.js: Frontend check failed. User is not AH. Displaying access denied modal immediately.");
            showAdminSetMessage('Only Admin can access this page.', 'access-denied-modal');
            disableSettingsControls(); // Disable controls
            adminSettingsContent.classList.add('hidden'); // Ensure content stays hidden
            return; // Stop further initialization if unauthorized
        } else {
            console.log("DEBUG admin_set.js: Frontend check passed. User is AH. Proceeding to fetch settings.");
        }

        // If frontend check passes, proceed with fetching settings from backend
        fetchAndDisplayLoginSettings();

        // Attach event listener to the Save Settings button
        if (saveAdminSettingsBtn) {
            saveAdminSettingsBtn.addEventListener('click', saveLoginSettings);
        }

        // NEW: Attach event listener to close the access denied modal
        if (closeAccessDeniedModalBtn) {
            closeAccessDeniedModalBtn.addEventListener('click', () => {
                if (accessDeniedModal) accessDeniedModal.style.display = 'none';
            });
        }
    }

    // Helper function to display messages within the admin_set tab or a modal
    function showAdminSetMessage(text, type, duration = 5000) {
        console.log(`DEBUG admin_set.js: showAdminSetMessage called with type: '${type}' and text: '${text}'`);
        // If it's an access denied message, use the modal
        if (type === 'access-denied-modal') {
            if (accessDeniedModal && accessDeniedMessageDiv) {
                accessDeniedMessageDiv.textContent = text;
                accessDeniedModal.style.display = 'flex'; // Show the modal
                // No timeout for modal messages, they stay until closed
            } else {
                console.error("DEBUG admin_set.js: Error: Access Denied Modal elements not found. Fallback to inline message.");
                // Fallback to inline message if modal not available
                if (adminSetMessageDiv) {
                    adminSetMessageDiv.textContent = text;
                    adminSetMessageDiv.className = `message-box error`;
                    adminSetMessageDiv.style.display = 'block';
                    adminSetMessageDiv.style.opacity = '1';
                }
            }
            return; // Exit after handling modal message
        }

        // For other message types, use the inline message box
        if (!adminSetMessageDiv) {
            console.error("DEBUG admin_set.js: Error: Admin Set Message div not found.");
            return;
        }
        adminSetMessageDiv.textContent = text;
        adminSetMessageDiv.className = `message-box ${type}`;
        adminSetMessageDiv.style.display = 'block';
        adminSetMessageDiv.style.opacity = '1';

        if (duration > 0) {
            setTimeout(() => {
                adminSetMessageDiv.style.opacity = '0';
                setTimeout(() => {
                    adminSetMessageDiv.style.display = 'none';
                    adminSetMessageDiv.textContent = '';
                }, 300);
            }, duration);
        }
    }

    // Function to disable all controls on the settings page
    function disableSettingsControls() {
        console.log("DEBUG admin_set.js: Disabling settings controls.");
        if (toggleBiometricLogin) toggleBiometricLogin.disabled = true;
        if (toggleOtpVerification) toggleOtpVerification.disabled = true;
        if (saveAdminSettingsBtn) saveAdminSettingsBtn.disabled = true;
    }

    // Function to enable all controls on the settings page
    function enableSettingsControls() {
        console.log("DEBUG admin_set.js: Enabling settings controls.");
        if (toggleBiometricLogin) toggleBiometricLogin.disabled = false;
        if (toggleOtpVerification) toggleOtpVerification.disabled = false;
        if (saveAdminSettingsBtn) saveAdminSettingsBtn.disabled = false;
    }


    // Function to fetch current login settings from the backend
    async function fetchAndDisplayLoginSettings() {
        if (!toggleBiometricLogin || !toggleOtpVerification || !adminSettingsContent) {
            console.error("DEBUG admin_set.js: Admin settings elements not fully found before fetch.");
            return;
        }

        // Hide any previous inline messages
        if (adminSetMessageDiv) {
            adminSetMessageDiv.style.display = 'none';
        }
        showAdminSetMessage('Loading settings...', 'info', 0); // Show loading message

        try {
            const response = await fetch(`${window.FLASK_API_BASE_URL}/admin/login_settings`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'
            });
            const settings = await response.json();

            // Log the full response and settings for debugging
            console.log("DEBUG admin_set.js: API Response Status:", response.status);
            console.log("DEBUG admin_set.js: API Response OK:", response.ok);
            console.log("DEBUG admin_set.js: Parsed settings.success:", settings.success);
            console.log("DEBUG admin_set.js: Parsed settings object:", settings);


            if (response.ok && settings.success) {
                console.log("DEBUG admin_set.js: API call successful and settings.success is true. Showing content.");
                toggleBiometricLogin.checked = settings.biometric_login_enabled;
                toggleOtpVerification.checked = settings.otp_verification_enabled;
                showAdminSetMessage('Login settings loaded successfully.', 'success');
                enableSettingsControls(); // Ensure controls are enabled if access is granted
                adminSettingsContent.classList.remove('hidden'); // Show the content
                if (accessDeniedModal) accessDeniedModal.style.display = 'none'; // Ensure modal is hidden
            } else if (response.status === 401 || response.status === 403 || (settings.success !== undefined && !settings.success)) {
                console.log("DEBUG admin_set.js: API call indicated access denied (401/403 or settings.success is false). Showing modal.");
                showAdminSetMessage(settings.message || 'Only Admin can access this page.', 'access-denied-modal'); // Use new modal type
                disableSettingsControls(); // Disable controls if access is denied
                adminSettingsContent.classList.add('hidden'); // Ensure content remains hidden
            }
            else {
                console.log("DEBUG admin_set.js: API call resulted in unexpected error. Showing error message.");
                // Catch-all for other non-ok responses or unexpected data
                showAdminSetMessage(settings.message || 'Failed to load login settings due to an unexpected error.', 'error');
                // Default to checked if loading fails, to be safe
                toggleBiometricLogin.checked = true;
                toggleOtpVerification.checked = true;
                disableSettingsControls(); // Disable controls on other errors
                adminSettingsContent.classList.add('hidden'); // Ensure content remains hidden
            }
        } catch (error) {
            console.error("DEBUG admin_set.js: Error fetching login settings (network/parse error):", error);
            showAdminSetMessage('Network error or server unreachable while loading settings.', 'error');
            // Default to checked if network error
            toggleBiometricLogin.checked = true;
            toggleOtpVerification.checked = true;
            disableSettingsControls(); // Disable controls on network errors
            adminSettingsContent.classList.add('hidden'); // Ensure content remains hidden
        }
    }

    // Function to save login settings to the backend
    async function saveLoginSettings() {
        if (!toggleBiometricLogin || !toggleOtpVerification) {
            console.error("DEBUG admin_set.js: Admin settings toggle elements not found for saving.");
            showAdminSetMessage('Error: Toggle elements not found.', 'error');
            return;
        }

        const settingsData = {
            biometric_login_enabled: toggleBiometricLogin.checked,
            otp_verification_enabled: toggleOtpVerification.checked
        };

        showAdminSetMessage('Saving settings...', 'info', 0); // Show loading message

        try {
            const response = await fetch(`${window.FLASK_API_BASE_URL}/admin/login_settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settingsData),
                credentials: 'include'
            });
            const result = await response.json();

            if (response.ok && result.success) {
                showAdminSetMessage('Login settings saved successfully!', 'success');
            } else if (response.status === 401 || response.status === 403 || (result.success !== undefined && !result.success)) {
                console.log("DEBUG admin_set.js: API POST call indicated access denied (401/403 or result.success is false). Showing modal.");
                // If response status is 401/403 OR if result.success is explicitly false (server-side denial)
                showAdminSetMessage(result.message || 'Only Admin can access this page. Settings not saved.', 'access-denied-modal');
                disableSettingsControls();
                adminSettingsContent.classList.add('hidden'); // Ensure content remains hidden
            } else {
                console.log("DEBUG admin_set.js: API POST call resulted in unexpected error. Showing error message.");
                showAdminSetMessage(result.message || 'Failed to save login settings.', 'error');
            }
        } catch (error) {
            console.error("DEBUG admin_set.js: Error saving login settings (network/parse error):", error);
            showAdminSetMessage('Network error or server unreachable while saving settings.', 'error');
        }
    }
});
