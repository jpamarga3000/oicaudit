<?php
// pages/home.php - Home page for the Audit Tool
// This page provides an overview of the Internal Audit System with a modern UI/UX.

// Function to read CSV and filter by Access Code
function get_users_by_access_code($access_code) {
    $users = [];
    $file_path = 'C:/xampp/htdocs/audit_tool/db/registered.csv'; // Adjust path as necessary
    if (($handle = fopen($file_path, "r")) !== FALSE) {
        $headers = fgetcsv($handle); // Get header row
        $headers = array_map('trim', $headers); // Trim whitespace from headers

        // Find column indices
        $username_col = array_search('Username', $headers);
        $first_name_col = array_search('First Name', $headers);
        $last_name_col = array_search('Last Name', $headers);
        $access_code_col = array_search('Access Code', $headers);
        $profile_picture_col = array_search('ProfilePicture', $headers);

        if ($username_col === false || $first_name_col === false || $last_name_col === false || $access_code_col === false || $profile_picture_col === false) {
            error_log("Missing required columns in registered.csv: Username, First Name, Last Name, Access Code, ProfilePicture");
            fclose($handle);
            return [];
        }

        while (($data = fgetcsv($handle)) !== FALSE) {
            // Ensure data row has enough columns
            if (count($data) > max($username_col, $first_name_col, $last_name_col, $access_code_col, $profile_picture_col)) {
                if (trim($data[$access_code_col]) === $access_code) {
                    $users[] = [
                        'username' => trim($data[$username_col]),
                        'first_name' => trim($data[$first_name_col]),
                        'last_name' => trim($data[$last_name_col]),
                        'profile_picture' => trim($data[$profile_picture_col])
                    ];
                }
            }
        }
        fclose($handle);
    } else {
        error_log("Failed to open registered.csv at: " . $file_path);
    }
    return $users;
}

// Fetch users for each role
$audit_head = get_users_by_access_code('AH');
$audit_admin = get_users_by_access_code('AA');
$internal_auditors = get_users_by_access_code('IA');

// Default placeholder image
$placeholder_img = 'https://placehold.co/200x200/cbd5e1/475569?text=Profile'; // Updated placeholder size

?>
<link rel="stylesheet" href="css/home.css">

<style>
    /* Custom styles for the committee-member-card within these sections */
    .audit-committee-section .committee-member-card,
    .audit-team-section .committee-member-card {
        padding: 0; /* Remove all padding */
        box-shadow: none !important; /* Remove any shadow, use !important to override */
        border: none !important; /* Remove any border, use !important to override */
        background-color: white; /* Set background to white */
    }

    /* Remove the border from the section titles in these specific sections */
    .audit-committee-section .section-title,
    .audit-team-section .section-title {
        border-bottom: none !important; /* Remove the blue line under the title */
    }

    /* Remove border and shadow from all images */
    .member-image,
    .responsive-image,
    .org-chart-image {
        border: none !important;
        box-shadow: none !important;
    }

    /* Ensure consistent sizing and alignment for team role groups */
    .team-roles-horizontal-container {
        display: flex;
        justify-content: center; /* Center the groups */
        gap: 2rem; /* Space between the groups */
        flex-wrap: wrap; /* Allow wrapping on smaller screens */
    }

    .team-role-group {
        flex: 1; /* Allow groups to grow and shrink */
        min-width: 280px; /* Adjusted min-width for larger images */
        max-width: 350px; /* Adjusted max-width for larger images */
        display: flex;
        flex-direction: column;
        align-items: center; /* Center content within each group */
    }

    .team-members-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 1rem; /* Space between member cards */
        width: 100%; /* Ensure container takes full width of its parent */
    }

    .committee-member-card {
        flex-shrink: 0; /* Prevent cards from shrinking */
        width: 200px; /* Explicitly set width for consistent size, increased */
        min-height: 260px; /* Adjusted minimum height to accommodate larger images and text */
        height: auto; /* Allow height to adjust based on content */
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start; /* Align content to the top */
    }

    .committee-member-card .member-image {
        width: 300px; /* Match the card width, increased */
        height: 300px !important; /* Keep consistent height for images, now with !important */
        object-fit: cover;
        border-radius: 8px; /* Slightly rounded corners for images */
        margin-bottom: 0.5rem;
    }

    .committee-member-card .member-name {
        font-weight: bold;
        margin-bottom: 0.25rem;
        font-size: 1rem; /* Slightly increased font size for names */
    }

    .committee-member-card .member-designation {
        font-size: 0.9rem; /* Slightly increased font size for designations */
        color: #666;
    }

    /* Adjustments for the internal auditors grid */
    .internal-auditors-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); /* 3 columns, responsive, adjusted minmax */
        justify-items: center; /* Center items within grid cells */
        gap: 1rem;
        width: 100%; /* Ensure it takes full width of its section */
        margin-top: 2rem; /* Add some space from the above horizontal groups */
    }

    /* Responsive adjustments for header elements to prevent overlapping */
    @media (max-width: 768px) { /* Adjust breakpoint as needed for mobile */
        #main-header {
            flex-wrap: wrap; /* Allow main header items to wrap if they exceed available space */
            height: auto; /* Allow header height to adjust if items wrap */
            padding-bottom: 0.75rem; /* Add some bottom padding if items wrap */
        }

        /* Assuming a container for user info and logout on the right side of the header */
        #main-header .header-right-section {
            display: flex; /* Ensure it's a flex container */
            flex-wrap: wrap; /* Allow items within this section to wrap */
            justify-content: flex-end; /* Keep elements aligned to the right */
            align-items: center;
            width: 100%; /* Take full width to allow wrapping */
            margin-top: 0.5rem; /* Add some space if it wraps to a new line */
        }

        /* Assuming a class for "Hello, Joseph Patrick!" text */
        #main-header .user-greeting {
            white-space: normal; /* Allow text to wrap */
            min-width: 0; /* Allow shrinking */
            margin-right: 0.5rem; /* Space between greeting and logout button */
        }

        /* Assuming a class for the logout button */
        #main-header .logout-button {
            margin-left: auto; /* Push logout button to the right if it's on a new line */
        }

        /* Adjustments for profile picture if it's part of the wrapping */
        .header-profile-pic {
            margin-right: 0; /* Remove right margin if it's wrapping */
            margin-left: 0.5rem; /* Add left margin if needed */
        }
    }
</style>

<div id="homeMain" class="tab-content p-6 active">
    <div class="home-container">
        <header class="hero-section">
            <h1 class="hero-title">Welcome to the Audit Management System</h1>
            <p class="hero-subtitle">Empowering OIC with Objective Assurance and Consulting Services</p>
        </header>

        <section class="info-section about-section scroll-reveal">
            <div class="info-content">
                <h2 class="section-title">About the Internal Audit Department</h2>
                <p class="section-paragraph">
                    The responsibility of internal auditing in Oro Integrated Cooperative (OIC) is assigned to the office of the Internal Audit Department (IAD).
                    Although the creation of the department was not formalized through a board resolution, its functions were written in the Internal Audit Charter 1st edition approved on February 27, 2016.
                    The Internal Audit Department (IAD or the Department) of OIC bears primary responsibility for audits.
                    IAD conducts audits in accordance with the International Standards for the Professional Practice of Internal Auditing (Standards).
                </p>
            </div>
            <div class="info-image">
                <img src="images/iad_fam.jpg" alt="IAD Family" class="responsive-image">
            </div>
        </section>

        <section class="info-section mission-section scroll-reveal">
            <div class="info-content">
                <h2 class="section-title">Mission</h2>
                <p class="section-paragraph">
                    The IAD’s mission is to enhance and protect the OIC’s value by providing risk-based, objective assurance, and consulting services to improve the effectiveness of governance, risk management, and internal control.
                </p>
                </p>
            </div>
        </section>

        <section class="info-section org-structure-section scroll-reveal">
            <h2 class="section-title">Organizational Structure of IAD</h2>
            <div class="org-chart-image-container">
                <img src="images/org_chart.png" alt="Organizational Chart of IAD" class="org-chart-image">
            </div>
        </section>

        <section class="info-section audit-committee-section scroll-reveal">
            <h2 class="section-title">Audit Committee</h2>
            <div class="committee-members-container">
                <div class="committee-member-card">
                    <img src="images/acchair.jpg" alt="Annalyn S. Jamila" class="member-image">
                    <div class="member-name">ANNALYN S. JAMILA</div>
                    <div class="member-designation">Chairperson</div>
                </div>
                <div class="committee-member-card">
                    <img src="images/acmember1.jpg" alt="Melan Dave C. Lalucan" class="member-image">
                    <div class="member-name">MELAN DAVE C. LALUCAN</div>
                    <div class="member-designation">Member</div>
                </div>
                <div class="committee-member-card">
                    <img src="images/acmember2.jpg" alt="Antonio T. Cagulang III" class="member-image">
                    <div class="member-name">ANTONIO T. CAGULANG III</div>
                    <div class="member-designation">Member</div>
                </div>
            </div>
        </section>

        <!-- NEW: Meet the Audit Team Section - Reordered and restructured for horizontal layout -->
        <section class="info-section audit-team-section scroll-reveal">
            <h2 class="section-title full-width-title">Meet the Audit Team</h2>

            <div class="team-roles-horizontal-container">
                <!-- Internal Audit Head -->
                <div class="team-role-group">
                    <div class="team-members-container">
                        <?php if (!empty($audit_head)): ?>
                            <?php foreach ($audit_head as $member): ?>
                                <div class="committee-member-card">
                                    <?php
                                        $img_src = !empty($member['profile_picture']) ? 'images/profile/' . htmlspecialchars($member['profile_picture']) : $placeholder_img;
                                    ?>
                                    <img src="<?php echo $img_src; ?>" alt="<?php echo htmlspecialchars($member['first_name'] . ' ' . $member['last_name']); ?>" class="member-image">
                                    <div class="member-name"><?php echo htmlspecialchars(strtoupper($member['first_name'] . ' ' . $member['last_name'])); ?></div>
                                    <div class="member-designation">Internal Audit Head</div>
                                </div>
                            <?php endforeach; ?>
                        <?php else: ?>
                            <p class="text-gray-600">No Internal Audit Head found.</p>
                        <?php endif; ?>
                    </div>
                </div>

                <!-- Audit Admin -->
                <div class="team-role-group">
                    <div class="team-members-container">
                        <?php if (!empty($audit_admin)): ?>
                            <?php foreach ($audit_admin as $member): ?>
                                <div class="committee-member-card">
                                    <?php
                                        $img_src = !empty($member['profile_picture']) ? 'images/profile/' . htmlspecialchars($member['profile_picture']) : $placeholder_img;
                                    ?>
                                    <img src="<?php echo $img_src; ?>" alt="<?php echo htmlspecialchars($member['first_name'] . ' ' . $member['last_name']); ?>" class="member-image">
                                    <div class="member-name"><?php echo htmlspecialchars(strtoupper($member['first_name'] . ' ' . $member['last_name'])); ?></div>
                                    <div class="member-designation">Audit Admin</div>
                                </div>
                            <?php endforeach; ?>
                        <?php else: ?>
                            <p class="text-gray-600">No Audit Admin found.</p>
                        <?php endif; ?>
                    </div>
                </div>
            </div> <!-- End team-roles-horizontal-container -->

            <!-- Internal Auditor(s) - This section remains vertical within the main flow but its members are 3-per-row -->
            <div class="team-members-container internal-auditors-grid">
                <?php if (!empty($internal_auditors)): ?>
                    <?php foreach ($internal_auditors as $member): ?>
                        <div class="committee-member-card">
                            <?php
                                $img_src = !empty($member['profile_picture']) ? 'images/profile/' . htmlspecialchars($member['profile_picture']) : $placeholder_img;
                            ?>
                            <img src="<?php echo $img_src; ?>" alt="<?php echo htmlspecialchars($member['first_name'] . ' ' . $member['last_name']); ?>" class="member-image">
                            <div class="member-name"><?php echo htmlspecialchars(strtoupper($member['first_name'] . ' ' . $member['last_name'])); ?></div>
                            <div class="member-designation">Internal Auditor</div>
                        </div>
                    <?php endforeach; ?>
                <?php else: ?>
                    <p class="text-gray-600">No Internal Auditors found.</p>
                <?php endif; ?>
            </div>
        </section>

    </div>
</div>

<script>
    // Ensure the home tab is active when loaded
    document.addEventListener('DOMContentLoaded', function() {
        // Function to simulate clicking a tab button and showing its content
        function activateTab(tabId) {
            // Remove 'active' class from all tab buttons and hide all tab contents
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            // Add 'active' class to the specific tab button (if exists)
            const correspondingButton = document.querySelector(`.tab-button[onclick*="openTab('${tabId}')"]`);
            if (correspondingButton) {
                correspondingButton.classList.add('active');
            }

            // Show the specific tab content
            const tabContent = document.getElementById(tabId);
            if (tabContent) {
                tabContent.classList.add('active');
            }
        }

        // Initially activate the 'homeMain' tab when the page loads
        activateTab('homeMain');

        // --- JavaScript for Scroll-Triggered Animations ---
        // This part needs to be integrated into your existing JS (e.g., main.js)
        // if you want a robust solution that runs once across your application.
        // For demonstration, I'm including it here.

        const scrollRevealSections = document.querySelectorAll('.scroll-reveal');

        const observerOptions = {
            root: null, // viewport
            rootMargin: '0px',
            threshold: 0.1 // Trigger when 10% of the element is visible
        };

        const observer = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target); // Stop observing once visible
                }
            });
        }, observerOptions);

        scrollRevealSections.forEach(section => {
            observer.observe(section);
        });
        // --- End of JavaScript for Scroll-Triggered Animations ---
    });

    // Helper function to simulate openTab if it's not globally defined yet
    // This is a simplified version and assumes the main.js openTab function handles actual tab switching.
    // If openTab is only defined after other scripts load, you might need to ensure this executes last.
    if (typeof openTab === 'undefined') {
        window.openTab = function(tabName) {
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(tabName).classList.add('active');

            // Update active state of sidebar buttons if applicable
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            const activeButton = document.querySelector(`.tab-button[onclick*="openTab('${tabName}')"]`);
            if (activeButton) {
                activeButton.classList.add('active');
            }
        };
    }
</script>
