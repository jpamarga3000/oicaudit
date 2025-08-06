<?php
// pages/operations_rest.php
// This content will be included in operations_main.php
?>
<div id="operationsRestructuredLoan" class="sub-tab-content hidden p-6 bg-white rounded-lg shadow-md">
    <h2 class="text-2xl font-bold text-gray-800 mb-6 text-center">Restructured Loans Report</h2>
    <p class="text-gray-600 mb-8 text-center">View summary and detailed information for restructured loans as of a specific date.</p>

    <div class="space-y-6 mb-8">
        <div class="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-4">
            <label for="restructuredDate" class="input-label">
                1. Select Date (MM/DD/YYYY):
            </label>
            <input type="date" id="restructuredDate" class="date-input p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500">
            <button id="generateRestructuredReportButton" class="process-button px-6 py-2 rounded-md transition duration-300" disabled>
                Generate Report
            </button>
        </div>
    </div>

    <div id="restructuredSummarySection" class="hidden">
        <h3 class="text-xl font-semibold text-gray-700 mb-4 text-center">Summary Balances</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div class="bg-blue-50 p-6 rounded-lg shadow-inner border border-blue-200">
                <h4 class="text-lg font-bold text-blue-800 mb-4 text-center">CURRENT ACCOUNTS</h4>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
                    <div class="p-3 bg-blue-100 rounded-md shadow-sm">
                        <p class="text-sm text-blue-700 font-medium">REMEDIAL</p>
                        <p id="summaryCurrentRemedial" class="text-xl font-bold text-blue-900">0.00</p>
                    </div>
                    <div class="p-3 bg-blue-100 rounded-md shadow-sm">
                        <p class="text-sm text-blue-700 font-medium">REGULAR</p>
                        <p id="summaryCurrentRegular" class="text-xl font-bold text-blue-900">0.00</p>
                    </div>
                    <div class="p-3 bg-blue-100 rounded-md shadow-sm">
                        <p class="text-sm text-blue-700 font-medium">BRL</p>
                        <p id="summaryCurrentBRL" class="text-xl font-bold text-blue-900">0.00</p>
                    </div>
                </div>
                <div class="mt-4 p-3 bg-blue-200 rounded-md shadow-sm text-center">
                    <p class="text-sm text-blue-800 font-bold">TOTAL CURRENT</p>
                    <p id="summaryCurrentTotal" class="text-2xl font-extrabold text-blue-900">0.00</p>
                </div>
            </div>

            <div class="bg-red-50 p-6 rounded-lg shadow-inner border border-red-200">
                <h4 class="text-lg font-bold text-red-800 mb-4 text-center">PAST DUE LOANS</h4>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
                    <div class="p-3 bg-red-100 rounded-md shadow-sm">
                        <p class="text-sm text-red-700 font-medium">REMEDIAL</p>
                        <p id="summaryPastDueRemedial" class="text-xl font-bold text-red-900">0.00</p>
                    </div>
                    <div class="p-3 bg-red-100 rounded-md shadow-sm">
                        <p class="text-sm text-red-700 font-medium">REGULAR</p>
                        <p id="summaryPastDueRegular" class="text-xl font-bold text-red-900">0.00</p>
                    </div>
                    <div class="p-3 bg-red-100 rounded-md shadow-sm">
                        <p class="text-sm text-red-700 font-medium">BRL</p>
                        <p id="summaryPastDueBRL" class="text-xl font-bold text-red-900">0.00</p>
                    </div>
                </div>
                <div class="mt-4 p-3 bg-red-200 rounded-md shadow-sm text-center">
                    <p class="text-sm text-red-800 font-bold">TOTAL PAST DUE</p>
                    <p id="summaryPastDueTotal" class="text-2xl font-extrabold text-red-900">0.00</p>
                </div>
            </div>
        </div>
    </div>

    <div id="restructuredDetailsSection" class="hidden">
        <h3 class="text-xl font-semibold text-gray-700 mb-4 text-center">Details of Restructured Loans</h3>
        <div class="overflow-x-auto bg-white rounded-lg shadow-md">
            <table id="restructuredDetailsTable" class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">BRANCH</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">CID</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">NAME</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ACCOUNT</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">TYPE</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">PRINCIPAL BALANCE</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">DISBDATE</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">DUE DATE</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    </tbody>
            </table>
        </div>
    </div>

    <div id="restructuredLoadingOverlay">
        <div class="restructured-logo-animation">
            <img src="images/logo.png" alt="Loading Logo" onerror="this.onerror=null;this.src='https://placehold.co/80x80/cbd5e1/475569?text=Logo';" />
        </div>
    </div>

    <style>
        /* Overlay for the loading animation */
        #restructuredLoadingOverlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.7); /* Semi-transparent background */
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999; /* Ensure it's on top */
            opacity: 0; /* Start hidden */
            visibility: hidden; /* Start hidden */
            transition: opacity 0.5s ease-in-out, visibility 0.5s ease-in-out;
        }

        #restructuredLoadingOverlay.active {
            opacity: 1;
            visibility: visible;
        }

        /* Logo animation styles */
        .restructured-logo-animation {
            width: 120px; /* Adjust size as needed */
            height: 120px;
            background-color: #fff; /* White background for the logo area */
            border-radius: 8px; /* Rectangular shape with slight rounded corners */
            display: flex;
            justify-content: center;
            align-items: center;
            box-shadow: 0 0 20px rgba(255, 255, 255, 0.5); /* Initial subtle glow */
            animation: logoFadeGlow 2s infinite alternate ease-in-out; /* Opacity and glow animation */
        }

        .restructured-logo-animation img {
            width: 80px; /* Size of the image inside the container */
            height: 80px;
        }

        @keyframes logoFadeGlow {
            0% {
                opacity: 1;
                box-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
            }
            50% {
                opacity: 0.2; /* Fade to 20% opacity */
                box-shadow: 0 0 40px rgba(255, 255, 255, 1), 0 0 60px rgba(255, 255, 255, 0.8); /* Stronger white glow */
            }
            100% {
                opacity: 1;
                box-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
            }
        }
    </style>

    <script src="js/tabs/operations_rest.js" defer></script>
</div>
