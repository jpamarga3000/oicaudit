<?php
// This is register.php
// You might include a header file here if you have one for common elements
// include_once 'includes/header.php';
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register</title>
    <!-- Load Tailwind CSS from CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Custom CSS for validation feedback and messages */
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f3f4f6; /* Light gray background */
        }
        .container {
            max-width: 800px; /* Max width for the form */
            margin: 50px auto;
            padding: 20px;
            background-color: #ffffff;
            border-radius: 12px; /* Rounded corners */
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        .form-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr); /* Exactly 3 columns of equal width */
            gap: 1.5rem; /* Space between fields */
        }
        .form-field {
            display: flex;
            flex-direction: column;
        }
        .form-field label {
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #4b5563; /* Darker gray for labels */
        }
        .form-field input[type="text"],
        .form-field input[type="email"],
        .form-field input[type="password"],
        .form-field input[type="tel"],
        .form-field input[type="date"] {
            padding: 0.75rem;
            border: 1px solid #d1d5db;
            border-radius: 8px; /* Rounded corners for inputs */
            font-size: 1rem;
            transition: border-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        }
        .form-field input:focus {
            outline: none;
            border-color: #6366f1; /* Indigo focus color */
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2); /* Light indigo shadow */
        }

        /* Password requirements styling */
        #passwordRequirements {
            margin-top: 0.5rem;
            padding-left: 0.5rem;
            font-size: 0.875rem;
            color: #6b7280; /* Gray text */
        }
        #passwordRequirements ul {
            list-style: none; /* Remove default bullet points */
            padding: 0;
            margin: 0;
        }
        #passwordRequirements li {
            padding-left: 1.5rem;
            position: relative;
            line-height: 1.5;
        }
        #passwordRequirements li.valid:before {
            content: '✔'; /* Checkmark */
            color: #10b981; /* Green */
            position: absolute;
            left: 0;
        }
        #passwordRequirements li.invalid:before {
            content: '✖'; /* X mark */
            color: #ef4444; /* Red */
            position: absolute;
            left: 0;
        }

        /* Message box styling */
        .message-box {
            padding: 1rem;
            margin-top: 1rem;
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
            background-color: #d1fae5; /* Light green */
            color: #065f46; /* Dark green text */
            border: 1px solid #34d399;
        }
        .message-box.error {
            background-color: #fee2e2; /* Light red */
            color: #991b1b; /* Dark red text */
            border: 1px solid #ef4444;
        }
        .message-box.invalid { /* For password match message when it's invalid */
            background-color: #fee2e2;
            color: #991b1b;
            border: 1px solid #ef4444;
        }
        .message-box.valid { /* For password match message when it's valid */
            background-color: #d1fae5;
            color: #065f46;
            border: 1px solid #34d399;
        }

        /* Loading Overlay CSS */
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen">
    <!-- Loading Overlay HTML -->
    <div id="loadingOverlay" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.5); z-index: 1000; justify-content: center; align-items: center;">
        <div class="spinner" style="border: 4px solid rgba(255, 255, 255, 0.3); border-top: 4px solid #fff; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite;"></div>
    </div>

    <div class="container">
        <h2 class="text-3xl font-bold text-center text-gray-800 mb-8">Register</h2>
        
        <div id="messageBox" class="message-box"></div>

        <form id="registerForm" class="space-y-6">
            <div class="form-grid">
                <div class="form-field">
                    <label for="firstName">First Name:</label>
                    <input type="text" id="firstName" name="firstName" class="rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500" required>
                </div>
                <div class="form-field">
                    <label for="lastName">Last Name:</label>
                    <input type="text" id="lastName" name="lastName" class="rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500" required>
                </div>
                <div class="form-field">
                    <label for="contactNumber">Contact Number:</label>
                    <input type="tel" id="contactNumber" name="contactNumber" class="rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div class="form-field">
                    <label for="birthdate">Birthdate:</label>
                    <input type="date" id="birthdate" name="birthdate" class="rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div class="form-field">
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" class="rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div class="form-field">
                    <label for="username">Username:</label>
                    <input type="text" id="username" name="username" class="rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500" required>
                </div>
            </div>

            <div class="form-field">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" class="rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500" required>
                <div id="passwordRequirements" class="mt-2">
                    <ul>
                        <li id="minLength">At least 8 characters</li>
                        <li id="alphanumeric">Alphanumeric (letters and numbers)</li>
                        <li id="oneSymbol">At least one symbol (!@#$%^&*)</li>
                    </ul>
                </div>
            </div>

            <div class="form-field">
                <label for="confirmPassword">Confirm Password:</label>
                <input type="password" id="confirmPassword" name="confirmPassword" class="rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500" required>
                <div id="passwordMatchMessage" class="message-box text-sm mt-2"></div>
            </div>

            <button type="submit" class="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-opacity-50 transition duration-150 ease-in-out">
                Register
            </button>
            <p class="text-center text-gray-600 text-sm mt-4">
                Already have an account? <a href="login.php" class="text-indigo-600 hover:text-indigo-800 font-medium">Login here</a>
            </p>
        </form>
    </div>

    <!-- Include utils.js first to define window.FLASK_API_BASE_URL -->
    <script src="js/utils.js"></script>
    <!-- Then include register.js, which relies on FLASK_API_BASE_URL -->
    <script src="js/tabs/register.js"></script>
</body>
</html>
<?php
// You might include a footer file here if you have one
// include_once 'includes/footer.php';
?>
