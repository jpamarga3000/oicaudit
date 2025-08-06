<?php
// This is login.php
// You might include a header file here if you have one for common elements
// include_once 'includes/header.php';

// Start session to check for logout messages
session_start();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audit Management System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Custom CSS for login form and OTP modal */
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f3f4f6; /* Light gray background */
        }
        /* The .container styles are now applied directly via Tailwind classes in the HTML */

        .form-field {
            margin-bottom: 1.5rem;
        }
        .form-field label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #4b5563;
        }
        .form-field input[type="text"],
        .form-field input[type="password"] {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        }
        .form-field input:focus {
            outline: none;
            border-color: #6366f1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }
        .message-box {
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 8px;
            font-weight: 500;
            text-align: center;
            display: none; /* Hidden by default, controlled by JS */
            opacity: 0;
            transition: opacity 0.3s ease-in-out;
        }
        .message-box.active {
            opacity: 1;
        }
        .message-box.success {
            background-color: #d1fae5;
            color: #065f46;
            border: 1px solid #34d399;
        }
        .message-box.error {
            background-color: #fee2e2;
            color: #991b1b;
            border: 1px solid #ef4444;
        }

        /* OTP Modal Specific Styles */
        .modal-overlay {
            display: none; /* Hidden by default */
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.6);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .modal-content {
            background: #ffffff;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
            text-align: center;
            max-width: 450px;
            width: 90%;
        }
        .otp-inputs {
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            margin-top: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .otp-inputs input {
            width: 45px; /* Adjust size for 6 boxes */
            height: 45px;
            text-align: center;
            font-size: 1.5rem;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            background-color: #f9fafb;
        }
        .otp-inputs input:focus {
            outline: none;
            border-color: #6366f1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }

        /* Loading Overlay CSS */
        #loadingOverlay {
            display: none; /* Hidden by default */
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1001; /* Higher z-index than modal */
            justify-content: center;
            align-items: center;
        }
        .spinner {
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-top: 4px solid #fff;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Biometric Modal Specific Styles */
        #biometricModal {
            display: none; /* Hidden by default */
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.6);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        #biometricModal .modal-content {
            /* Inherits most styles from .modal-content */
            max-width: 400px;
        }
        .biometric-icon-svg { /* Renamed from .biometric-icon to avoid conflict if any */
            font-size: 3rem;
            color: #6366f1;
            margin-bottom: 1rem;
        }
        /* New style for the biometric option button/icon */
        #biometricOptionBtn {
            background: none;
            border: none;
            padding: 0;
            margin-top: 1.5rem; /* Space below the login button */
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            color: #6366f1; /* Icon color */
            transition: color 0.2s ease-in-out, transform 0.2s ease-in-out;
            font-size: 0.9rem; /* Text size below icon */
            font-weight: 500;
        }
        #biometricOptionBtn:hover {
            color: #4338ca; /* Darker on hover */
            transform: translateY(-2px);
        }
        #biometricOptionBtn:active {
            transform: translateY(0);
        }
        #biometricOptionBtn.disabled {
            color: #9ca3af; /* Gray out when disabled */
            cursor: not-allowed;
        }
        #biometricOptionBtn svg {
            width: 3rem; /* Larger icon */
            height: 3rem;
            margin-bottom: 0.5rem;
        }
    </style>
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen">
    <div id="loadingOverlay">
        <div class="spinner"></div>
    </div>

    <div class="max-w-md w-full mx-auto my-12 p-8 bg-white rounded-xl shadow-lg">
        <div class="text-center mb-8">
            <img src="images/logo.png" alt="Company Logo" class="mx-auto h-24 w-auto">
        </div>
        <h2 class="text-3xl font-bold text-center text-gray-800 mb-8">Audit Management System</h2>
        
        <div id="message" class="message-box"></div>

        <form id="loginForm" class="space-y-6">
            <div class="form-field">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required class="rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500">
            </div>
            <div class="form-field">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required class="rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500">
            </div>
            <button type="submit" id="standardLoginBtn" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-opacity-50 transition duration-150 ease-in-out">
                Login
            </button>
            <!-- Biometric login option button - always visible, enabled/disabled by JS -->
            <div class="flex justify-center">
                <button type="button" id="biometricOptionBtn" class="focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-opacity-50 transition duration-150 ease-in-out">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="biometric-icon-svg">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M17.982 18.725A7.488 7.488 0 0 0 12 15.75a7.488 7.488 0 0 0-5.982 2.975m11.963 0a9 9 0 1 0-11.963 0m11.963 0A8.966 8.966 0 0 1 12 21a8.966 8.966 0 0 1-5.982-2.275M15 9.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                    </svg>
                    <span>Login with Biometrics</span>
                </button>
            </div>
            <p class="text-center text-gray-600 text-sm mt-4">
                Don't have an account? <a href="register.php" class="text-indigo-600 hover:text-indigo-800 font-medium">Register here</a>
            </p>
        </form>
    </div>

    <!-- OTP Modal -->
    <div id="otpModal" class="modal-overlay">
        <div class="modal-content">
            <h3 class="text-2xl font-bold text-gray-800 mb-4">Verify OTP</h3>
            <p class="text-gray-600 mb-4">A 6-digit OTP has been sent to <span id="maskedContactNumberDisplay" class="font-semibold text-gray-800"></span>.</p>
            <div class="otp-inputs">
                <input type="text" id="otp1" maxlength="1" class="otp-input rounded-lg" autocomplete="one-time-code">
                <input type="text" id="otp2" maxlength="1" class="otp-input rounded-lg">
                <input type="text" id="otp3" maxlength="1" class="otp-input rounded-lg">
                <input type="text" id="otp4" maxlength="1" class="otp-input rounded-lg">
                <input type="text" id="otp5" maxlength="1" class="otp-input rounded-lg">
                <input type="text" id="otp6" maxlength="1" class="otp-input rounded-lg">
            </div>
            <div id="otpMessage" class="message-box text-sm mt-2"></div>
            <button id="verifyOtpBtn" class="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-opacity-50 transition duration-150 ease-in-out mt-4">
                Verify OTP
            </button>
            <button id="resendOtpBtn" class="w-full bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-opacity-50 transition duration-150 ease-in-out mt-2">
                Resend OTP
            </button>
        </div>
    </div>

    <!-- Biometric Modal -->
    <div id="biometricModal" class="modal-overlay">
        <div class="modal-content">
            <h3 class="text-2xl font-bold text-gray-800 mb-4">Biometric Login</h3>
            <div class="biometric-icon-svg">
                <!-- You can use an SVG icon here for Face ID/Fingerprint -->
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-12 h-12 mx-auto">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M17.982 18.725A7.488 7.488 0 0 0 12 15.75a7.488 7.488 0 0 0-5.982 2.975m11.963 0a9 9 0 1 0-11.963 0m11.963 0A8.966 8.966 0 0 1 12 21a8.966 8.966 0 0 1-5.982-2.275M15 9.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                </svg>
            </div>
            <p class="text-gray-600 mb-4">Please use your device's biometric sensor (Face ID or Fingerprint) to log in.</p>
            <div id="biometricMessage" class="message-box text-sm mt-2"></div>
            <button id="cancelBiometricLoginBtn" class="w-full bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-opacity-50 transition duration-150 ease-in-out mt-4">
                Cancel
            </button>
        </div>
    </div>

    <script src="js/utils.js"></script>
    <script src="js/tabs/login.js"></script>
</body>
</html>
<?php
// You might include a footer file here if you have one
// include_once 'includes/footer.php';

// Clear the logout message from session after displaying it
if (isset($_SESSION['logout_message'])) {
    unset($_SESSION['logout_message']);
    unset($_SESSION['logout_message_type']);
}
?>
