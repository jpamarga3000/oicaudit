<?php
// pages/mon_spe_aud.php
?>
<div id="monSpeAud" class="dashboard-section hidden">
    <div class="dashboard-card card-span-full">
        <h3 class="card-title">Monitoring: Special Audit</h3>

        <div class="flex flex-wrap items-end gap-4 pb-4">
            <div class="input-group">
                <label for="monSpeAudArea" class="input-label">AREA:</label>
                <select id="monSpeAudArea" class="select-field">
                    <option value="">Select Area</option>
                    <option value="Consolidated">Consolidated (All Branches)</option>
                    <option value="Area 1">Area 1</option>
                    <option value="Area 2">Area 2</option>
                    <option value="Area 3">Area 3</option>
                </select>
            </div>
            <div class="input-group">
                <label for="monSpeAudBranch" class="input-label">Branch:</label>
                <select id="monSpeAudBranch" class="select-field" disabled>
                    <option value="">Select Branch</option>
                    <!-- Branch options will be populated by JavaScript -->
                </select>
            </div>
            <div class="input-group">
                <button id="generateMonSpeAudReport" class="process-button" disabled>
                    Generate Report
                </button>
            </div>
        </div>

        <div class="table-scroll-wrapper">
            <div id="monSpeAudReportContainer" class="mt-4 overflow-x-auto" style="min-height: 200px; background-color: #f0f9ff; border: 2px dashed #93c5fd;">
                <p class="text-gray-500 text-center">Special Audit report will appear here.</p>
            </div>
        </div>
    </div>
</div>

<script src="js/tabs/mon_spe_aud.js" defer></script>
