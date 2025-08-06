<?php
?>

<div id="operationsDosri" class="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 p-6">
    <div class="container mx-auto p-4 bg-white rounded-lg shadow-md">
        <h2 class="text-2xl font-semibold mb-6 text-gray-800 text-center">DOSRI and Former Employees Configuration</h2>

        <!-- Changed flex-nowrap to flex-wrap to allow buttons to move to the next row -->
        <div class="flex flex-wrap justify-center gap-4 mb-8">
            <button id="openDosriListBtn" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition duration-300 ease-in-out transform hover:scale-105">
                List of DOSRI
            </button>
            <button id="openFormerEmployeesListBtn" class="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition duration-300 ease-in-out transform hover:scale-105">
                List of Former Employees
            </button>
            <div class="flex items-center gap-2">
                <label for="dosriTypeMultiFilter" class="text-gray-700 font-semibold">DOSRI Type:</label>
                <select id="dosriTypeMultiFilter" multiple class="mt-1 block border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500 min-w-[150px]">
                    <option value="Director">Director</option>
                    <option value="Officer">Officer</option>
                    <option value="Staff">Staff</option>
                    <option value="Related Interest">Related Interest</option>
                </select>
            </div>
            <!-- NEW: Date input for report generation -->
            <div class="flex items-center gap-2">
                <label for="reportDate" class="text-gray-700 font-semibold">Report Date:</label>
                <input type="date" id="reportDate" class="mt-1 block border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500">
            </div>
            <button id="generateReportsBtn" class="bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition duration-300 ease-in-out transform hover:scale-105">
                Generate All Reports
            </button>
        </div>

        <div id="messageBox" class="hidden modal">
            <div class="bg-gray-800 text-white font-semibold shadow-lg rounded-lg px-8 py-6 text-center max-w-sm mx-auto">
                </div>
        </div>

        <div id="dosriListModal" class="hidden modal">
            <div class="modal-content">
                <div class="flex justify-between items-center border-b pb-3 mb-4">
                    <h3 class="text-xl font-bold text-gray-800">List of DOSRI</h3>
                    <button id="closeDosriListModalBtn" class="text-gray-500 hover:text-gray-800 text-2xl font-bold">&times;</button>
                </div>

                <!-- Changed flex-nowrap to flex-wrap to allow items to move to the next row -->
                <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
                    <div class="flex items-center gap-4">
                        <input type="text" id="dosriSearchInput" placeholder="Search DOSRI records..." class="mt-1 block w-64 border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500">
                        <select id="dosriTypeFilter" class="mt-1 block border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500">
                            <option value="">All Types</option>
                            <option value="Director">Director</option>
                            <option value="Officer">Officer</option>
                            <option value="Staff">Staff</option>
                            <option value="Related Interest">Related Interest</option>
                            </select>
                    </div>
                    <div>
                        <button id="addDosriBtn" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md shadow-sm">
                            Add New DOSRI
                        </button>
                        <button id="uploadCsvBtn" class="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-md shadow-sm">
                            Upload CSV
                        </button>
                    </div>
                </div>

                <div class="overflow-x-auto">
                    <table class="min-w-full bg-white rounded-lg shadow-md">
                        <thead>
                            <tr class="bg-gray-200 text-gray-600 uppercase text-sm leading-normal">
                                <th class="py-3 px-6 text-left">ID</th>
                                <th class="py-3 px-6 text-left">CID</th>
                                <th class="py-3 px-6 text-left">BRANCH</th>
                                <th class="py-3 px-6 text-left">NAME</th>
                                <th class="py-3 px-6 text-left">TYPE</th>
                                <th class="py-3 px-6 text-left">POSITION</th>
                                <th class="py-3 px-6 text-left">RELATED TO</th>
                                <th class="py-3 px-6 text-left">RELATIONSHIP</th>
                                <th class="py-3 px-6 text-center">ACTIONS</th>
                            </tr>
                        </thead>
                        <tbody id="dosriListTableBody" class="text-gray-700 text-sm">
                            <tr><td colspan="9" class="text-center py-4">Loading DOSRI list...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div id="dosriModal" class="hidden modal">
            <div class="modal-content">
                <div class="flex justify-between items-center border-b pb-3 mb-4">
                    <h3 id="modalTitle" class="text-xl font-bold text-gray-800">Add New DOSRI</h3>
                    <button id="cancelDosriBtn" class="text-gray-500 hover:text-gray-800 text-2xl font-bold">&times;</button>
                </div>
                <form id="dosriForm" class="space-y-4">
                    <input type="hidden" id="dosriId">

                    <div>
                        <label for="cid" class="block text-sm font-medium text-gray-700">CID:</label>
                        <input type="number" id="cid" name="CID" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Customer ID (optional)">
                    </div>
                    <div>
                        <label for="branch" class="block text-sm font-medium text-gray-700">Branch:</label>
                        <input type="text" id="branch" name="BRANCH" required class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500" placeholder="e.g., Main Branch">
                    </div>
                    <div>
                        <label for="name" class="block text-sm font-medium text-gray-700">Name:</label>
                        <input type="text" id="name" name="NAME" required class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Full Name">
                    </div>
                    <div>
                        <label for="type" class="block text-sm font-medium text-gray-700">Type:</label>
                        <input type="text" id="type" name="TYPE" required class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500" placeholder="e.g., Director, Officer">
                    </div>
                    <div>
                        <label for="position" class="block text-sm font-medium text-gray-700">Position:</label>
                        <input type="text" id="position" name="POSITION" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500" placeholder="e.g., CEO, Manager">
                    </div>
                    <div>
                        <label for="relatedTo" class="block text-sm font-medium text-gray-700">Related To:</label>
                        <input type="text" id="relatedTo" name="RELATED TO" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500" placeholder="e.g., Self, Family Member">
                    </div>
                    <div>
                        <label for="relationship" class="block text-sm font-medium text-gray-700">Relationship:</label>
                        <input type="text" id="relationship" name="RELATIONSHIP" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500" placeholder="e.g., Spouse, Child">
                    </div>
                    <div class="flex justify-end space-x-2">
                        <button type="button" id="cancelDosriBtnForm" class="bg-gray-300 hover:bg-gray-400 text-gray-800 px-4 py-2 rounded-md shadow-sm">Cancel</button>
                        <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md shadow-sm">Save Record</button>
                    </div>
                </form>
            </div>
        </div>

        <div id="uploadCsvModal" class="hidden modal">
            <div class="modal-content">
                <div class="flex justify-between items-center border-b pb-3 mb-4">
                    <h3 class="text-xl font-bold text-gray-800">Upload DOSRI CSV</h3>
                    <button id="cancelUploadCsvBtn" class="text-gray-500 hover:text-gray-800 text-2xl font-bold">&times;</button>
                </div>
                <form id="uploadCsvForm" class="space-y-4">
                    <div>
                        <label for="dosriCsvFile" class="block text-sm font-medium text-gray-700">Select CSV File:</label>
                        <input type="file" id="dosriCsvFile" name="csv_file" accept=".csv" required class="mt-1 block w-full text-gray-700 border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500">
                    </div>
                    <div class="space-y-2">
                        <p class="block text-sm font-medium text-gray-700">Upload Option:</p>
                        <div class="flex items-center">
                            <input type="radio" id="overrideAll" name="upload_option" value="override" class="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300" checked>
                            <label for="overrideAll" class="ml-2 block text-sm text-gray-900">
                                Override All Existing Records (Deletes all current records before adding new)
                            </label>
                        </div>
                        <div class="flex items-center">
                            <input type="radio" id="append" name="upload_option" value="append" class="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300">
                            <label for="append" class="ml-2 block text-sm text-gray-900">
                                Append to Existing Records (Adds new records; this may result in duplicates if not careful)
                            </label>
                        </div>
                    </div>
                    <div class="flex justify-end space-x-2">
                        <button type="button" id="cancelUploadCsvBtnForm" class="bg-gray-300 hover:bg-gray-400 text-gray-800 px-4 py-2 rounded-md shadow-sm">Cancel</button>
                        <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md shadow-sm">Upload</button>
                    </div>
                </form>
            </div>
        </div>

        <div id="formerEmployeesListModal" class="hidden modal">
            <div class="modal-content">
                <div class="flex justify-between items-center border-b pb-3 mb-4">
                    <h3 class="text-xl font-bold text-gray-800">List of Former Employees</h3>
                    <button id="closeFormerEmployeesListModalBtn" class="text-gray-500 hover:text-gray-800 text-2xl font-bold">&times;</button>
                </div>

                <!-- Changed flex-nowrap to flex-wrap to allow items to move to the next row -->
                <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
                    <div class="flex items-center gap-4">
                        <input type="text" id="formEmpSearchInput" placeholder="Search former employees..." class="mt-1 block w-64 border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500">
                        <select id="formEmpStatusFilter" class="mt-1 block border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500">
                            <option value="">All Statuses</option>
                            <option value="Active">Active</option>
                            <option value="Resigned">Resigned</option>
                            <option value="Terminated">Terminated</option>
                            <option value="Retired">Retired</option>
                            </select>
                    </div>
                    <div>
                        <button id="addFormEmpBtn" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md shadow-sm">
                            Add New Former Employee
                        </button>
                        <button id="uploadFormEmpCsvBtn" class="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-md shadow-sm">
                            Upload CSV
                        </button>
                    </div>
                </div>

                <div class="overflow-x-auto">
                    <table class="min-w-full bg-white rounded-lg shadow-md">
                        <thead>
                            <tr class="bg-gray-200 text-gray-600 uppercase text-sm leading-normal">
                                <th class="py-3 px-6 text-left">ID</th>
                                <th class="py-3 px-6 text-left">BRANCH</th>
                                <th class="py-3 px-6 text-left">NAME</th>
                                <th class="py-3 px-6 text-left">CID</th>
                                <th class="py-3 px-6 text-left">DATE RESIGNED</th>
                                <th class="py-3 px-6 text-left">STATUS</th>
                                <th class="py-3 px-6 text-center">ACTIONS</th>
                            </tr>
                        </thead>
                        <tbody id="formerEmployeesListTableBody" class="text-gray-700 text-sm">
                            <tr><td colspan="7" class="text-center py-4">Loading former employee data...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div id="formEmpModal" class="hidden modal">
            <div class="modal-content">
                <div class="flex justify-between items-center border-b pb-3 mb-4">
                    <h3 id="formEmpModalTitle" class="text-xl font-bold text-gray-800">Add New Former Employee</h3>
                    <button id="cancelFormEmpBtn" class="text-gray-500 hover:text-gray-800 text-2xl font-bold">&times;</button>
                </div>
                <form id="formEmpForm" class="space-y-4">
                    <input type="hidden" id="formEmpId">

                    <div>
                        <label for="formEmpBranch" class="block text-sm font-medium text-gray-700">Branch:</label>
                        <input type="text" id="formEmpBranch" name="BRANCH" required class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500" placeholder="e.g., YACAPIN">
                    </div>
                    <div>
                        <label for="formEmpName" class="block text-sm font-medium text-gray-700">Name:</label>
                        <input type="text" id="formEmpName" name="NAME" required class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Full Name">
                    </div>
                    <div>
                        <label for="formEmpCid" class="block text-sm font-medium text-gray-700">CID:</label>
                        <input type="number" id="formEmpCid" name="CID" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Customer ID (optional)">
                    </div>
                    <div>
                        <label for="formEmpDateResigned" class="block text-sm font-medium text-gray-700">Date Resigned:</label>
                        <input type="text" id="formEmpDateResigned" name="DATE RESIGNED" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500" placeholder="MM/DD/YYYY">
                    </div>
                    <div>
                        <label for="formEmpStatus" class="block text-sm font-medium text-gray-700">Status:</label>
                        <input type="text" id="formEmpStatus" name="STATUS" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500" placeholder="e.g., Resigned, Active">
                    </div>

                    <div class="flex justify-end space-x-2">
                        <button type="button" id="cancelFormEmpBtnForm" class="bg-gray-300 hover:bg-gray-400 text-gray-800 px-4 py-2 rounded-md shadow-sm">Cancel</button>
                        <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md shadow-sm">Save Record</button>
                    </div>
                </form>
            </div>
        </div>

        <div id="uploadFormEmpCsvModal" class="hidden modal">
            <div class="modal-content">
                <div class="flex justify-between items-center border-b pb-3 mb-4">
                    <h3 class="text-xl font-bold text-gray-800">Upload Former Employee CSV</h3>
                    <button id="cancelUploadFormEmpCsvBtn" class="text-gray-500 hover:text-gray-800 text-2xl font-bold">&times;</button>
                </div>
                <form id="uploadFormEmpCsvForm" class="space-y-4">
                    <div>
                        <label for="formEmpCsvFile" class="block text-sm font-medium text-gray-700">Select CSV File:</label>
                        <input type="file" id="formEmpCsvFile" name="csv_file" accept=".csv" required class="mt-1 block w-full text-gray-700 border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500">
                    </div>
                    <div class="space-y-2">
                        <p class="block text-sm font-medium text-gray-700">Upload Option:</p>
                        <div class="flex items-center">
                            <input type="radio" id="formEmpOverrideAll" name="upload_option" value="override" class="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300" checked>
                            <label for="formEmpOverrideAll" class="ml-2 block text-sm text-gray-900">
                                Override All Existing Records
                            </label>
                        </div>
                        <div class="flex items-center">
                            <input type="radio" id="formEmpAppend" name="upload_option" value="append" class="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300">
                            <label for="append" class="ml-2 block text-sm text-gray-900">
                                Append to Existing Records
                            </label>
                        </div>
                    </div>
                    <div class="flex justify-end space-x-2">
                        <button type="button" id="cancelUploadFormEmpCsvBtnForm" class="bg-gray-300 hover:bg-gray-400 text-gray-800 px-4 py-2 rounded-md shadow-sm">Cancel</button>
                        <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md shadow-sm">Upload</button>
                    </div>
                </form>
            </div>
        </div>

        <div class="bg-white shadow-md rounded-lg p-6 mt-8">
            <h2 class="text-2xl font-semibold text-gray-700 mb-4">SUMMARY REPORT OF DOSRI</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="flex flex-col items-center justify-center p-4 border border-gray-200 rounded-lg">
                    <h3 class="text-xl font-semibold text-gray-700 mb-4">LOAN BALANCES</h3>
                    <div id="loan_balances_summary_tiles" class="w-full flex flex-col items-center justify-center">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
                            <div class="bg-green-100 p-4 rounded-lg shadow-sm text-center">
                                <p class="text-sm font-medium text-green-800">CURRENT BALANCE</p>
                                <p id="loan_current_balance_amount" class="text-2xl font-bold text-green-900 mt-1">₱0.00</p>
                                <!-- DOSRI Type Breakdown for Current Balance -->
                                <div class="text-xs font-medium text-green-700 mt-2">
                                    <p>D: <span id="loan_current_d_amount">₱0.00</span></p>
                                    <p>O: <span id="loan_current_o_amount">₱0.00</span></p>
                                    <p>S: <span id="loan_current_s_amount">₱0.00</span></p>
                                    <p>RI: <span id="loan_current_ri_amount">₱0.00</span></p>
                                </div>
                            </div>
                            <div class="bg-red-100 p-4 rounded-lg shadow-sm text-center">
                                <p class="text-sm font-medium text-red-800">TOTAL PAST DUE</p>
                                <p id="loan_total_past_due_amount" class="text-2xl font-bold text-red-900 mt-1">₱0.00</p>
                                <!-- DOSRI Type Breakdown for Total Past Due -->
                                <div class="text-xs font-medium text-red-700 mt-2">
                                    <p>D: <span id="loan_past_due_d_amount">₱0.00</span></p>
                                    <p>O: <span id="loan_past_due_o_amount">₱0.00</span></p>
                                    <p>S: <span id="loan_past_due_s_amount">₱0.00</span></p>
                                    <p>RI: <span id="loan_past_due_ri_amount">₱0.00</span></p>
                                </div>
                            </div>
                        </div>

                        <h4 class="text-lg font-semibold text-gray-700 mt-6 mb-3">PAST DUE BREAKDOWN</h4>
                        <div id="loan_past_due_breakdown_tiles" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4 gap-4 w-full">
                            <div class="bg-orange-100 p-3 rounded-lg shadow-sm text-center">
                                <p class="text-xs font-medium text-orange-800">1-30 DAYS</p>
                                <p id="past_due_1_30_days_amount" class="text-xl font-bold text-orange-900 mt-1">₱0.00</p>
                                <div class="text-xs font-medium text-orange-700 mt-1">
                                    <p>D: <span id="past_due_1_30_d_amount">₱0.00</span></p>
                                    <p>O: <span id="past_due_1_30_o_amount">₱0.00</span></p>
                                    <p>S: <span id="past_due_1_30_s_amount">₱0.00</span></p>
                                    <p>RI: <span id="past_due_1_30_ri_amount">₱0.00</span></p>
                                </div>
                            </div>
                            <div class="bg-orange-100 p-3 rounded-lg shadow-sm text-center">
                                <p class="text-xs font-medium text-orange-800">31-60 DAYS</p>
                                <p id="past_due_31_60_days_amount" class="text-xl font-bold text-orange-900 mt-1">₱0.00</p>
                                <div class="text-xs font-medium text-orange-700 mt-1">
                                    <p>D: <span id="past_due_31_60_d_amount">₱0.00</span></p>
                                    <p>O: <span id="past_due_31_60_o_amount">₱0.00</span></p>
                                    <p>S: <span id="past_due_31_60_s_amount">₱0.00</span></p>
                                    <p>RI: <span id="past_due_31_60_ri_amount">₱0.00</span></p>
                                </div>
                            </div>
                            <div class="bg-orange-100 p-3 rounded-lg shadow-sm text-center">
                                <p class="text-xs font-medium text-orange-800">61-90 DAYS</p>
                                <p id="past_due_61_90_days_amount" class="text-xl font-bold text-orange-900 mt-1">₱0.00</p>
                                <div class="text-xs font-medium text-orange-700 mt-1">
                                    <p>D: <span id="past_due_61_90_d_amount">₱0.00</span></p>
                                    <p>O: <span id="past_due_61_90_o_amount">₱0.00</span></p>
                                    <p>S: <span id="past_due_61_90_s_amount">₱0.00</span></p>
                                    <p>RI: <span id="past_due_61_90_ri_amount">₱0.00</span></p>
                                </div>
                            </div>
                            <div class="bg-orange-100 p-3 rounded-lg shadow-sm text-center">
                                <p class="text-xs font-medium text-orange-800">91-120 DAYS</p>
                                <p id="past_due_91_120_days_amount" class="text-xl font-bold text-orange-900 mt-1">₱0.00</p>
                                <div class="text-xs font-medium text-orange-700 mt-1">
                                    <p>D: <span id="past_due_91_120_d_amount">₱0.00</span></p>
                                    <p>O: <span id="past_due_91_120_o_amount">₱0.00</span></p>
                                    <p>S: <span id="past_due_91_120_s_amount">₱0.00</span></p>
                                    <p>RI: <span id="past_due_91_120_ri_amount">₱0.00</span></p>
                                </div>
                            </div>
                            <div class="bg-red-100 p-3 rounded-lg shadow-sm text-center">
                                <p class="text-xs font-medium text-red-800">121-180 DAYS</p>
                                <p id="past_due_121_180_days_amount" class="text-xl font-bold text-red-900 mt-1">₱0.00</p>
                                <div class="text-xs font-medium text-red-700 mt-1">
                                    <p>D: <span id="past_due_121_180_d_amount">₱0.00</span></p>
                                    <p>O: <span id="past_due_121_180_o_amount">₱0.00</span></p>
                                    <p>S: <span id="past_due_121_180_s_amount">₱0.00</span></p>
                                    <p>RI: <span id="past_due_121_180_ri_amount">₱0.00</span></p>
                                </div>
                            </div>
                            <div class="bg-red-100 p-3 rounded-lg shadow-sm text-center">
                                <p class="text-xs font-medium text-red-800">181-365 DAYS</p>
                                <p id="past_due_181_365_days_amount" class="text-xl font-bold text-red-900 mt-1">₱0.00</p>
                                <div class="text-xs font-medium text-red-700 mt-1">
                                    <p>D: <span id="past_due_181_365_d_amount">₱0.00</span></p>
                                    <p>O: <span id="past_due_181_365_o_amount">₱0.00</span></p>
                                    <p>S: <span id="past_due_181_365_s_amount">₱0.00</span></p>
                                    <p>RI: <span id="past_due_181_365_ri_amount">₱0.00</span></p>
                                </div>
                            </div>
                            <div class="bg-red-100 p-3 rounded-lg shadow-sm text-center col-span-2 sm:col-span-1 md:col-span-2 lg:col-span-1 xl:col-span-1">
                                <p class="text-xs font-medium text-red-800">OVER 365 DAYS</p>
                                <p id="past_due_over_365_days_amount" class="text-xl font-bold text-red-900 mt-1">₱0.00</p>
                                <div class="text-xs font-medium text-red-700 mt-1">
                                    <p>D: <span id="past_due_over_365_d_amount">₱0.00</span></p>
                                    <p>O: <span id="past_due_over_365_o_amount">₱0.00</span></p>
                                    <p>S: <span id="past_due_over_365_s_amount">₱0.00</span></p>
                                    <p>RI: <span id="past_due_over_365_ri_amount">₱0.00</span></p>
                                </div>
                            </div>
                        </div>
                        <p id="loan_balances_status" class="text-gray-500 text-center mt-4 hidden">Loading loan data...</p>
                        <p id="loan_balances_error" class="text-red-500 text-center mt-4 hidden">Error loading loan data.</p>
                        <p id="loan_balances_no_data" class="text-gray-500 text-center mt-4 hidden">No loan data available for DOSRI.</p>
                    </div>
                </div>

                <div class="p-4 border border-gray-200 rounded-lg">
                    <h3 class="text-xl font-semibold text-gray-700 mb-4 text-center">DEPOSIT LIABILITIES</h3>
                    <div id="deposit_liabilities_tiles" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 gap-4">
                        <div class="bg-blue-100 p-4 rounded-lg shadow-sm text-center">
                            <p class="text-sm font-medium text-blue-800">REGULAR SAVINGS</p>
                            <p id="regular_savings_amount" class="text-2xl font-bold text-blue-900 mt-1">₱0.00</p>
                            <p id="regular_savings_count" class="text-xs font-medium text-blue-700 mt-1">Accounts: 0</p>
                            <!-- DOSRI Type Breakdown for Regular Savings -->
                            <div class="text-xs font-medium text-blue-700 mt-1">
                                <p>D: <span id="regular_savings_d_amount">₱0.00</span></p>
                                <p>O: <span id="regular_savings_o_amount">₱0.00</span></p>
                                <p>S: <span id="regular_savings_s_amount">₱0.00</span></p>
                                <p>RI: <span id="regular_savings_ri_amount">₱0.00</span></p>
                            </div>
                        </div>
                        <div class="bg-gray-100 p-4 rounded-lg shadow-sm text-center">
                            <p class="text-sm font-medium text-gray-800">ATM SAVINGS</p>
                            <p id="atm_savings_amount" class="text-2xl font-bold text-gray-900 mt-1">₱0.00</p>
                            <p id="atm_savings_count" class="text-xs font-medium text-gray-700 mt-1">Accounts: 0</p>
                            <!-- DOSRI Type Breakdown for ATM Savings -->
                            <div class="text-xs font-medium text-gray-700 mt-1">
                                <p>D: <span id="atm_savings_d_amount">₱0.00</span></p>
                                <p>O: <span id="atm_savings_o_amount">₱0.00</span></p>
                                <p>S: <span id="atm_savings_s_amount">₱0.00</span></p>
                                <p>RI: <span id="atm_savings_ri_amount">₱0.00</span></p>
                            </div>
                        </div>
                        <div class="bg-green-100 p-4 rounded-lg shadow-sm text-center">
                            <p class="text-sm font-medium text-green-800">SHARE CAPITAL</p>
                            <p id="share_capital_amount" class="text-2xl font-bold text-green-900 mt-1">₱0.00</p>
                            <p id="share_capital_count" class="text-xs font-medium text-green-700 mt-1">Accounts: 0</p>
                            <!-- DOSRI Type Breakdown for Share Capital -->
                            <div class="text-xs font-medium text-green-700 mt-1">
                                <p>D: <span id="share_capital_d_amount">₱0.00</span></p>
                                <p>O: <span id="share_capital_o_amount">₱0.00</span></p>
                                <p>S: <span id="share_capital_s_amount">₱0.00</span></p>
                                <p>RI: <span id="share_capital_ri_amount">₱0.00</span></p>
                            </div>
                        </div>
                        <div class="bg-yellow-100 p-4 rounded-lg shadow-sm text-center">
                            <p class="text-sm font-medium text-yellow-800">TIME DEPOSITS</p>
                            <p id="time_deposits_amount" class="text-2xl font-bold text-yellow-900 mt-1">₱0.00</p>
                            <p id="time_deposits_count" class="text-xs font-medium text-yellow-700 mt-1">Accounts: 0</p>
                            <!-- DOSRI Type Breakdown for Time Deposits -->
                            <div class="text-xs font-medium text-yellow-700 mt-1">
                                <p>D: <span id="time_deposits_d_amount">₱0.00</span></p>
                                <p>O: <span id="time_deposits_o_amount">₱0.00</span></p>
                                <p>S: <span id="time_deposits_s_amount">₱0.00</span></p>
                                <p>RI: <span id="time_deposits_ri_amount">₱0.00</span></p>
                            </div>
                        </div>
                        <div class="bg-purple-100 p-4 rounded-lg shadow-sm text-center">
                            <p class="text-sm font-medium text-purple-800">YOUTH SAVINGS</p>
                            <p id="youth_savings_amount" class="text-2xl font-bold text-purple-900 mt-1">₱0.00</p>
                            <p id="youth_savings_count" class="text-xs font-medium text-purple-700 mt-1">Accounts: 0</p>
                            <!-- DOSRI Type Breakdown for Youth Savings -->
                            <div class="text-xs font-medium text-purple-700 mt-1">
                                <p>D: <span id="youth_savings_d_amount">₱0.00</span></p>
                                <p>O: <span id="youth_savings_o_amount">₱0.00</span></p>
                                <p>S: <span id="youth_savings_s_amount">₱0.00</span></p>
                                <p>RI: <span id="youth_savings_ri_amount">₱0.00</span></p>
                            </div>
                        </div>
                        <div class="bg-red-100 p-4 rounded-lg shadow-sm text-center">
                            <p class="text-sm font-medium text-red-800">SPECIAL DEPOSITS</p>
                            <p id="special_deposits_amount" class="text-2xl font-bold text-red-900 mt-1">₱0.00</p>
                            <p id="special_deposits_count" class="text-xs font-medium text-red-700 mt-1">Accounts: 0</p>
                            <!-- DOSRI Type Breakdown for Special Deposits -->
                            <div class="text-xs font-medium text-red-700 mt-1">
                                <p>D: <span id="special_deposits_d_amount">₱0.00</span></p>
                                <p>O: <span id="special_deposits_o_amount">₱0.00</span></p>
                                <p>S: <span id="special_deposits_s_amount">₱0.00</span></p>
                                <p>RI: <span id="special_deposits_ri_amount">₱0.00</span></p>
                            </div>
                        </div>
                    </div>
                    <p id="deposit_status" class="text-gray-500 text-center mt-4 hidden">Loading deposit data.</p>
                    <p id="deposit_error" class="text-red-500 text-center mt-4 hidden">Error loading deposit data.</p>
                    <p id="deposit_no_data" class="text-gray-500 text-center mt-4 hidden">No deposit data available for DOSRI.</p>
                </div>
            </div>

            <div class="details-section mt-8">
                <h2 class="text-2xl font-bold mb-4 text-gray-700 text-center">DOSRI DETAILS</h2>

                <div class="loan-balance-details bg-white p-6 rounded-lg shadow-md mb-6">
                    <h3 class="text-xl font-semibold mb-3 text-gray-700">LOAN BALANCE</h3>
                    <!-- Changed flex-nowrap to flex-wrap to allow items to move to the next row -->
                    <div class="flex flex-wrap items-center gap-4 mb-4">
                        <input type="text" id="loanBalanceSearchInput" placeholder="Search loan balances..." class="mt-1 block w-64 border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500">
                        <button id="copyLoanBalanceTableBtn" class="bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-md shadow-sm">Copy Table</button>
                        <button id="downloadDosriExcelBtn" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-md shadow-sm">Download All as Excel</button>
                    </div>
                    <div class="overflow-y-auto" style="max-height: 800px;">
                        <table id="loan-balance-table" class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-50 sticky top-0 z-10">
                                <tr>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">BRANCH</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">CID</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">NAME OF MEMBER</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">TYPE</th> <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">LOAN ACCT.</th>
                                    <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">PRINCIPAL BALANCE</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">PRODUCT</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">DISBDATE</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">DUE DATE</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">AGING</th>
                                </tr>
                            </thead>
                            <tbody id="loan-balance-table-body" class="bg-white divide-y divide-gray-200">
                                <tr><td colspan="10" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">Loading loan balance details...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="deposit-liabilities-details bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-xl font-semibold mb-3 text-gray-700">DEPOSIT LIABILITIES</h3>
                    <!-- Changed flex-nowrap to flex-wrap to allow items to move to the next row -->
                    <div class="flex flex-wrap items-center gap-4 mb-4">
                        <input type="text" id="depositLiabilitiesSearchInput" placeholder="Search deposit liabilities..." class="mt-1 block w-64 border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500">
                        <button id="copyDepositLiabilitiesTableBtn" class="bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-md shadow-sm">Copy Table</button>
                    </div>
                    <div class="overflow-y-auto" style="max-height: 800px;">
                        <table id="deposit-liabilities-table" class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-50 sticky top-0 z-10">
                                <tr>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">BRANCH</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ACCOUNT ACC</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">NAME</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">TYPE</th> <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">CID</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">PRODUCT ACCNAME</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">OPENED DOPEN</th>
                                    <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">BALANCE BAL</th>
                                </tr>
                            </thead>
                            <tbody id="deposit-liabilities-table-body" class="bg-white divide-y divide-gray-200">
                                <tr><td colspan="8" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">Loading deposit liabilities details...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <div class="bg-white shadow-md rounded-lg p-6 mt-8">
            <h2 class="text-2xl font-semibold text-gray-700 mb-4">SUMMARY REPORT OF FORMER EMPLOYEES</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="flex flex-col items-center justify-center p-4 border border-gray-200 rounded-lg">
                    <h3 class="text-xl font-semibold text-gray-700 mb-4">LOAN BALANCES (Former Employees)</h3>
                    <div id="form_emp_loan_summary_tiles" class="w-full flex flex-col items-center justify-center">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
                            <div class="bg-green-100 p-4 rounded-lg shadow-sm text-center">
                                <p class="text-sm font-medium text-green-800">CURRENT BALANCE</p>
                                <p id="form_emp_loan_current_balance_amount" class="text-2xl font-bold text-green-900 mt-1">₱0.00</p>
                            </div>
                            <div class="bg-red-100 p-4 rounded-lg shadow-sm text-center">
                                <p class="text-sm font-medium text-red-800">TOTAL PAST DUE</p>
                                <p id="form_emp_loan_total_past_due_amount" class="text-2xl font-bold text-red-900 mt-1">₱0.00</p>
                            </div>
                        </div>

                        <h4 class="text-lg font-semibold text-gray-700 mt-6 mb-3">PAST DUE BREAKDOWN (Former Employees)</h4>
                        <div id="form_emp_loan_past_due_breakdown_tiles" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4 gap-4 w-full">
                            <div class="bg-orange-100 p-3 rounded-lg shadow-sm text-center">
                                <p class="text-xs font-medium text-orange-800">1-30 DAYS</p>
                                <p id="form_emp_past_due_1_30_days_amount" class="text-xl font-bold text-orange-900 mt-1">₱0.00</p>
                            </div>
                            <div class="bg-orange-100 p-3 rounded-lg shadow-sm text-center">
                                <p class="text-xs font-medium text-orange-800">31-60 DAYS</p>
                                <p id="form_emp_past_due_31_60_days_amount" class="text-xl font-bold text-orange-900 mt-1">₱0.00</p>
                            </div>
                            <div class="bg-orange-100 p-3 rounded-lg shadow-sm text-center">
                                <p class="text-xs font-medium text-orange-800">61-90 DAYS</p>
                                <p id="form_emp_past_due_61_90_days_amount" class="text-xl font-bold text-orange-900 mt-1">₱0.00</p>
                            </div>
                            <div class="bg-orange-100 p-3 rounded-lg shadow-sm text-center">
                                <p class="text-xs font-medium text-orange-800">91-120 DAYS</p>
                                <p id="form_emp_past_due_91_120_days_amount" class="text-xl font-bold text-orange-900 mt-1">₱0.00</p>
                            </div>
                            <div class="bg-red-100 p-3 rounded-lg shadow-sm text-center">
                                <p class="text-xs font-medium text-red-800">121-180 DAYS</p>
                                <p id="form_emp_past_due_121_180_days_amount" class="text-xl font-bold text-red-900 mt-1">₱0.00</p>
                            </div>
                            <div class="bg-red-100 p-3 rounded-lg shadow-sm text-center">
                                <p class="text-xs font-medium text-red-800">181-365 DAYS</p>
                                <p id="form_emp_past_due_181_365_days_amount" class="text-xl font-bold text-red-900 mt-1">₱0.00</p>
                            </div>
                            <div class="bg-red-100 p-3 rounded-lg shadow-sm text-center col-span-2 sm:col-span-1 md:col-span-2 lg:col-span-1 xl:col-span-1">
                                <p class="text-xs font-medium text-red-800">OVER 365 DAYS</p>
                                <p id="form_emp_past_due_over_365_days_amount" class="text-xl font-bold text-red-900 mt-1">₱0.00</p>
                            </div>
                        </div>
                        <p id="form_emp_loan_status" class="text-gray-500 text-center mt-4 hidden">Loading loan data...</p>
                        <p id="form_emp_loan_error" class="text-red-500 text-center mt-4 hidden">Error loading loan data.</p>
                        <p id="form_emp_loan_no_data" class="text-gray-500 text-center mt-4 hidden">No loan data available for Former Employees.</p>
                    </div>
                </div>

                <div class="p-4 border border-gray-200 rounded-lg">
                    <h3 class="text-xl font-semibold text-gray-700 mb-4 text-center">DEPOSIT LIABILITIES (Former Employees)</h3>
                    <div id="form_emp_deposit_liabilities_tiles" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 gap-4">
                        <div class="bg-blue-100 p-4 rounded-lg shadow-sm text-center">
                            <p class="text-sm font-medium text-blue-800">REGULAR SAVINGS</p>
                            <p id="form_emp_regular_savings_amount" class="text-2xl font-bold text-blue-900 mt-1">₱0.00</p>
                            <p id="form_emp_regular_savings_count" class="text-xs font-medium text-blue-700 mt-1">Accounts: 0</p>
                        </div>
                        <div class="bg-gray-100 p-4 rounded-lg shadow-sm text-center">
                            <p class="text-sm font-medium text-gray-800">ATM SAVINGS</p>
                            <p id="form_emp_atm_savings_amount" class="text-2xl font-bold text-gray-900 mt-1">₱0.00</p>
                            <p id="form_emp_atm_savings_count" class="text-xs font-medium text-gray-700 mt-1">Accounts: 0</p>
                        </div>
                        <div class="bg-green-100 p-4 rounded-lg shadow-sm text-center">
                            <p class="text-sm font-medium text-green-800">SHARE CAPITAL</p>
                            <p id="form_emp_share_capital_amount" class="text-2xl font-bold text-green-900 mt-1">₱0.00</p>
                            <p id="form_emp_share_capital_count" class="text-xs font-medium text-green-700 mt-1">Accounts: 0</p>
                        </div>
                        <div class="bg-yellow-100 p-4 rounded-lg shadow-sm text-center">
                            <p class="text-sm font-medium text-yellow-800">TIME DEPOSITS</p>
                            <p id="form_emp_time_deposits_amount" class="text-2xl font-bold text-yellow-900 mt-1">₱0.00</p>
                            <p id="form_emp_time_deposits_count" class="text-xs font-medium text-yellow-700 mt-1">Accounts: 0</p>
                        </div>
                        <div class="bg-purple-100 p-4 rounded-lg shadow-sm text-center">
                            <p class="text-sm font-medium text-purple-800">YOUTH SAVINGS</p>
                            <p id="form_emp_youth_savings_amount" class="text-2xl font-bold text-purple-900 mt-1">₱0.00</p>
                            <p id="form_emp_youth_savings_count" class="text-xs font-medium text-purple-700 mt-1">Accounts: 0</p>
                        </div>
                        <div class="bg-red-100 p-4 rounded-lg shadow-sm text-center">
                            <p class="text-sm font-medium text-red-800">SPECIAL DEPOSITS</p>
                            <p id="form_emp_special_deposits_amount" class="text-2xl font-bold text-red-900 mt-1">₱0.00</p>
                            <p id="form_emp_special_deposits_count" class="text-xs font-medium text-red-700 mt-1">Accounts: 0</p>
                        </div>
                    </div>
                    <p id="form_emp_deposit_status" class="text-gray-500 text-center mt-4 hidden">Loading deposit data.</p>
                    <p id="form_emp_deposit_error" class="text-red-500 text-center mt-4 hidden">Error loading deposit data.</p>
                    <p id="form_emp_deposit_no_data" class="text-gray-500 text-center mt-4 hidden">No deposit data available for Former Employees.</p>
                </div>
            </div>
            <div class="details-section mt-8">
                <h2 class="text-2xl font-bold mb-4 text-gray-700 text-center">FORMER EMPLOYEES DETAILS</h2>

                <div class="loan-balance-details bg-white p-6 rounded-lg shadow-md mb-6">
                    <h3 class="text-xl font-semibold mb-3 text-gray-700">LOAN BALANCE (Former Employees)</h3>
                    <!-- Changed flex-nowrap to flex-wrap to allow items to move to the next row -->
                    <div class="flex flex-wrap items-center gap-4 mb-4">
                        <input type="text" id="formEmpLoanBalanceSearchInput" placeholder="Search loan balances..." class="mt-1 block w-64 border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500">
                        <button id="copyFormEmpLoanBalanceTableBtn" class="bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-md shadow-sm">Copy Table</button>
                        <button id="downloadFormEmpExcelBtn" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-md shadow-sm">Download All as Excel</button>
                    </div>
                    <div class="overflow-y-auto" style="max-height: 800px;">
                        <table id="form-emp-loan-balance-table" class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-50 sticky top-0 z-10">
                                <tr>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">BRANCH</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">CID</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">NAME OF MEMBER</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">LOAN ACCT.</th>
                                    <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">PRINCIPAL BALANCE</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">PRODUCT</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">DISBDATE</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">DUE DATE</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">AGING</th>
                                </tr>
                            </thead>
                            <tbody id="form-emp-loan-table-body" class="bg-white divide-y divide-gray-200">
                                <tr><td colspan="9" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">Loading loan balance details...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="deposit-liabilities-details bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-xl font-semibold mb-3 text-gray-700">DEPOSIT LIABILITIES (Former Employees)</h3>
                    <!-- Changed flex-nowrap to flex-wrap to allow items to move to the next row -->
                    <div class="flex flex-wrap items-center gap-4 mb-4">
                        <input type="text" id="formEmpDepositLiabilitiesSearchInput" placeholder="Search deposit liabilities..." class="mt-1 block w-64 border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500">
                        <button id="copyFormEmpDepositLiabilitiesTableBtn" class="bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-md shadow-sm">Copy Table</button>
                    </div>
                    <div class="overflow-y-auto" style="max-height: 800px;">
                        <table id="form-emp-deposit-liabilities-table" class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-50 sticky top-0 z-10">
                                <tr>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">BRANCH</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ACCOUNT ACC</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">NAME</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">CID</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">PRODUCT ACCNAME</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">OPENED DOPEN</th>
                                    <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">BALANCE BAL</th>
                                </tr>
                            </thead>
                            <tbody id="form-emp-deposit-liabilities-table-body" class="bg-white divide-y divide-gray-200">
                                <tr><td colspan="7" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">Loading deposit liabilities details...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script src="js/tabs/operations_dosri.js"></script>
<script src="js/tabs/operations_form_emp.js"></script>
