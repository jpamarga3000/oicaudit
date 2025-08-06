// audit_tool/js/tabs/admin_profile.js

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


// Ensure that this script runs only after the DOM is fully loaded and
// the main initializer (if any) is available.
if (window.registerTabInitializer) {
    // Register this tab's initializer with the main system.
    window.registerTabInitializer('adminProfile', function() {
        console.log("admin_profile.js: Initializing Admin Profile tab.");

        const profilePic = document.getElementById('profilePic');
        const uploadProfilePic = document.getElementById('uploadProfilePic');
        const editProfileButton = document.getElementById('editProfileButton');
        const saveProfileButton = document.getElementById('saveProfileButton');
        const cancelEditButton = document.getElementById('cancelEditButton');
        const profileMessage = document.getElementById('profileMessage');

        const profileFirstName = document.getElementById('profileFirstName');
        const profileLastName = document.getElementById('profileLastName');
        const profileContactNumber = document.getElementById('profileContactNumber');
        const profileBirthdate = document.getElementById('profileBirthdate');
        const profileEmail = document.getElementById('profileEmail');
        const profileUsername = document.getElementById('profileUsername'); // Readonly
        const profileBranch = document.getElementById('profileBranch'); // This field will now always be readonly/disabled

        // New biometric elements
        const biometricStatusSpan = document.getElementById('biometricStatus');
        const enrollBiometricsButton = document.getElementById('enrollBiometricsButton');

        // Store initial values for cancellation
        let initialProfileValues = {};

        // Helper function to display messages
        function showProfileMessage(message, type = 'info') {
            if (!profileMessage) return;
            profileMessage.textContent = message;
            profileMessage.className = `p-3 rounded-md mt-4 text-center ${type === 'error' ? 'bg-red-100 text-red-700' : type === 'success' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`;
            profileMessage.classList.remove('hidden');
            setTimeout(() => profileMessage.classList.add('hidden'), 5000);
        }

        // Function to toggle edit mode
        function toggleEditMode(isEditing) {
            const editableFields = [
                profileFirstName, profileLastName, profileContactNumber,
                profileBirthdate, profileEmail
            ];

            editableFields.forEach(field => {
                if (field) { // Ensure field exists before accessing its properties
                    field.readOnly = !isEditing;
                    field.classList.toggle('bg-gray-100', !isEditing); // Add gray background when readonly
                    field.classList.toggle('focus:shadow-outline', isEditing); // Add focus shadow when editable
                }
            });

            if (profileBranch) {
                profileBranch.classList.add('bg-gray-100'); // Ensure it always has the gray background
                profileBranch.readOnly = true; // Ensure it's always readonly
                profileBranch.disabled = true; // Ensure it's always disabled
            }

            if (editProfileButton) editProfileButton.classList.toggle('hidden', isEditing);
            if (saveProfileButton) saveProfileButton.classList.toggle('hidden', !isEditing);
            if (cancelEditButton) cancelEditButton.classList.toggle('hidden', !isEditing);
            // Ensure uploadProfilePic exists before accessing its closest label
            if (uploadProfilePic && uploadProfilePic.closest('label')) {
                uploadProfilePic.closest('label').classList.toggle('hidden', !isEditing); // Hide/show upload button
            }

            // Biometric button visibility (always visible, but might be disabled based on enrollment status)
            if (enrollBiometricsButton) {
                // The button is always visible, but its enabled state depends on biometric support and enrollment status.
                // We'll update its disabled state after checking biometric status.
            }
        }

        // Function to save current profile values as initial
        function saveInitialProfileValues() {
            initialProfileValues = {
                firstName: profileFirstName ? profileFirstName.value : '',
                lastName: profileLastName ? profileLastName.value : '',
                contactNumber: profileContactNumber ? profileContactNumber.value : '',
                birthdate: profileBirthdate ? profileBirthdate.value : '',
                email: profileEmail ? profileEmail.value : '',
            };
        }

        // Function to revert to initial values
        function revertProfileValues() {
            if (profileFirstName) profileFirstName.value = initialProfileValues.firstName;
            if (profileLastName) profileLastName.value = initialProfileValues.lastName;
            if (profileContactNumber) profileContactNumber.value = initialProfileValues.contactNumber;
            if (profileBirthdate) profileBirthdate.value = initialProfileValues.birthdate;
            if (profileEmail) profileEmail.value = initialProfileValues.email;
        }

        // Function to load profile picture on initialization
        async function loadProfilePicture() {
            const username = profileUsername ? profileUsername.value : '';
            if (!username) {
                console.warn("admin_profile.js: Username not available from profileUsername element to load profile picture. Using placeholder.");
                if (profilePic) {
                    profilePic.src = `https://placehold.co/160x160/cbd5e1/475569?text=Profile`;
                }
                return;
            }

            try {
                // Fetch the image URL for the profile picture from the backend
                const response = await fetch(`${window.FLASK_API_BASE_URL}/get_profile_picture/${username}`, {
                    credentials: 'include' // Important for sending session cookies
                });
                if (response.ok) {
                    const data = await response.json();
                    if (data.image_url) {
                        if (profilePic) {
                            profilePic.src = data.image_url + '?' + new Date().getTime(); // Add cache buster
                        }
                    } else {
                        if (profilePic) {
                            profilePic.src = `https://placehold.co/160x160/cbd5e1/475569?text=Profile`;
                        }
                    }
                } else {
                    console.warn("Failed to fetch profile picture status, using default. Status:", response.status);
                    if (profilePic) {
                        profilePic.src = `https://placehold.co/160x160/cbd5e1/475569?text=Profile`; // Fallback to default
                    }
                }
            } catch (error) {
                console.error("Error loading profile picture:", error);
                if (profilePic) {
                    profilePic.src = `https://placehold.co/160x160/cbd5e1/475569?text=Profile`; // Fallback to default
                }
            }
        }

        // --- New Biometric Functions ---

        // Function to check and update biometric status display
        async function updateBiometricStatus() {
            const username = profileUsername ? profileUsername.value : '';
            if (!username || !biometricStatusSpan || !enrollBiometricsButton) return;

            // Check if WebAuthn is supported by the browser/device
            if (!window.PublicKeyCredential) {
                biometricStatusSpan.textContent = "Not Supported (Device/Browser)";
                biometricStatusSpan.classList.remove('text-green-500', 'text-red-500');
                biometricStatusSpan.classList.add('text-gray-500');
                enrollBiometricsButton.disabled = true;
                return;
            }

            try {
                // Fetch current biometric enrollment status from backend
                const response = await fetch(`${window.FLASK_API_BASE_URL}/get_biometric_status/${username}`, {
                    credentials: 'include'
                });
                const data = await response.json();

                if (response.ok && data.is_enrolled) {
                    biometricStatusSpan.textContent = "Enrolled";
                    biometricStatusSpan.classList.remove('text-red-500', 'text-gray-500');
                    biometricStatusSpan.classList.add('text-green-500');
                    enrollBiometricsButton.textContent = "Re-enroll Biometrics"; // Option to re-enroll
                    enrollBiometricsButton.disabled = false; // Always allow re-enrollment
                } else {
                    biometricStatusSpan.textContent = "Not Enrolled";
                    biometricStatusSpan.classList.remove('text-green-500', 'text-gray-500');
                    biometricStatusSpan.classList.add('text-red-500');
                    enrollBiometricsButton.textContent = "Enroll Biometrics";
                    enrollBiometricsButton.disabled = false; // Enable enrollment button
                }
            } catch (error) {
                console.error("Error fetching biometric status:", error);
                biometricStatusSpan.textContent = "Error (Check Console)";
                biometricStatusSpan.classList.remove('text-green-500');
                biometricStatusSpan.classList.add('text-red-500');
                enrollBiometricsButton.disabled = true; // Disable on error
            }
        }

        // Function to enroll biometrics (Face ID/Fingerprint)
        async function enrollBiometrics() {
            const username = profileUsername ? profileUsername.value : '';
            if (!username) {
                showProfileMessage('Username not available. Cannot enroll biometrics.', 'error');
                return;
            }

            if (!window.PublicKeyCredential) {
                showProfileMessage('Biometric authentication is not supported on this device or browser.', 'error');
                return;
            }

            showProfileMessage('Initiating biometric enrollment...', 'info');
            enrollBiometricsButton.disabled = true;

            try {
                // Step 1: Get WebAuthn registration options from the backend
                const optionsResponse = await fetch(`${window.FLASK_API_BASE_URL}/webauthn/register/begin`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: username }),
                    credentials: 'include'
                });
                const options = await optionsResponse.json();

                if (!optionsResponse.ok) {
                    throw new Error(options.message || 'Failed to get registration options from backend.');
                }

                // Convert base64url to ArrayBuffer for WebAuthn API
                // Use the helper function for robust decoding
                options.challenge = base64urlToArrayBuffer(options.challenge);
                options.user.id = base64urlToArrayBuffer(options.user.id);
                if (options.excludeCredentials) {
                    options.excludeCredentials.forEach(cred => {
                        cred.id = base64urlToArrayBuffer(cred.id);
                    });
                }
                // Convert pubKeyCredParams algorithm from int to string if necessary (some browsers prefer string)
                if (options.pubKeyCredParams) {
                    options.pubKeyCredParams.forEach(param => {
                        if (typeof param.alg === 'number') {
                            param.alg = param.alg.toString();
                        }
                    });
                }

                // IMPORTANT: Dynamically set rp.id to ensure it matches the exact origin's hostname.
                // This is crucial for SecurityError: Invalid domain.
                // The rp.id should be the domain or IP, without protocol or port.
                options.rp.id = window.location.hostname; // Use the hostname from the current URL


                // Step 2: Create a new credential using WebAuthn API
                const credential = await navigator.credentials.create({
                    publicKey: options
                });

                // Step 3: Send the credential response to the backend for verification and storage
                // Convert ArrayBuffers to base64url strings for sending to backend
                const attestationObject = arrayBufferToBase64url(credential.response.attestationObject);
                const clientDataJSON = arrayBufferToBase64url(credential.response.clientDataJSON);
                const rawId = arrayBufferToBase64url(credential.rawId);


                const verificationResponse = await fetch(`${window.FLASK_API_BASE_URL}/webauthn/register/complete`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        username: username,
                        id: credential.id, // This is the credential ID (base64url)
                        rawId: rawId, // Raw credential ID (base64url)
                        type: credential.type,
                        response: {
                            clientDataJSON: clientDataJSON,
                            attestationObject: attestationObject
                        }
                    }),
                    credentials: 'include'
                });
                const verificationResult = await verificationResponse.json();

                if (verificationResponse.ok && verificationResult.success) {
                    showProfileMessage('Biometrics enrolled successfully!', 'success');
                } else {
                    throw new Error(verificationResult.message || 'Biometric enrollment failed.');
                }
            } catch (error) {
                console.error("Biometric enrollment error:", error);
                showProfileMessage('Biometric enrollment failed: ' + error.message, 'error');
            } finally {
                enrollBiometricsButton.disabled = false;
                updateBiometricStatus(); // Refresh status after attempt
            }
        }

        // Handle profile picture upload
        if (uploadProfilePic && profilePic) {
            uploadProfilePic.addEventListener('change', async function() {
                if (this.files && this.files[0]) {
                    const file = this.files[0];
                    const username = profileUsername ? profileUsername.value : '';

                    if (!username) {
                        showProfileMessage('Cannot upload photo: Username not available.', 'error');
                        return;
                    }

                    const reader = new FileReader();
                    reader.onload = function(e) {
                        if (profilePic) {
                            profilePic.src = e.target.result;
                        }
                    };
                    reader.readAsDataURL(file);

                    const formData = new FormData();
                    formData.append('profile_picture', file);
                    formData.append('username', username);

                    try {
                        const response = await fetch(`${window.FLASK_API_BASE_URL}/upload_profile_picture`, {
                            method: 'POST',
                            body: formData,
                            credentials: 'include'
                        });

                        const result = await response.json();
                        if (response.ok) {
                            showProfileMessage(result.message, 'success');
                            if (result.image_url) {
                                if (profilePic) {
                                    profilePic.src = result.image_url + '?' + new Date().getTime();
                                }
                            }
                        } else {
                            throw new Error(result.message || 'Failed to upload photo.');
                        }
                    } catch (error) {
                        console.error("Error uploading profile picture:", error);
                        showProfileMessage('Photo upload failed: ' + error.message, 'error');
                        loadProfilePicture();
                    }
                }
            });
        } else {
            console.warn("admin_profile.js: Profile picture elements not found.");
        }

        // Handle Save Profile Button Click
        if (saveProfileButton) {
            saveProfileButton.addEventListener('click', async function() {
                const username = profileUsername ? profileUsername.value : '';

                const profileData = {
                    'First Name': profileFirstName ? profileFirstName.value : '',
                    'Last Name': profileLastName ? profileLastName.value : '',
                    'Contact Number': profileContactNumber ? profileContactNumber.value : '',
                    'Birthdate': profileBirthdate ? profileBirthdate.value : '',
                    'Email': profileEmail ? profileEmail.value : '',
                    'Username': username,
                };

                try {
                    const response = await fetch(`${window.FLASK_API_BASE_URL}/update_user_profile`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(profileData),
                        credentials: 'include'
                    });

                    const result = await response.json();
                    if (response.ok) {
                        showProfileMessage(result.message, 'success');
                        toggleEditMode(false);
                        saveInitialProfileValues();
                    } else {
                        throw new Error(result.message || 'Failed to save profile.');
                    }
                } catch (error) {
                    console.error("Error saving profile:", error);
                    showProfileMessage('Failed to save profile: ' + error.message, 'error');
                }
            });
        } else {
            console.warn("admin_profile.js: Save profile button not found.");
        }

        // Handle Edit Profile Button Click
        if (editProfileButton) {
            editProfileButton.addEventListener('click', function() {
                saveInitialProfileValues();
                toggleEditMode(true);
                showProfileMessage('You can now edit your profile. Click Save Changes when done.', 'info');
            });
        }

        // Handle Cancel Edit Button Click
        if (cancelEditButton) {
            cancelEditButton.addEventListener('click', function() {
                revertProfileValues();
                toggleEditMode(false);
                showProfileMessage('Profile editing cancelled. Changes were not saved.', 'info');
            });
        }

        // Handle Enroll Biometrics Button Click
        if (enrollBiometricsButton) {
            enrollBiometricsButton.addEventListener('click', enrollBiometrics);
        }

        // Initial setup: load picture, set to read-only mode, and update biometric status
        loadProfilePicture();
        toggleEditMode(false);
        updateBiometricStatus(); // Check and display biometric status on load

        console.log("Admin Profile tab initialized.");
    });
} else {
    console.error("admin_profile.js: window.registerTabInitializer is not defined. Ensure main.js is loaded first.");
}
