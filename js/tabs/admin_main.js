// audit_tool/js/tabs/admin_main.js

// Ensure window.registerTabInitializer is available from main.js
if (window.registerTabInitializer) {
    // This is the initializer function for 'adminMain' itself, called by main.js
    // when the "Admin" main tab is activated.
    window.registerTabInitializer('adminMain', function() {
        console.log("admin_main.js: Initializing Admin Main Tab. (adminMain)");

        // Get references to the horizontal sub-tab buttons within admin_main.php
        const profileButton = document.querySelector('#adminMain .horizontal-tab-button:nth-child(1)');
        const settingsButton = document.querySelector('#adminMain .horizontal-tab-button:nth-child(2)'); // Existing Settings button
        const databaseButton = document.querySelector('#adminMain .horizontal-tab-button:nth-child(3)'); // NEW: Database button
        // Add references for other admin sub-tab buttons here if they exist

        // Get references to the content sections
        const adminProfileSection = document.getElementById('adminProfile');
        const adminSetSection = document.getElementById('adminSet'); // Existing Settings section
        const adminDatabaseSection = document.getElementById('adminDatabase'); // NEW: Database section
        // Add references for other admin sub-tab sections here if they exist

        // Function to handle showing the correct sub-sub-tab within Admin
        window.openAdminSubTab = function(tabId) { // Made global for direct access from HTML onclick
            console.log(`admin_main.js: openAdminSubTab called for: ${tabId}`);

            // Deactivate all horizontal tab buttons within Admin
            if (profileButton) profileButton.classList.remove('active');
            if (settingsButton) settingsButton.classList.remove('active'); // Deactivate Settings button
            if (databaseButton) databaseButton.classList.remove('active'); // NEW: Deactivate Database button
            // Deactivate other admin sub-tab buttons here

            // Hide all content sections within Admin by adding 'hidden'
            if (adminProfileSection) adminProfileSection.classList.add('hidden');
            if (adminSetSection) adminSetSection.classList.add('hidden'); // Hide Settings section
            if (adminDatabaseSection) adminDatabaseSection.classList.add('hidden'); // NEW: Hide Database section
            // Hide other admin sub-tab sections here

            // Show the selected section and activate its button
            let initializerToCall = null;

            if (tabId === 'adminProfile') {
                if (adminProfileSection) adminProfileSection.classList.remove('hidden');
                if (profileButton) profileButton.classList.add('active');
                initializerToCall = window.tabInitializerMap.get('adminProfile'); // Get initializer for admin_profile.js
            } else if (tabId === 'adminSet') { // Logic for Settings tab
                if (adminSetSection) adminSetSection.classList.remove('hidden');
                if (settingsButton) settingsButton.classList.add('active');
                initializerToCall = window.tabInitializerMap.get('adminSet'); // Get initializer for admin_set.js
            } else if (tabId === 'adminDatabase') { // NEW: Logic for Database tab
                if (adminDatabaseSection) adminDatabaseSection.classList.remove('hidden');
                if (databaseButton) databaseButton.classList.add('active');
                initializerToCall = window.tabInitializerMap.get('adminDatabase'); // Get initializer for admin_database.js
            }
            // Add logic for other admin sub-tabs here

            // Execute the specific initializer for the tab content
            if (initializerToCall) {
                initializerToCall();
            } else {
                console.warn(`admin_main.js: Initializer not found for tabId: ${tabId}. Ensure it's registered.`);
            }
            window.hideMessage(); // Hide any general messages
        }; // End of openAdminSubTab function

        // Attach event listeners to the horizontal tab buttons
        if (profileButton) {
            profileButton.addEventListener('click', () => window.openAdminSubTab('adminProfile'));
        } else {
            console.error("admin_main.js: Profile tab button not found. Event listener not attached.");
        }
        if (settingsButton) { // Attach listener for Settings button
            settingsButton.addEventListener('click', () => window.openAdminSubTab('adminSet'));
        } else {
            console.error("admin_main.js: Settings tab button not found. Event listener not attached.");
        }
        if (databaseButton) { // NEW: Attach listener for Database button
            databaseButton.addEventListener('click', () => window.openAdminSubTab('adminDatabase'));
        } else {
            console.error("admin_main.js: Database tab button not found. Event listener not attached.");
        }
        // Attach event listeners for other admin sub-tab buttons here

        // On initial load of 'adminMain', default to showing 'adminProfile'
        // If a specific tab needs to be pre-selected, change this.
        window.openAdminSubTab('adminProfile');
    });

} else {
    console.error("admin_main.js: window.registerTabInitializer is not defined. Ensure main.js is loaded first.");
}
