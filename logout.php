<?php
// logout.php
session_start();

// Unset all session variables
$_SESSION = array();

// Check if the logout reason is due to inactivity
if (isset($_GET['reason']) && $_GET['reason'] === 'inactivity') {
    $_SESSION['logout_message'] = 'You have been logged out due to 10 minutes of inactivity.';
    $_SESSION['logout_message_type'] = 'logout-inactivity'; // Custom type for styling
}

// Destroy the session
session_destroy();

// Redirect to the login page
header("Location: login.php");
exit;
?>
