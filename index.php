<?php
// Force all errors to be displayed and logged for debugging
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
ini_set('log_errors', 1);
ini_set('error_log', 'C:/xampp/php/logs/php_error_debug.log'); // Use a specific debug log file

// index.php (Revised for Login and Debugging)
session_start(); // Start the session at the very beginning

// Check if the user is logged in
if (!isset($_SESSION['loggedin']) || $_SESSION['loggedin'] !== true) {
    // If not logged in, redirect to the login page
    header('Location: login.php');
    exit; // Stop further script execution
}

// If logged in, include the header and main content
include 'includes/header.php';

// Include the new home page as the default landing page after login
include 'pages/home.php';

// --- Main content pages as top-level tabs ---
// All pages should now be included.

include 'pages/audit_tool_main_page.php';
include 'pages/trnm_main.php';
include 'pages/gl_main.php';
include 'pages/lnacc_main.php';
include 'pages/svacc_main.php';
include 'pages/actg_main.php';
include 'pages/monitoring_main.php';
include 'pages/admin_main.php'; // NEW: Include the Admin main page
include 'pages/operations_main.php';



// Removed direct includes for wp_lr_collaterals.php, wp_lr_documents.php, wp_lr_reference.php
// as they are included within wp_lr_main.php.

?>
<div id="message"></div>
<?php
include 'includes/footer.php';
?>
