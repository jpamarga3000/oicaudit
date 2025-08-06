<?php
// pages/actg_fs.php


?>


<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<div id="actgFs" class="tab-content hidden">
    <main class="flex-1 overflow-x-hidden overflow-y-auto bg-gray-200">
        <div class="container mx-auto px-6 py-8">
            <h3 class="text-gray-700 text-3xl font-medium mb-4 mt-0">Financial Statement</h3>
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <h4 class="text-gray-700 text-xl font-semibold mb-4">Select Options</h4>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label for="areaSelect" class="block text-gray-700 text-sm font-bold mb-2">AREA:</label>
                        <select id="areaSelect" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
                            <option value="">Select Area</option>
                        </select>
                    </div>
                    <div>
                        <label for="branchSelect" class="block text-gray-700 text-sm font-bold mb-2">BRANCH:</label>
                        <select id="branchSelect" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
                            <option value="">Select Branch</option>
                        </select>
                    </div>
                    <div>
                        <label for="dateInput" class="block text-gray-700 text-sm font-bold mb-2">DATE (mm/dd/yyyy):</label>
                        <input type="date" id="dateInput" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
                    </div>
                </div>
                <div class="mt-6">
                    <button id="generateReportBtn" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline">
                        Generate Report
                    </button>
                </div>
            </div>

            <div id="loadingIndicator" class="hidden text-center py-4">
                <div class="logo-loader-container mx-auto">
                    <img id="logoLoader" src="images/logo.png" alt="Loading Logo" class="w-24 h-24 object-contain">
                </div>
                <p class="text-gray-600 mt-0">Generating Financial Statement...</p> </div>

            <div id="customAlert" class="fixed top-4 right-4 z-50 hidden p-4 rounded-lg shadow-lg text-white font-bold text-center transition-opacity duration-300 ease-in-out opacity-0">
                <span id="customAlertText"></span>
            </div>

            <div id="financialStatementSection" class="hidden bg-white rounded-lg shadow-md p-6">
                <h4 class="text-gray-700 text-xl font-semibold mb-4 text-center">FINANCIAL POSITION</h4>
                <div class="financial-statement-table-container">
                    <style>
                        /* Custom styles for Financial Statement table */
                        .financial-statement-table {
                            width: 100%;
                            border-collapse: collapse;
                        }
                        .financial-statement-table th,
                        .financial-statement-table td {
                            padding: 8px 12px;
                            border-bottom: 1px solid #e2e8f0; /* Tailwind gray-200 */
                            vertical-align: top;
                        }
                        .financial-statement-table thead th {
                            background-color: #f8f8f8; /* Light gray background for headers */
                            font-size: 0.9rem;
                            color: #4a5568; /* Tailwind gray-700 */
                            text-transform: uppercase;
                            letter-spacing: 0.05em;
                            padding-top: 12px;
                            padding-bottom: 12px;
                            position: sticky; /* Make headers sticky */
                            top: 0; /* Stick to the top */
                            z-index: 10; /* Ensure it stays above other content when scrolling */
                            white-space: normal; /* Allow text to wrap */
                        }
                        .financial-performance-table thead th { /* Apply sticky to performance table headers as well */
                            position: sticky;
                            top: 0;
                            z-index: 10;
                            background-color: #f8f8f8; /* Match background */
                            white-space: normal;
                        }
                        .header-asset {
                            background-color: #e0f2f7; /* Light blue */
                        }
                        .header-liab-equity {
                            background-color: #ffe0b2; /* Light orange */
                        }
                        .item-label {
                            font-size: 0.95rem;
                            color: #2d3748; /* Tailwind gray-800 */
                        }
                        .item-value {
                            font-size: 0.95rem;
                            color: #2d3748;
                            font-weight: 600;
                        }
                        .category-header {
                            background-color: #edf2f7; /* Tailwind gray-100 */
                            font-size: 1rem;
                            padding-top: 10px;
                            padding-bottom: 10px;
                            border-bottom: 2px solid #cbd5e0; /* Tailwind gray-300 */
                        }
                        .section-header { /* New style for ASSETS, LIABILITIES, EQUITY headers */
                            background-color: #cbd5e0; /* A slightly darker gray */
                            font-size: 1.1rem;
                            font-weight: bold;
                            padding-top: 12px;
                            padding-bottom: 12px;
                            text-align: center;
                            border-bottom: 2px solid #a0aec0;
                            text-transform: uppercase;
                        }
                        .total-item {
                            border-top: 2px solid #a0aec0; /* Tailwind gray-400 */
                            font-size: 1rem;
                            padding-top: 10px;
                            padding-bottom: 10px;
                        }
                        .grand-total-row {
                            border-top: 3px double #4a5568; /* Double border for grand total */
                            background-color: #e2e8f0; /* Slightly darker background */
                        }
                        .grand-total-row .item-label,
                        .grand-total-row .item-value {
                            font-size: 1.1rem;
                            font-weight: 700;
                        }
                        .spacer-column, .spacer-column-header {
                            width: 50px; /* Fixed width for the spacer */
                            background-color: #f8f8f8; /* Match header background */
                            border-bottom: 1px solid #e2e8f0;
                        }
                        .spacer-column-header {
                            border-bottom: 1px solid #e2e8f0; /* Maintain border */
                        }
                        /* Removed main-account-clickable as it was for modal */
                        .toggle-sub-accounts { /* New class for clickable main accounts */
                            cursor: pointer;
                            transition: background-color 0.2s ease;
                        }
                        .toggle-sub-accounts:hover {
                            background-color: #f0f4f8; /* Light hover effect */
                        }
                        /* NEW: Styles for sub-accounts in the main table */
                        .sub-account-row {
                            font-size: 0.9rem;
                            color: #4a5568;
                        }
                        /* New class for indenting sub-account labels */
                        .sub-account-label-indent {
                            padding-left: 40px; /* 2x indent */
                        }
                        .sub-total-indent {
                            padding-left: 20px; /* Indentation for sub-totals */
                        }
                        /* Ensure hidden class works for toggling */
                        .hidden {
                            display: none;
                        }
                        /* Styles for custom alert */
                        .alert-success {
                            background-color: #4CAF50; /* Green */
                        }
                        .alert-error {
                            background-color: #f44336; /* Red */
                        }
                        .alert-info {
                            background-color: #2196F3; /* Blue */
                        }

                        /* NEW LOADER STYLES - Logo Loader */
                        .logo-loader-container {
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: auto; /* Adjusted to auto */
                            margin-bottom: 0; /* Removed gap below logo */
                        }

                        #logoLoader {
                            animation: logo-glow 2s infinite; /* Apply glow animation to the image, adjusted duration */
                            /* Initial state for the image */
                            opacity: 1;
                            filter: drop-shadow(0 0 5px rgba(255, 255, 255, 0.5));
                            width: 250px; /* 3x original width (24 * 3) */
                            height: 250px; /* 3x original height (24 * 3) */
                            border-radius: 30px; /* Curved edges */
                        }

                        @keyframes logo-glow {
                            0% {
                                opacity: 1;
                                filter: drop-shadow(0 0 5px rgba(255, 255, 255, 0.5));
                            }
                            50% {
                                opacity: 0; /* Fade out to 0% */
                                filter: drop-shadow(0 0 20px rgba(255, 255, 255, 1)) drop-shadow(0 0 40px rgba(255, 255, 255, 0.8)); /* Stronger, 3D-like glow */
                            }
                            100% {
                                opacity: 1;
                                filter: drop-shadow(0 0 5px rgba(255, 255, 255, 0.5));
                            }
                        }

                        /* NEW: Styles to make table containers scrollable with sticky headers */
                        .financial-statement-table-container,
                        .financial-performance-table-container {
                            max-height: 500px; /* Adjust as needed, makes the container scrollable */
                            overflow-y: auto; /* Enables vertical scrolling */
                            border: 1px solid #e2e8f0; /* Optional: Add a border to show scrollable area */
                            border-radius: 0.5rem; /* Match parent container's rounded corners */
                        }

                        /* NEW: Styles for the in-table trend row */
                        .trend-row {
                            background-color: #f8fafc; /* Light background for the trend row */
                        }
                        .trend-chart-container {
                            position: relative;
                            height: 400px; /* Adjust height as needed for the chart */
                            width: 100%;
                            padding: 10px;
                        }
                        .trend-chart-container canvas {
                            width: 100% !important;
                            height: 100% !important;
                        }

                        .sub-account-label-indent {
    padding-left: 40px; /* Increase this value to move it further right */
    /* Or use margin-left, depending on your layout preferences */
    /* margin-left: 20px; */
}
                    </style>
                    <table class="financial-statement-table">
                        <thead>
                            <tr>
                                <th class="text-left">ACCOUNT</th>
                                <th class="text-right">CURRENT BALANCE</th>
                                <th class="text-right">BALANCES LAST DECEMBER</th>
                                <th class="text-right">CHANGES (%)</th>
                                <th class="text-center">TREND</th> <th class="text-right">STRUCTURE (%)</th>
                            </tr>
                        </thead>
                        <tbody id="financialStatementBody">
                            </tbody>
                        <tfoot id="financialStatementFooter">
                            </tfoot>
                    </table>
                </div>
            </div>

            <div id="financialPerformanceSection" class="hidden bg-white rounded-lg shadow-md p-6 mt-8">
                <h4 class="text-gray-700 text-xl font-semibold mb-4 text-center">FINANCIAL PERFORMANCE</h4>
                <div class="financial-performance-table-container">
                    <table class="financial-performance-table w-full border-collapse">
                        <thead>
                            <tr>
                                <th class="text-left">ACCOUNT</th>
                                <th class="text-right">CURRENT BALANCE</th>
                                <th class="text-right">PREVIOUS PERIOD</th> <th class="text-right">CHANGES (%)</th>
                                <th class="text-center">TREND</th> <th class="text-center">STRUCTURE (%)</th>
                            </tr>
                        </thead>
                        <tbody id="financialPerformanceBody">
                        </tbody>
                        <tfoot id="financialPerformanceFooter">
                        </tfoot>
                    </table>
                </div>
            </div>

        </div>
    </main>
</div>


<script src="js/tabs/actg_fs.js"></script>
