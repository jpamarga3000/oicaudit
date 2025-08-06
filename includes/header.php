<?php
// includes/header.php (Revised: Added Monitoring tab and sub-tabs, profile picture next to greeting and dynamic mobile menu top and Inactivity Logout)

// Ensure session is started, although index.php should handle this
if (session_status() == PHP_SESSION_NONE) {
    session_start();
}

// Determine profile picture path - this will be handled by JS for dynamic loading
// PHP will just provide a default placeholder.
$profilePicPath = 'https://placehold.co/32x32/cbd5e1/475569?text=P'; // Default placeholder

// Get username and access_code from session for fetching profile picture and client-side access control
$loggedInUsername = isset($_SESSION['username']) ? htmlspecialchars($_SESSION['username']) : ''; // CORRECTED: Use $_SESSION['username']
$loggedInFirstName = isset($_SESSION['first_name']) ? htmlspecialchars($_SESSION['first_name']) : ''; // NEW: Keep first name for greeting
$userAccessCode = isset($_SESSION['access_code']) ? htmlspecialchars($_SESSION['access_code']) : ''; // Get access code

// Expose userAccessCode globally for JavaScript
echo "<script>window.userAccessCode = '{$userAccessCode}';</script>";
// Expose loggedInUsername globally for JavaScript (for profile picture lookup)
echo "<script>window.loggedInUser = '{$loggedInUsername}';</script>"; // NEW: Expose actual username
echo "<script>window.loggedInUsername = '{$loggedInUsername}';</script>"; // Expose for main.js to pick up

// REMOVED: Redundant definition of window.FLASK_API_BASE_URL as it's now centralized in utils.js
// echo "<script>window.FLASK_API_BASE_URL = 'http://localhost:5000';</script>";

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audit Management System</title>
    <!-- Favicon link added here -->
    <link rel="icon" type="image/png" href="images/logo_sol.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="css/style.css">
    <link rel="stylesheet" href="css/actg.css">
    <link rel="stylesheet" href="css/header_nav.css">
    <link rel="stylesheet" href="css/operations_dc.css"> <link rel="stylesheet" href="css/operations_soa.css"> <link rel="stylesheet" href="css/operations_dosri.css"> <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <script src="js/utils.js"></script>
    <script src="js/main.js"></script>

    <style>
        /* Responsive adjustments for header elements to prevent overlapping */
        @media (max-width: 768px) { /* Adjust breakpoint as needed for mobile */
            #main-header {
                height: auto; /* Allow header height to adjust if items wrap */
                flex-wrap: wrap; /* Allow main header items to wrap if they exceed available space */
                padding-top: 1rem;
                padding-bottom: 1rem;
                align-items: flex-start; /* Align content at the start when wrapped */
            }

            /* Target the logo/title section */
            #main-header > div:first-child { /* This targets the logo and title div */
                flex-basis: 100%; /* Force it to take full width and move to new line */
                justify-content: center; /* Center content horizontally */
                margin-bottom: 0.5rem; /* Add space below if it wraps */
                /* Ensure no absolute positioning or transforms interfere */
                position: relative; /* Changed from static to relative to maintain flow but allow z-index if needed */
                transform: none;
                left: auto;
                top: auto;
            }

            /* Target the user info/logout/hamburger section */
            #main-header > div:last-child { /* This targets the user info, logout, and hamburger div */
                flex-basis: 100%; /* Force it to take full width and move to new line */
                justify-content: center; /* Center content horizontally */
                margin-top: 0.5rem; /* Add space above if it wraps */
                /* Ensure no absolute positioning or transforms interfere */
                position: relative; /* Changed from static to relative to maintain flow but allow z-index if needed */
                transform: none;
                right: auto;
                top: auto;
            }

            /* Further adjustments for elements within the right section if needed */
            #main-header .user-greeting { /* "Hello, Joseph Patrick!" text */
                white-space: normal; /* Allow text to wrap */
                text-align: center; /* Center the text */
                flex-grow: 1; /* Allow it to take available space */
                margin-right: 0; /* Remove specific right margin */
                order: 1; /* Ensure greeting comes first if elements wrap */
            }

            #main-header .logout-button {
                margin-left: 0.5rem; /* Add some space if needed */
                margin-right: 0.5rem; /* Add some space if needed */
                order: 2; /* Ensure logout button comes second */
            }
            
            #main-header .hamburger-menu-icon {
                margin-left: 0.5rem; /* Add some space if needed */
                order: 3; /* Ensure hamburger icon comes last in its row */
                z-index: 101; /* Ensure it's above other header elements */
            }

            /* Mobile Navigation Menu - Adjust pointer-events for proper interaction */
            .mobile-nav-menu {
                pointer-events: none; /* Disable pointer events when menu is hidden */
            }

            .mobile-nav-menu.active {
                pointer-events: auto; /* Enable pointer events when menu is active */
            }
        }
    </style>

</head>
<body class="min-h-screen flex flex-col">
    <div class="container flex-grow flex-col">
        <header id="main-header" class="top-nav-bar relative">
            <div class="flex items-center">
                <img src="images/logo.png" alt="Audit Tool Logo" class="h-8 mr-3">
                <span class="text-black text-xl font-bold whitespace-nowrap">Audit Management System</span>
            </div>

            <div class="flex items-center space-x-4">
                <?php if (isset($_SESSION['first_name'])): ?>
                    <span class="text-gray-700 text-lg user-greeting">Hello, <span class="font-semibold"><?php echo $loggedInFirstName; ?></span>!</span> <!-- Display first name for greeting -->
                    <!-- Profile picture placeholder - will be updated by JS -->
                    <img id="headerProfilePic" src="<?php echo $profilePicPath; ?>" alt="Profile Picture" class="header-profile-pic">
                    <!-- Hidden input to pass username to JavaScript -->
                    <input type="hidden" id="loggedInUsername" value="<?php echo $loggedInUsername; ?>">
                <?php endif; ?>
                
                <a href="logout.php" class="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded text-sm transition duration-150 ease-in-out logout-button">
                    Logout
                </a>
                <button class="hamburger-menu-icon" id="openMobileMenu">
                    <i class="fas fa-bars"></i>
                </button>
            </div>

            <nav class="centered-nav-items">
                <div class="tab-item has-submenu">
                    <button class="tab-button active" onclick="openTab('auditToolMainPage')">
                        <i class="fas fa-cogs mr-2"></i> Audit Tool
                    </button>
                    <div class="submenu-container" id="auditToolSubmenu">
                        <button class="submenu-item" onclick="openSubTab('auditToolMainPage', 'agingConsolidatedSection')">Aging Consolidated</button>
                        <button class="submenu-item" onclick="openSubTab('auditToolMainPage', 'pettyCashSection')">Petty Cash</button>

                        <div class="nested-tab-item has-submenu">
                            <button class="nested-tab-button" onclick="toggleNestedSubmenu(event, 'trnmSubmenuNested')">TRNM</button>
                            <div class="nested-submenu-container" id="trnmSubmenuNested">
                                <button class="submenu-item" onclick="openSubTab('trnmMain', 'combine', event.currentTarget)">DOS Combine CSV</button>
                                <button class="submenu-item" onclick="openSubTab('trnmMain', 'convert', event.currentTarget)">DOS DBF to CSV</button>
                                <button class="submenu-item" onclick="openSubTab('trnmMain', 'win', event.currentTarget)">WIN</button>
                            </div>
                        </div>

                        <div class="nested-tab-item has-submenu">
                            <button class="nested-tab-button" onclick="toggleNestedSubmenu(event, 'glSubmenuNested')">GL Processing </button>
                            <div class="nested-submenu-container" id="glSubmenuNested">
                                <button class="submenu-item" onclick="openSubTab('glMain', 'glDos', event.currentTarget)">Process DOS Files</button>
                                <button class="submenu-item" onclick="openSubTab('glMain', 'glWin', event.currentTarget)">Process WIN Files</button>
                            </div>
                        </div>

                        <div class="nested-tab-item has-submenu">
                            <button class="nested-tab-button" onclick="toggleNestedSubmenu(event, 'lnaccSubmenuNested')">LNACC Processing </button>
                            <div class="nested-submenu-container" id="lnaccSubmenuNested">
                                <button class="submenu-item" onclick="openSubTab('lnaccMain', 'lnaccDos', event.currentTarget)">Process DOS Files</button>
                                <button class="submenu-item" onclick="openSubTab('lnaccMain', 'lnaccWin', event.currentTarget)">Process WIN Files</button>
                            </div>
                        </div>

                        <div class="nested-tab-item has-submenu">
                            <button class="nested-tab-button" onclick="toggleNestedSubmenu(event, 'svaccSubmenuNested')">SVACC Processing </button>
                            <div class="nested-submenu-container" id="svaccSubmenuNested"> <!-- Corrected ID here -->
                                <button class="submenu-item" onclick="openSubTab('svaccMain', 'svaccDos', event.currentTarget)">Process DOS Files</button>
                                <button class="submenu-item" onclick="openSubTab('svaccMain', 'svaccWin', event.currentTarget)">Process WIN Files</button>
                            </div>
                        </div>
                        <button class="submenu-item" onclick="openSubTab('auditToolMainPage', 'journalVoucherSection')">Journal Voucher</button>
                        <!-- NEW: Trial Balance Processing submenu item -->
                        <button class="submenu-item" onclick="openSubTab('auditToolMainPage', 'auditToolTbSection')">Trial Balance Processing</button>
                    </div>
                </div>

                <div class="tab-item has-submenu">
                    <button class="tab-button" onclick="openTab('actgMain')">
                        <i class="fas fa-calculator mr-2"></i> Accounting
                    </button>
                    <div class="submenu-container" id="accountingSubmenu">
                        <button class="submenu-item" onclick="openSubTab('actgMain', 'actgGl', event.currentTarget)">General Ledger</button>
                        <button class="submenu-item" onclick="openSubTab('actgMain', 'actgTb', event.currentTarget)">Trial Balance</button>
                        <button class="submenu-item" onclick="openSubTab('actgMain', 'actgRef', event.currentTarget)">Reference</button>
                        <button class="submenu-item" onclick="openSubTab('actgMain', 'actgDesc', event.currentTarget)">Description</button>
                        <button class="submenu-item" onclick="openSubTab('actgMain', 'actgTrend', event.currentTarget)">Trend</button>
                        <button class="submenu-item" onclick="openSubTab('actgMain', 'actgFs', event.currentTarget)">FS</button>
                    </div>
                </div>

                <div class="tab-item has-submenu">
                    <button class="tab-button" onclick="openTab('operationsMain')">
                        <i class="fas fa-tasks mr-2"></i> Operations
                    </button>
                    <div class="submenu-container" id="operationsSubmenu">
                        <button class="submenu-item" onclick="openSubTab('operationsMain', 'operationsAgingReport', event.currentTarget)">Aging Report</button>
                        <button class="submenu-item" onclick="openSubTab('operationsMain', 'operationsStatementOfAccount', event.currentTarget)">Statement Of Account</button>
                        <button class="submenu-item" onclick="openSubTab('operationsMain', 'operationsDepositCounterpart', event.currentTarget)">Deposit Counterpart</button>
                        <button class="submenu-item" onclick="openSubTab('operationsMain', 'operationsDepositLiabilities', event.currentTarget)">Deposit Liabilities</button>
                        <button class="submenu-item" onclick="openSubTab('operationsMain', 'operationsDosri', event.currentTarget)">DOSRI</button>
                        <button class="submenu-item" onclick="openSubTab('operationsMain', 'operationsRestructuredLoan', event.currentTarget)">Restructured Loan</button> <!-- NEW: Restructured Loan Menu Item -->
                    </div>
                </div>

                <!-- NEW: Monitoring main tab with new sub-tab -->
                <div class="tab-item has-submenu">
                    <button class="tab-button" onclick="openTab('monitoringMain')">
                        <i class="fas fa-eye mr-2"></i> Monitoring
                    </button>
                    <div class="submenu-container" id="monitoringSubmenu">
                        <button class="submenu-item" onclick="openSubTab('monitoringMain', 'monRegAud', event.currentTarget)">Regular Audit</button>
                        <button class="submenu-item" onclick="openSubTab('monitoringMain', 'monSpeAud', event.currentTarget)">Special Audit</button>
                    </div>
                </div>

                <div class="tab-item has-submenu">
                    <button class="tab-button" onclick="openMobileTabAndToggleSubmenu(event, 'adminMain', 'adminMobileSubmenu')">
                        <i class="fas fa-user-shield mr-2"></i> Admin
                    </button>
                    <div class="submenu-container" id="adminSubmenu">
                        <button class="submenu-item" onclick="openSubTab('adminMain', 'adminProfile')">Profile</button>
                        <button class="submenu-item" onclick="openSubTab('adminMain', 'adminSet')">Settings</button> <!-- NEW: Settings Submenu Item -->
                        <button class="submenu-item" onclick="openSubTab('adminMain', 'adminDatabase')">Database</button> <!-- NEW: Database Submenu Item -->
                    </div>
                </div>
            </nav>
        </header>

        <div class="mobile-nav-menu" id="mobileNavMenu">
            <div class="tab-item has-submenu">
                <button class="tab-button" onclick="openMobileTabAndToggleSubmenu(event, 'auditToolMainPage', 'auditToolMobileSubmenu')">
                    <i class="fas fa-cogs mr-2"></i> Audit Tool
                </button>
                <div class="submenu-container" id="auditToolMobileSubmenu">
                    <button class="submenu-item" onclick="openMobileSubTab('auditToolMainPage', 'agingConsolidatedSection')">Aging Consolidated</button>
                    <button class="submenu-item" onclick="openMobileSubTab('auditToolMainPage', 'pettyCashSection')">Petty Cash</button>

                    <div class="nested-tab-item has-submenu">
                        <button class="nested-tab-button" onclick="toggleMobileNestedSubmenu(event, 'trnmMobileNested')">TRNM</button>
                        <div class="nested-submenu-container" id="trnmMobileNested">
                            <button class="submenu-item" onclick="openMobileSubTab('trnmMain', 'combine')">DOS Combine CSV</button>
                            <button class="submenu-item" onclick="openMobileSubTab('trnmMain', 'convert')">DOS DBF to CSV</button>
                            <button class="submenu-item" onclick="openMobileSubTab('trnmMain', 'win')">WIN</button>
                        </div>
                    </div>

                    <div class="nested-tab-item has-submenu">
                        <button class="nested-tab-button" onclick="toggleMobileNestedSubmenu(event, 'glMobileNested')">GL Processing </button>
                        <div class="nested-submenu-container" id="glMobileNested">
                            <button class="submenu-item" onclick="openMobileSubTab('glMain', 'glDos')">DOS</button>
                            <button class="submenu-item" onclick="openMobileSubTab('glMain', 'glWin')">WIN</button>
                        </div>
                    </div>

                    <div class="nested-tab-item has-submenu">
                        <button class="nested-tab-button" onclick="toggleMobileNestedSubmenu(event, 'lnaccMobileNested')">LNACC Processing </button>
                        <div class="nested-submenu-container" id="lnaccMobileNested">
                            <button class="submenu-item" onclick="openMobileSubTab('lnaccMain', 'lnaccDos')">DOS</button>
                            <button class="submenu-item" onclick="openMobileSubTab('lnaccMain', 'lnaccWin')">WIN</button>
                        </div>
                    </div>

                    <div class="nested-tab-item has-submenu">
                        <button class="nested-tab-button" onclick="toggleMobileNestedSubmenu(event, 'svaccMobileNested')">SVACC Processing </button>
                        <div class="nested-submenu-container" id="svaccMobileNested"> <!-- Corrected ID here -->
                            <button class="submenu-item" onclick="openMobileSubTab('svaccMain', 'svaccDos')">DOS</button>
                            <button class="submenu-item" onclick="openMobileSubTab('svaccMain', 'svaccWin')">WIN</button>
                        </div>
                    </div>
                    <button class="submenu-item" onclick="openMobileSubTab('auditToolMainPage', 'journalVoucherSection')">Journal Voucher</button>
                    <!-- NEW: Trial Balance Processing submenu item for mobile -->
                    <button class="submenu-item" onclick="openMobileSubTab('auditToolMainPage', 'auditToolTbSection')">Trial Balance</button>
                </div>
            </div>

            <div class="tab-item has-submenu">
                <button class="tab-button" onclick="openMobileTabAndToggleSubmenu(event, 'actgMain', 'accountingMobileSubmenu')">
                    <i class="fas fa-calculator mr-2"></i> Accounting
                </button>
                <div class="submenu-container" id="accountingMobileSubmenu">
                    <button class="submenu-item" onclick="openMobileSubTab('actgMain', 'actgGl')">General Ledger</button>
                    <button class="submenu-item" onclick="openMobileSubTab('actgMain', 'actgTb')">Trial Balance</button>
                    <button class="submenu-item" onclick="openMobileSubTab('actgMain', 'actgRef')">Reference</button>
                    <button class="submenu-item" onclick="openMobileSubTab('actgMain', 'actgDesc')">Description</button>
                    <button class="submenu-item" onclick="openMobileSubTab('actgMain', 'actgTrend')">Trend</button>
                    <button class="submenu-item" onclick="openMobileSubTab('actgMain', 'actgFs')">FS</button>
                </div>
            </div>

            <div class="tab-item has-submenu">
                <button class="tab-button" onclick="openMobileTabAndToggleSubmenu(event, 'operationsMain', 'operationsMobileSubmenu')">
                    <i class="fas fa-tasks mr-2"></i> Operations
                </button>
                <div class="submenu-container" id="operationsMobileSubmenu">
                    <button class="submenu-item" onclick="openMobileSubTab('operationsMain', 'operationsAgingReport')">Aging Report</button>
                    <button class="submenu-item" onclick="openMobileSubTab('operationsMain', 'operationsStatementOfAccount')">Statement Of Account</button>
                    <button class="submenu-item" onclick="openMobileSubTab('operationsMain', 'operationsDepositCounterpart')">Deposit Counterpart</button>
                    <button class="submenu-item" onclick="openMobileSubTab('operationsMain', 'operationsDepositLiabilities')">Deposit Liabilities</button>
                    <button class="submenu-item" onclick="openMobileSubTab('operationsMain', 'operationsDosri')">DOSRI</button>
                    <button class="submenu-item" onclick="openMobileSubTab('operationsMain', 'operationsRestructuredLoan')">Restructured Loan</button> <!-- NEW: Restructured Loan Mobile Menu Item -->
                </div>
            </div>

            <!-- NEW: Monitoring mobile tab with new sub-tab -->
            <div class="tab-item has-submenu">
                <button class="tab-button" onclick="openMobileTabAndToggleSubmenu(event, 'monitoringMain', 'monitoringMobileSubmenu')">
                    <i class="fas fa-eye mr-2"></i> Monitoring
                </button>
                <div class="submenu-container" id="monitoringMobileSubmenu">
                    <button class="submenu-item" onclick="openMobileSubTab('monitoringMain', 'monRegAud')">Regular Audit</button>
                    <button class="submenu-item" onclick="openMobileSubTab('monitoringMain', 'monSpeAud')">Special Audit</button>
                </div>
            </div>

            <div class="tab-item has-submenu">
                <button class="tab-button" onclick="openMobileTabAndToggleSubmenu(event, 'adminMain', 'adminMobileSubmenu')">
                    <i class="fas fa-user-shield mr-2"></i> Admin
                </button>
                <div class="submenu-container" id="adminMobileSubmenu">
                    <button class="submenu-item" onclick="openMobileSubTab('adminMain', 'adminProfile')">Profile</button>
                    <button class="submenu-item" onclick="openMobileSubTab('adminMain', 'adminSet')">Settings</button> <!-- NEW: Settings Submenu Item for Mobile -->
                    <button class="submenu-item" onclick="openMobileSubTab('adminMain', 'adminDatabase')">Database</button> <!-- NEW: Database Submenu Item for Mobile -->
                </div>
            </div>
        </div>

        <div class="main-content-area pt-0 mt-0"> <div class="tab-content-wrapper">
<script>
    // Inactivity Logout Logic
    const INACTIVITY_TIMEOUT = 10 * 60 * 1000; // 10 minutes in milliseconds
    let inactivityTimer;

    function resetInactivityTimer() {
        clearTimeout(inactivityTimer);
        inactivityTimer = setTimeout(logoutDueToInactivity, INACTIVITY_TIMEOUT);
    }

    function logoutDueToInactivity() {
        // Check if the user is currently logged in (based on PHP session status)
        // This requires a PHP endpoint to check session, or relying purely on client-side JS.
        // For simplicity and direct control, we'll redirect to logout.php with a parameter.
        window.location.href = 'logout.php?reason=inactivity';
    }

    // Attach event listeners to reset the timer on user activity
    document.addEventListener('mousemove', resetInactivityTimer);
    document.addEventListener('keydown', resetInactivityTimer);
    document.addEventListener('click', resetInactivityTimer);
    document.addEventListener('scroll', resetInactivityTimer); // Also consider scroll

    // Start the timer when the page loads
    resetInactivityTimer();

    // Existing header JS logic below...

    function adjustMobileMenuPosition() {
        const mainHeader = document.getElementById('main-header');
        const mobileNavMenu = document.getElementById('mobileNavMenu');
        if (mainHeader && mobileNavMenu) {
            const headerHeight = mainHeader.offsetHeight;
            // Use !important to override any conflicting CSS rules
            mobileNavMenu.style.setProperty('top', `${headerHeight}px`, 'important');
            mobileNavMenu.style.setProperty('height', `calc(100vh - ${headerHeight}px)`, 'important');
        }
    }

    // Function to close the mobile navigation menu
    function closeMobileNavMenu() {
        const mobileNavMenu = document.getElementById('mobileNavMenu');
        const openMobileMenuButton = document.getElementById('openMobileMenu');
        if (mobileNavMenu) {
            mobileNavMenu.classList.remove('active');
            document.body.classList.remove('menu-open'); // Remove class to re-enable scrolling
            // Restore hamburger icon if it was changed
            if (openMobileMenuButton) {
                openMobileMenuButton.innerHTML = '<i class="fas fa-bars"></i>';
            }
        }
    }

    // Add event listener to the mobile menu to close it when a link/button is clicked
    const mobileNavMenu = document.getElementById('mobileNavMenu');
    if (mobileNavMenu) {
        mobileNavMenu.addEventListener('click', function(event) {
            // Check if a tab-button, nested-tab-button, or submenu-item was clicked
            const target = event.target;
            if (target.matches('.tab-button') || target.matches('.nested-tab-button') || target.matches('.submenu-item')) {
                // Only close the menu if it's not a nested-tab-button that is toggling a submenu
                // The toggleMobileNestedSubmenu function handles opening/closing nested submenus
                if (!target.matches('.nested-tab-button') || !target.classList.contains('active')) {
                    closeMobileNavMenu();
                }
            }
        });
    }


    // Initial adjustment
    adjustMobileMenuPosition();

    // Adjust on window resize
    window.addEventListener('resize', adjustMobileMenuPosition);

    // Optional: Also adjust if content inside header changes (e.g., dynamic elements loading)
    // This might require a MutationObserver for more complex scenarios, but resize is usually sufficient.
</script>


