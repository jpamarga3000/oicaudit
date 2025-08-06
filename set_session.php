<?php
// set_session.php
session_start();

header('Content-Type: application/json');

$response = ['success' => false, 'message' => 'Invalid request.'];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $loggedin = isset($_POST['loggedin']) ? ($_POST['loggedin'] === 'true' ? true : false) : false;
    
    // Retrieve all user data sent from the frontend
    $firstName = isset($_POST['firstName']) ? $_POST['firstName'] : '';
    $lastName = isset($_POST['lastName']) ? $_POST['lastName'] : '';
    $contactNumber = isset($_POST['contactNumber']) ? $_POST['contactNumber'] : '';
    $birthdate = isset($_POST['birthdate']) ? $_POST['birthdate'] : '';
    $email = isset($_POST['email']) ? $_POST['email'] : '';
    $username = isset($_POST['username']) ? $_POST['username'] : '';
    $approvedStatus = isset($_POST['approvedStatus']) ? $_POST['approvedStatus'] : '';
    $accessCode = isset($_POST['accessCode']) ? $_POST['accessCode'] : '';
    $branch = isset($_POST['branch']) ? $_POST['branch'] : '';

    if ($loggedin) {
        $_SESSION['loggedin'] = true;
        $_SESSION['first_name'] = $firstName;
        $_SESSION['last_name'] = $lastName;
        $_SESSION['contact_number'] = $contactNumber;
        $_SESSION['birthdate'] = $birthdate;
        $_SESSION['email'] = $email;
        $_SESSION['username'] = $username;
        $_SESSION['approved_status'] = $approvedStatus;
        $_SESSION['access_code'] = $accessCode;
        $_SESSION['branch'] = $branch;

        $response = ['success' => true, 'message' => 'Session set successfully.'];
    } else {
        // If loggedin is explicitly false, destroy session (e.g., for logout)
        session_unset();
        session_destroy();
        $response = ['success' => true, 'message' => 'Session destroyed successfully.'];
    }
}

echo json_encode($response);
?>
