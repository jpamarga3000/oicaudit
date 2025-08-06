// js/tabs/login.js

// Helper function to convert base64url to ArrayBuffer
function base64urlToArrayBuffer(base64url) {
    // Convert base64url to base64
    const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
    // Pad out with '=' until it is a multiple of 4
    const pad = base64.length % 4;
    const paddedBase64 = pad ? base64 + '===='.slice(0, 4 - pad) : base64;
    
    // Decode base64 to binary string, then convert to ArrayBuffer
    const binary_string = window.atob(paddedBase64);
    const len = binary_string.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binary_string.charCodeAt(i);
    }
    return bytes.buffer;
}

// Helper function to convert ArrayBuffer to base64url
function arrayBufferToBase64url(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}


document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username'); // Get username input
    const passwordInput = document.getElementById('password'); // Get password input
    const messageDiv = document.getElementById('message'); // Main message box
    const loadingOverlay = document.getElementById('loadingOverlay'); // Loading overlay

    // OTP Modal elements
    const otpModal = document.getElementById('otpModal');
    const otpInputs = document.querySelectorAll('.otp-input');
    const verifyOtpBtn = document.getElementById('verifyOtpBtn');
    const resendOtpBtn = document.getElementById('resendOtpBtn');
    const otpMessageDiv = document.getElementById('otpMessage'); // Message box inside OTP modal
    const maskedContactNumberDisplay = document.getElementById('maskedContactNumberDisplay'); // New element for masked number

    // Biometric Login elements
    const biometricOptionBtn = document.getElementById('biometricOptionBtn'); // The new biometric icon button
    const biometricModal = document.getElementById('biometricModal');
    const biometricMessageDiv = document.getElementById('biometricMessage');
    const cancelBiometricLoginBtn = document.getElementById('cancelBiometricLoginBtn');

    let currentUsername = ''; // To store username for OTP/Biometric verification
    let biometricEnrolledForCurrentUser = false; // Flag to track biometric enrollment status
    let biometricLoginEnabled = true; // NEW: Global setting for biometric login
    let otpVerificationEnabled = true; // NEW: Global setting for OTP verification

    // Function to display messages (re-using from utils.js, but local for clarity if utils.js isn't loaded first)
    // If utils.js is guaranteed to load first, you can remove this local definition.
    // For this context, assuming utils.js's showMessage is available globally via window.showMessage.
    function showMessage(text, type, duration = 5000, targetDiv = messageDiv) {
        if (!targetDiv) {
            console.error("Error: Message div not found in the DOM.");
            return;
        }
        targetDiv.textContent = text;
        targetDiv.className = `message-box ${type}`;
        targetDiv.style.display = 'block';
        targetDiv.style.opacity = '1'; // Ensure it's visible after setting display

        if (duration > 0) {
            setTimeout(() => {
                targetDiv.style.opacity = '0';
                setTimeout(() => {
                    targetDiv.style.display = 'none';
                    targetDiv.textContent = '';
                }, 300); // Allow fade out transition
            }, duration);
        }
    }

    // Function to show/hide loading overlay
    function showLoading() {
        if (loadingOverlay) loadingOverlay.style.display = 'flex';
    }

    function hideLoading() {
        if (loadingOverlay) loadingOverlay.style.display = 'none';
    }

    // Function to hide all modals
    function hideAllModals() {
        if (otpModal) otpModal.style.display = 'none';
        if (biometricModal) biometricModal.style.display = 'none';
    }

    // Function to update the state of the biometric option button
    function updateBiometricOptionButton() {
        if (biometricOptionBtn) {
            if (biometricLoginEnabled && biometricEnrolledForCurrentUser && window.PublicKeyCredential) {
                biometricOptionBtn.classList.remove('disabled');
                biometricOptionBtn.disabled = false;
                biometricOptionBtn.style.display = 'flex'; // Ensure it's visible
                // Only show this message if no other message is currently active (e.g., logout message)
                if (!messageDiv.classList.contains('active')) {
                    showMessage('Biometric login available. Enter credentials or click the icon.', 'info');
                }
            } else {
                biometricOptionBtn.classList.add('disabled');
                biometricOptionBtn.disabled = true;
                biometricOptionBtn.style.display = 'none'; // Hide if disabled by settings or not enrolled
                // Only show this message if no other message is currently active (e.g., logout message)
                if (!messageDiv.classList.contains('active')) {
                    showMessage('Biometric login not available or enrolled for this user/device.', 'info');
                }
            }
        }
    }

    // NEW: Function to fetch login settings from backend
    async function fetchLoginSettings() {
        try {
            const response = await fetch(`${window.FLASK_API_BASE_URL}/admin/login_settings`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'
            });
            const settings = await response.json();

            if (response.ok && settings.success) {
                biometricLoginEnabled = settings.biometric_login_enabled;
                otpVerificationEnabled = settings.otp_verification_enabled;
                console.log("Login settings fetched:", settings);
            } else {
                console.error("Failed to fetch login settings:", settings.message);
                // Default to true if fetch fails to ensure basic login functionality
                biometricLoginEnabled = true;
                otpVerificationEnabled = true;
            }
        } catch (error) {
            console.error("Error fetching login settings:", error);
            // Default to true if network error
            biometricLoginEnabled = true;
            otpVerificationEnabled = true;
        } finally {
            // After fetching settings, proceed with biometric status check and UI update
            checkBiometricStatusAndRenderLogin();
        }
    }


    // Check biometric status on page load
    async function checkBiometricStatusAndRenderLogin() {
        // Only proceed if biometric login is enabled by admin settings
        if (biometricLoginEnabled && window.PublicKeyCredential && navigator.credentials && navigator.credentials.get) {
            try {
                const rememberedUsername = localStorage.getItem('rememberedUsername');
                if (rememberedUsername) {
                    currentUsername = rememberedUsername; // Set currentUsername if remembered
                    // Use window.FLASK_API_BASE_URL for API calls
                    const response = await fetch(`${window.FLASK_API_BASE_URL}/get_biometric_status/${rememberedUsername}`, {
                        credentials: 'include'
                    });
                    const data = await response.json();
                    if (response.ok && data.is_enrolled) {
                        biometricEnrolledForCurrentUser = true;
                    }
                }
            } catch (error) {
                console.warn("Passive biometric check failed:", error);
                // Error during passive check, assume not enrolled or not supported for now.
            }
        } else {
            // If biometric login is disabled by settings, ensure flag is false
            biometricEnrolledForCurrentUser = false;
        }
        updateBiometricOptionButton(); // Update the button state based on the check and settings
    }

    // Function to check for and display logout messages from URL parameters
    function displayLogoutMessage() {
        const urlParams = new URLSearchParams(window.location.search);
        const logoutReason = urlParams.get('reason');
        const logoutMessage = urlParams.get('message'); // For a more generic message if needed

        if (logoutReason === 'inactivity') {
            showMessage('You have been logged out due to 10 minutes of inactivity.', 'logout-inactivity', 7000); // Display for 7 seconds
        } else if (logoutMessage) {
            // Generic message display if a 'message' parameter is passed
            showMessage(decodeURIComponent(logoutMessage), 'info', 5000);
        }
    }

    // Login Form Submission (Handles standard username/password login)
    if (loginForm) {
        loginForm.addEventListener('submit', async function(event) {
            event.preventDefault();

            const username = usernameInput.value;
            const password = passwordInput.value;

            if (!username || !password) {
                showMessage('Please enter both username and password.', 'error');
                return;
            }

            currentUsername = username; // Store username for subsequent steps (OTP/Biometric)

            showLoading(); // Show loading animation before fetch

            try {
                // Use window.FLASK_API_BASE_URL for API calls
                const response = await fetch(`${window.FLASK_API_BASE_URL}/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, password }),
                });

                const result = await response.json();

                hideLoading(); // Hide loading immediately after receiving a response

                if (response.ok) {
                    // Store username if login is successful (for future biometric attempts)
                    localStorage.setItem('rememberedUsername', username);

                    // Check otpVerificationEnabled setting before requiring OTP
                    if (otpVerificationEnabled && result.otp_required) {
                        // OTP is required (standard 2FA)
                        showMessage(result.message, 'info'); // "OTP sent. Please check your phone."
                        if (maskedContactNumberDisplay && result.masked_contact_number) {
                            maskedContactNumberDisplay.textContent = result.masked_contact_number;
                        }
                        showOtpModal();
                    } else {
                        // Direct login if OTP is not enabled or not required by backend
                        showMessage(result.message, 'success');
                        await setPhpSessionAndRedirect(result);
                    }
                    
                    // Update biometric status based on backend response and current settings
                    if (typeof result.biometric_enrolled !== 'undefined') {
                        biometricEnrolledForCurrentUser = result.biometric_enrolled;
                    }
                    updateBiometricOptionButton(); // Update button state
                } else {
                    showMessage(result.message || 'Login failed. Please try again.', 'error');
                    biometricEnrolledForCurrentUser = false; // Assume biometric not enrolled on failed login
                    updateBiometricOptionButton(); // Update button state
                }
            } catch (error) {
                console.error('Error during login fetch:', error);
                showMessage('An error occurred. Please check your network connection and try again.', 'error');
                hideLoading();
                biometricEnrolledForCurrentUser = false; // Assume biometric not enrolled on network error
                updateBiometricOptionButton(); // Update button state
            }
        });
    }

    // Biometric Option Button Click
    if (biometricOptionBtn) {
        biometricOptionBtn.addEventListener('click', function() {
            // Only allow click if biometric login is enabled by admin settings
            if (!biometricOptionBtn.disabled && biometricLoginEnabled) {
                // If username is not entered in the form, try to use remembered username
                if (!usernameInput.value) {
                    const rememberedUsername = localStorage.getItem('rememberedUsername');
                    if (rememberedUsername) {
                        currentUsername = rememberedUsername;
                    } else {
                        showMessage('Please enter your username first to use biometric login.', 'error');
                        return;
                    }
                } else {
                    currentUsername = usernameInput.value; // Use the username from the form
                }

                hideAllModals(); // Hide any other modals if open
                showBiometricModal();
                triggerBiometricLogin();
            } else {
                showMessage('Biometric login is not available for this user or device (disabled by admin settings or not enrolled).', 'info');
            }
        });
    }

    // Cancel Biometric Login Button
    if (cancelBiometricLoginBtn) {
        cancelBiometricLoginBtn.addEventListener('click', function() {
            hideBiometricModal();
            showMessage('Biometric login cancelled. You can try standard login or re-attempt biometric login.', 'info');
        });
    }

    // --- WebAuthn (Biometric) Login Flow ---
    async function triggerBiometricLogin() {
        const username = currentUsername; // Use the stored username

        if (!username) {
            showMessage('Username is required for biometric login.', 'error', 0, biometricMessageDiv);
            hideBiometricModal();
            return;
        }
        // Also check global setting here
        if (!biometricLoginEnabled) {
            showMessage('Biometric login is currently disabled by admin settings.', 'error', 0, biometricMessageDiv);
            hideBiometricModal();
            return;
        }
        if (!window.PublicKeyCredential) {
            showMessage('Biometric authentication is not supported on this device or browser.', 'error', 0, biometricMessageDiv);
            hideBiometricModal();
            return;
        }

        showMessage('Please approve the biometric prompt on your device...', 'info', 0, biometricMessageDiv);
        showLoading(); // Show loading during biometric prompt

        try {
            // Step 1: Get WebAuthn authentication options from the backend
            // Use window.FLASK_API_BASE_URL for API calls
            const optionsResponse = await fetch(`${window.FLASK_API_BASE_URL}/webauthn/login/begin`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username }),
                credentials: 'include'
            });
            const options = await optionsResponse.json();

            if (!optionsResponse.ok) {
                throw new Error(options.message || 'Failed to get authentication options from backend.');
            }

            // Convert base64url to ArrayBuffer for WebAuthn API
            options.challenge = base64urlToArrayBuffer(options.challenge);
            options.allowCredentials.forEach(cred => {
                cred.id = base64urlToArrayBuffer(cred.id);
            });

            // IMPORTANT: Explicitly set rpId to "localhost" here to match the backend's RELYING_PARTY_ID.
            // This is crucial for SecurityError: Invalid domain.
            options.rpId = "localhost"; // Hardcode to "localhost" to match backend

            // Step 2: Get a credential from the user's device using WebAuthn API
            const credential = await navigator.credentials.get({
                publicKey: options
            });

            // Step 3: Send the credential assertion to the backend for verification
            const authenticatorData = arrayBufferToBase64url(credential.response.authenticatorData);
            const clientDataJSON = arrayBufferToBase64url(credential.response.clientDataJSON);
            const signature = arrayBufferToBase64url(credential.response.signature);
            const userHandle = credential.response.userHandle ? arrayBufferToBase64url(credential.response.userHandle) : null;
            const rawId = arrayBufferToBase64url(credential.rawId);


            // Use window.FLASK_API_BASE_URL for API calls
            const verificationResponse = await fetch(`${window.FLASK_API_BASE_URL}/webauthn/login/complete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: username,
                    id: credential.id,
                    rawId: rawId,
                    type: credential.type,
                    response: {
                        authenticatorData: authenticatorData,
                        clientDataJSON: clientDataJSON,
                        signature: signature,
                        userHandle: userHandle
                    }
                }),
                credentials: 'include'
            });
            const verificationResult = await verificationResponse.json();

            if (verificationResponse.ok && verificationResult.success) {
                showMessage('Biometric login successful!', 'success', 5000, messageDiv);
                hideBiometricModal();
                await setPhpSessionAndRedirect(verificationResult);
            } else {
                throw new Error(verificationResult.message || 'Biometric login failed.');
            }
        } catch (error) {
            console.error("Biometric login error:", error);
            showMessage('Biometric login failed: ' + error.message, 'error', 5000, biometricMessageDiv);
        } finally {
            hideLoading();
        }
    }

    // OTP Modal Functions
    function showOtpModal() {
        if (otpModal) {
            otpModal.style.display = 'flex';
            if (otpInputs.length > 0) {
                otpInputs[0].focus();
            }
            otpInputs.forEach(input => input.value = '');
            showMessage('', '', 0, otpMessageDiv);
        }
    }

    function hideOtpModal() {
        if (otpModal) {
            otpModal.style.display = 'none';
        }
    }

    // Biometric Modal Functions
    function showBiometricModal() {
        if (biometricModal) {
            biometricModal.style.display = 'flex';
            showMessage('', '', 0, biometricMessageDiv); // Clear biometric modal message
        }
    }

    function hideBiometricModal() {
        if (biometricModal) {
            biometricModal.style.display = 'none';
        }
    }

    // Handle OTP input navigation
    otpInputs.forEach((input, index) => {
        input.addEventListener('input', () => {
            if (input.value.length === 1 && index < otpInputs.length - 1) {
                otpInputs[index + 1].focus();
            }
            validateOtpInputs();
        });

        input.addEventListener('keydown', (event) => {
            if (event.key === 'Backspace' && input.value.length === 0 && index > 0) {
                otpInputs[index - 1].focus();
            }
        });
    });

    // Validate if all OTP inputs are filled
    function validateOtpInputs() {
        const allFilled = Array.from(otpInputs).every(input => input.value.length === 1);
        if (verifyOtpBtn) {
            verifyOtpBtn.disabled = !allFilled;
        }
    }

    // Initial validation on load
    if (verifyOtpBtn) {
        validateOtpInputs();
    }

    // Verify OTP Button Click
    if (verifyOtpBtn) {
        verifyOtpBtn.addEventListener('click', async function() {
            const otpCode = Array.from(otpInputs).map(input => input.value).join('');

            if (otpCode.length !== 6) {
                showMessage('Please enter the full 6-digit OTP.', 'error', 5000, otpMessageDiv);
                return;
            }

            showLoading();

            try {
                // Use window.FLASK_API_BASE_URL for API calls
                const response = await fetch(`${window.FLASK_API_BASE_URL}/verify_otp`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username: currentUsername, otp: otpCode }),
                });

                const result = await response.json();

                if (response.ok) {
                    showMessage(result.message, 'success', 5000, otpMessageDiv);
                    hideOtpModal();
                    await setPhpSessionAndRedirect(result);
                } else {
                    showMessage(result.message || 'OTP verification failed.', 'error', 5000, otpMessageDiv);
                }
            } catch (error) {
                console.error('Error during OTP verification fetch:', error);
                showMessage('An error occurred during OTP verification. Try again.', 'error', 5000, otpMessageDiv);
            } finally {
                hideLoading();
            }
        });
    }

    // Resend OTP Button Click
    if (resendOtpBtn) {
        resendOtpBtn.addEventListener('click', async function() {
            showLoading();

            try {
                // Use window.FLASK_API_BASE_URL for API calls
                const response = await fetch(`${window.FLASK_API_BASE_URL}/resend_otp`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username: currentUsername }),
                });

                const result = await response.json();

                hideLoading();

                if (response.ok) {
                    showMessage(result.message, 'info', 5000, otpMessageDiv);
                    if (maskedContactNumberDisplay && result.masked_contact_number) {
                        maskedContactNumberDisplay.textContent = result.masked_contact_number;
                    }
                } else {
                    showMessage(result.message || 'Failed to resend OTP.', 'error', 5000, otpMessageDiv);
                }
            } catch (error) {
                console.error('Error during resend OTP fetch:', error);
                showMessage('An error occurred while trying to resend OTP. Try again.', 'error', 5000, otpMessageDiv);
                hideLoading();
            }
        });
    }

    // Helper to set PHP session and redirect
    async function setPhpSessionAndRedirect(flaskResult) {
        try {
            const setSessionResponse = await fetch('set_session.php', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    loggedin: 'true',
                    firstName: flaskResult.first_name,
                    lastName: flaskResult.last_name,
                    contactNumber: flaskResult.contact_number,
                    birthdate: flaskResult.birthdate,
                    email: flaskResult.email,
                    username: flaskResult.username,
                    approvedStatus: flaskResult.approved_status,
                    accessCode: flaskResult.access_code, // Pass accessCode to PHP session
                    branch: flaskResult.branch
                }).toString(),
            });
            const setSessionResult = await setSessionResponse.json();
            if (setSessionResult.success) {
                window.location.href = 'index.php';
            } else {
                console.error('Error setting PHP session:', setSessionResult.message);
                showMessage('Login successful, but failed to set session. Please try again.', 'error', 5000, messageDiv);
            }
        } catch (sessionError) {
            console.error('Error during set_session.php fetch:', sessionError);
            showMessage('Login successful, but failed to set session due to network error.', 'error', 5000, messageDiv);
        }
    }

    // Initial checks and rendering when the page loads
    fetchLoginSettings(); // NEW: Fetch settings first
    displayLogoutMessage(); // Call this function to check for and display logout messages
});
