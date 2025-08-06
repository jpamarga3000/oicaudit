    <?php
    // pages/admin_database.php
    // This file contains the content for the "Database" sub-tab within the Admin section.
    ?>
    <div id="adminDatabase" class="dashboard-section hidden p-4">
        <h2 class="text-2xl font-bold mb-4">Database Summary</h2>
        <p class="text-gray-700 mb-6">
            This section displays the date range of the oldest to latest records for various data types across all branches.
        </p>

        <div class="mb-4 flex justify-end">
            <button id="refreshDatabaseSummaryBtn" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
                Refresh Data
            </button>
        </div>

        <!-- Outer container for horizontal scrolling if needed -->
        <div class="overflow-x-auto bg-white shadow-md rounded-lg">
            <!-- Inner container for vertical scrolling with fixed header -->
            <div class="max-h-[500px] overflow-y-auto">
                <table class="min-w-full divide-y divide-gray-200" id="databaseSummaryTable">
                    <thead class="bg-gray-50 sticky top-0 z-10">
                        <tr>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">BRANCH</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">TRNM (Transaction Records)</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SVACC (Savings Accounts)</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">LNACC (Loan Accounts)</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">GL (General Ledger)</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ACCLIST</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">AGING</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">TB (Trial Balance)</th> <!-- NEW: Added TB column header -->
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200" id="databaseSummaryTableBody">
                        <!-- Data will be loaded here by JavaScript -->
                        <tr>
                            <td colspan="8" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">Loading data...</td> <!-- Updated colspan to 8 -->
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script src="js/tabs/admin_database.js" defer></script>
