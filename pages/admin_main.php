<?php
// pages/admin_main.php
// This file serves as the main container for Admin related sub-tabs.
?>
<div id="adminMain" class="tab-content">
        
            <!-- Content area for the horizontal sub-tabs -->
            <div id="adminTabContent" class="p-4 bg-white rounded-lg shadow-md border border-gray-200 w-full">
                <!-- These PHP includes bring the content of each sub-tab into this main container -->
                <!-- NEW: Wrap admin_profile.php in a div with dashboard-section and hidden classes -->
                <div id="adminProfile" class="dashboard-section hidden">
                    <?php include 'admin_profile.php'; ?>
                </div>
                <?php include 'admin_set.php'; ?> <!-- admin_set.php already has dashboard-section hidden -->
                 <?php include 'admin_database.php'; ?> <!-- admin_set.php already has dashboard-section hidden -->
                <!-- Include other admin sub-pages here -->
                <!-- <?php // include 'admin_users.php'; ?> -->
            </div>
        </div>
    </div>
    <!-- Defer loading of the script to ensure DOM is ready -->
    <script src="js/tabs/admin_main.js" defer></script>
    <!-- NEW: Include admin_set.js here -->
    <script src="js/tabs/admin_set.js" defer></script> 
</div>
