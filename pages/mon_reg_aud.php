<?php
// pages/mon_reg_aud.php
?>
<div id="monRegAud" class="dashboard-section">
    <div class="dashboard-card card-span-full">
        <h3 class="card-title">Monitoring: Regular Audit</h3>

        <div class="flex flex-wrap items-end gap-4 pb-4">
            <div class="input-group">
                <label for="monRegAudArea" class="input-label">AREA:</label>
                <select id="monRegAudArea" class="select-field">
                    <option value="">Select Area</option>
                    <option value="Consolidated">Consolidated (All Branches)</option>
                    <option value="Area 1">Area 1</option>
                    <option value="Area 2">Area 2</option>
                    <option value="Area 3">Area 3</option>
                </select>
            </div>
            <div class="input-group">
                <label for="monRegAudBranch" class="input-label">Branch:</label>
                <select id="monRegAudBranch" class="select-field" disabled>
                    <option value="">Select Branch</option>
                    <!-- Branch options will be populated by JavaScript -->
                </select>
            </div>
            <div class="input-group">
                <button id="generateMonRegAudReport" class="process-button" disabled>
                    Generate Report
                </button>
            </div>
        </div>

        <!-- NEW: Summary section for compliance rate and graph -->
        <!-- The 'hidden' class is removed. JS will now only populate the data. -->
        <div id="monRegAudSummary">
            <div class="flex flex-col md:flex-row gap-4 mb-8">
                <!-- Compliance Rate Tile -->
                <div class="bg-gray-100 dark:bg-gray-800 p-6 rounded-lg shadow-sm flex-1">
                    <h4 class="text-lg font-semibold text-gray-700 dark:text-gray-200">Overall Compliance Rate</h4>
                    <p id="complianceRate" class="text-4xl font-bold text-green-600 dark:text-green-400 mt-2">0.00%</p>
                </div>
                <!-- Status Counts Line Graph -->
                <div class="bg-gray-100 dark:bg-gray-800 p-6 rounded-lg shadow-sm flex-1">
                    <h4 class="text-lg font-semibold text-gray-700 dark:text-gray-200 mb-4">Audit Status Breakdown</h4>
                    <canvas id="statusChart"></canvas>
                </div>
            </div>
        </div>

        <div class="table-scroll-wrapper">
            <div id="monRegAudReportContainer" class="mt-4 overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Year Audited</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Area Audited</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Finding ID</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk No</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk Event</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk Level</th>
                        </tr>
                    </thead>
                    <tbody id="monRegAudTableBody" class="bg-white divide-y divide-gray-200">
                        <!-- Table data will be populated by JavaScript -->
                        <tr>
                            <td colspan="7" class="text-gray-500 text-center p-4">Select an area and branch, then click "Generate Report"</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="js/tabs/mon_reg_aud.js" defer></script>
