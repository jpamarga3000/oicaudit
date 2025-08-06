// js/tabs/bank_reconciliation.js

(function() { // Start IIFE

    /**
     * Initializes the Bank Reconciliation sub-sub-tab.
     * This function is called by main.js when the sub-sub-tab is activated.
     */
    function initBankReconciliationTab() {
        console.log('Initializing Bank Reconciliation Tab...');
        // Add any specific initialization logic for the Bank Reconciliation tab here.
        // For example, loading data, attaching event listeners to its forms/buttons, etc.
    }

    // Register this sub-sub-tab's initializer with the main application logic
    // The ID 'bankReconciliation' must match the div ID in bank_reconciliation.php
    registerTabInitializer('bankReconciliation', initBankReconciliationTab);

})(); // End IIFE
