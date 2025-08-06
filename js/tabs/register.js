// audit_tool/js/tabs/register.js

document.addEventListener('DOMContentLoaded', function() {
    // Get the registration form element
    const registerForm = document.getElementById('registerForm');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword'); // Assuming you add this ID to your Confirm Password input
    const passwordMatchMessage = document.getElementById('passwordMatchMessage'); // Message for password match
    const passwordRequirements = document.getElementById('passwordRequirements'); // Container for strength requirements

    // Elements for individual password requirements (assuming you add these IDs in your HTML)
    const minLength = document.getElementById('minLength');
    const alphanumeric = document.getElementById('alphanumeric');
    const oneSymbol = document.getElementById('oneSymbol');

    // Get loading overlay element
    const loadingOverlay = document.getElementById('loadingOverlay'); // Assuming you add this ID to your loading overlay div

    // Check if the form exists on the page
    if (registerForm) {
        // Add event listeners for real-time password validation
        if (passwordInput) {
            passwordInput.addEventListener('keyup', validatePassword);
            passwordInput.addEventListener('focus', () => {
                if (passwordRequirements) passwordRequirements.style.display = 'block';
            });
            passwordInput.addEventListener('blur', () => {
                // Hide requirements only if password is valid or empty, otherwise keep showing if invalid
                if (passwordRequirements && validatePassword()) { // Only hide if valid
                    passwordRequirements.style.display = 'none';
                }
                // Also re-validate on blur to ensure the final state is correct if user tabs away
                validatePassword(); // Call without isSubmission=true to prevent messageBox from showing
            });
        }
        if (confirmPasswordInput) {
            confirmPasswordInput.addEventListener('keyup', validatePassword);
            confirmPasswordInput.addEventListener('blur', validatePassword); // Re-validate on blur
        }


        registerForm.addEventListener('submit', async function(event) {
            event.preventDefault(); // Prevent default form submission

            // Collect form data
            const firstName = document.getElementById('firstName').value;
            const lastName = document.getElementById('lastName').value;
            const contactNumber = document.getElementById('contactNumber').value;
            const birthdate = document.getElementById('birthdate').value; // Format: mm/dd/yyyy
            const email = document.getElementById('email').value;
            const username = document.getElementById('username').value;
            const password = passwordInput.value; // Get value from the input element
            const confirmPassword = confirmPasswordInput ? confirmPasswordInput.value : ''; // Get value from confirm input

            // Basic client-side validation for required fields
            if (!firstName || !lastName || !username || !password) {
                showMessage('Please fill in all required fields (First Name, Last Name, Username, Password).', 'error');
                return;
            }

            // Perform password validation on submission
            const isPasswordValidOnSubmit = validatePassword(true); // Pass true to potentially show general error

            if (!isPasswordValidOnSubmit) {
                // validatePassword(true) already shows the error message if needed
                return; // Stop submission if validation fails
            } else {
                // If password validation passes on submission, show a success message for it
                // This message will be quickly replaced by the server's response message
                showMessage('Password meets all requirements and matches confirmation.', 'success');
            }


            // Construct the data payload
            const formData = {
                firstName: firstName,
                lastName: lastName,
                contactNumber: contactNumber,
                birthdate: birthdate,
                email: email,
                username: username,
                password: password
            };

            console.log('Sending registration data:', formData); // Log data for debugging

            // Show loading overlay
            if (loadingOverlay) {
                loadingOverlay.style.display = 'flex'; // Use flex to center content
            }

            try {
                // Use window.FLASK_API_BASE_URL for the API endpoint
                const response = await fetch(window.FLASK_API_BASE_URL + '/register_user', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });

                const result = await response.json(); // Parse the JSON response

                if (response.ok) { // Check if the response status is 2xx
                    // Display the specific success message from the backend
                    alert(result.message); // Use alert as requested for this specific message

                    // Redirect to login page after successful registration
                    window.location.href = 'login.php'; // Redirect to login page
                } else {
                    // Handle server-side errors (e.g., username already exists, validation errors)
                    showMessage(result.message || 'Registration failed. Please try again.', 'error');
                }
            } catch (error) {
                console.error('Error during registration fetch:', error);
                showMessage('An error occurred. Please check your network connection and try again.', 'error');
            } finally {
                // Hide loading overlay regardless of success or failure
                if (loadingOverlay) {
                    loadingOverlay.style.display = 'none';
                }
            }
        });
    }

    // Helper function for password validation
    function validatePassword(isSubmission = false) {
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput ? confirmPasswordInput.value : '';
        let isValid = true;

        // Check password length
        const isMinLength = password.length >= 8;
        if (minLength) minLength.className = isMinLength ? 'valid' : 'invalid';
        if (!isMinLength) isValid = false;

        // Check for alphanumeric characters (letters and numbers)
        const isAlphanumeric = /[a-zA-Z]/.test(password) && /[0-9]/.test(password);
        if (alphanumeric) alphanumeric.className = isAlphanumeric ? 'valid' : 'invalid';
        if (!isAlphanumeric) isValid = false;

        // Check for at least one symbol (!@#$%^&*()_+-=[]{};':"|,.<>/?`~)
        const isOneSymbol = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(password);
        if (oneSymbol) oneSymbol.className = isOneSymbol ? 'valid' : 'invalid';
        if (!isOneSymbol) isValid = false;

        // Check if passwords match (only if confirmPasswordInput exists)
        if (confirmPasswordInput) {
            const passwordsMatch = (password === confirmPassword && password !== '');
            if (passwordMatchMessage) {
                if (passwordsMatch) {
                    passwordMatchMessage.textContent = 'Passwords match';
                    passwordMatchMessage.className = 'message-box valid';
                } else if (confirmPassword !== '') {
                    passwordMatchMessage.textContent = 'Passwords do not match';
                    passwordMatchMessage.className = 'message-box invalid';
                    isValid = false; // Passwords don't match, so overall validation fails
                } else {
                    passwordMatchMessage.textContent = ''; // Clear message if confirm is empty
                    passwordMatchMessage.className = '';
                }
            }
        }

        // Only show the general error message if it's a submission and not valid
        if (isSubmission && !isValid) {
            showMessage('Please ensure your password meets all requirements and matches the confirmation.', 'error');
        }

        return isValid;
    }

    // Helper function to display messages to the user
    function showMessage(message, type) {
        const messageBox = document.getElementById('messageBox'); // Assuming you have a div with id="messageBox" in your HTML
        if (messageBox) {
            messageBox.textContent = message;
            messageBox.className = `message-box ${type}`; // Add class for styling (e.g., 'success', 'error')
            messageBox.style.display = 'block'; // Make it visible

            // Hide after a few seconds
            setTimeout(() => {
                messageBox.style.display = 'none';
                messageBox.textContent = '';
            }, 5000);
        }
        // No alert() fallback here, as alert is used explicitly for the final success message
    }
});
