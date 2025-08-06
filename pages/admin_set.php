<?php
// pages/admin_set.php
// This file contains the settings for login requirements.
?>
<div id="adminSet" class="dashboard-section hidden">
    <!-- NEW: Add a wrapper div for the content that should be hidden/shown -->
    <div id="adminSettingsContent" class="hidden"> 
        <h3 class="section-title">Login Requirements</h3>

        <div class="space-y-6">
            <!-- Biometric Login Toggle -->
            <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 shadow-sm">
                <label for="toggleBiometricLogin" class="text-lg font-medium text-gray-800 cursor-pointer">
                    Enable Biometric Login
                </label>
                <label class="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" value="" id="toggleBiometricLogin" class="sr-only peer">
                    <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
            </div>

            <!-- OTP Verification Toggle -->
            <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 shadow-sm">
                <label for="toggleOtpVerification" class="text-lg font-medium text-gray-800 cursor-pointer">
                    Enable OTP Verification
                </label>
                <label class="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" value="" id="toggleOtpVerification" class="sr-only peer">
                    <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
            </div>
        </div>

        <div class="mt-6 flex justify-end">
            <button id="saveAdminSettingsBtn" class="process-button">Save Settings</button>
        </div>
    </div>
    <div id="adminSetMessage" class="message-box mt-4"></div> <!-- Message div is now outside the content wrapper -->

    <!-- Access Denied Modal (Integrated directly into admin_set.php) -->
    <div id="accessDeniedModal" class="modal-overlay">
        <div class="modal-content">
            <h3 class="text-2xl font-bold text-red-700 mb-4 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8 mr-2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.38 3.375 2.07 3.375h14.006c1.69 0 2.936-1.875 2.07-3.375L13.106 3.374c-.866-1.5-3.377-1.5-4.243 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                </svg>
                Access Denied
            </h3>
            <p id="accessDeniedMessage" class="text-gray-700 mb-6">Only Admin can access this page.</p>
            <button id="closeAccessDeniedModalBtn" class="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50 transition duration-150 ease-in-out">
                Close
            </button>
        </div>
    </div>

</div>
