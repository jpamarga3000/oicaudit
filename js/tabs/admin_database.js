// audit_tool/js/tabs/admin_database.js

// Ensure window.registerTabInitializer is available from main.js
if (window.registerTabInitializer) {
    window.registerTabInitializer('adminDatabase', function() {
        console.log("admin_database.js: Initializing Database Summary Tab.");

        const databaseSummaryTableBody = document.getElementById('databaseSummaryTableBody');
        const refreshButton = document.getElementById('refreshDatabaseSummaryBtn');

        // Function to format date from YYYY-MM-DD to MM-DD-YY
        function formatDateToMMDDYY(dateString) {
            if (!dateString) return '';
            // The backend is now returning MM/DD/YYYY, so we can directly use it
            // If the backend ever changes to YYYY-MM-DD, this conversion would be needed:
            // const date = new Date(dateString);
            // if (isNaN(date)) return dateString; // Return original if invalid date
            // const month = (date.getMonth() + 1).toString().padStart(2, '0');
            // const day = date.getDate().toString().padStart(2, '0');
            // const year = date.getFullYear().toString().slice(-2);
            // return `${month}-${day}-${year}`;
            return dateString; // Assuming backend now sends MM/DD/YYYY directly
        }

        async function fetchDatabaseSummary(forceRefresh = false) { // Added forceRefresh parameter
            window.showMessage('Loading database summary...', 'loading');
            // Updated colspan to 8 to account for the new TB column
            databaseSummaryTableBody.innerHTML = '<tr><td colspan="8" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">Loading data...</td></tr>';

            try {
                // Construct the URL with force_refresh parameter if true
                const url = `${window.FLASK_API_BASE_URL}/get_database_summary${forceRefresh ? '?force_refresh=true' : ''}`;

                const response = await fetch(url, { // Use the constructed URL
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || 'Failed to fetch database summary.');
                }

                const data = await response.json();
                console.log("Database Summary Data:", data);

                // Clear existing rows
                databaseSummaryTableBody.innerHTML = '';

                if (data.success && data.data.length > 0) {
                    data.data.forEach(row => {
                        const tr = document.createElement('tr');
                        tr.className = 'hover:bg-gray-100';
                        tr.innerHTML = `
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${row.BRANCH}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">${row.TRNM || ''}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">${row.SVACC || ''}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">${row.LNACC || ''}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">${row.GL || ''}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">${row.ACCLIST || ''}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">${row.AGING || ''}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">${row.TB || ''}</td> <!-- NEW: Added TB data cell -->
                        `;
                        databaseSummaryTableBody.appendChild(tr);
                    });
                    window.showMessage('Database summary loaded successfully!', 'success');
                } else {
                    // Updated colspan to 8
                    databaseSummaryTableBody.innerHTML = '<tr><td colspan="8" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">No data available or an error occurred.</td></tr>';
                    window.showMessage(data.message || 'No data available or an error occurred.', 'info');
                }

            } catch (error) {
                console.error('Error fetching database summary:', error);
                // Updated colspan to 8
                databaseSummaryTableBody.innerHTML = '<tr><td colspan="8" class="px-6 py-4 whitespace-nowrap text-center text-red-500">Failed to load data. Please try again.</td></tr>';
                window.showMessage(`Error: ${error.message}`, 'error');
            }
        }

        // Add event listener for the refresh button
        if (refreshButton) {
            refreshButton.addEventListener('click', () => fetchDatabaseSummary(true)); // Pass true to force refresh
        }

        // Fetch data when the tab is initialized/shown (initial load does not force refresh)
        fetchDatabaseSummary(false);
    });
} else {
    console.error("admin_database.js: window.registerTabInitializer is not defined. Ensure main.js is loaded first.");
}
