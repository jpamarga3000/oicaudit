// js/main.js (Revised for Apple-like Top Horizontal Navigation - Definitive Smooth Transitions & Dropdown Closing)

// Expose tabInitializerMap globally
window.tabInitializerMap = new Map();

const trnmCategories = {
    'LOAN': [
        '40-45', '46-49', '50-70', '71', '72-73', '74-79', '80 AND ABOVE'
    ],
    'DEPOSIT': [
        '20', '11', '12', '13', '15', '30', 'SC', 'SD'
    ],
    'BOTH': []
};

// Global trackers for active sub-tabs within each main section
let activeSubTabTracker = {
    'auditToolMainPage': null,
    'trnmMain': null,
    'glMain': null,
    'lnaccMain': null,
    'svaccMain': null,
    'actgMain': null,
    'operationsMain': null,
    'monitoringMain': null, // NEW: Add monitoringMain to the tracker
    'adminMain': null
};

let activeNestedSubmenuId = null;
let currentActiveMainTabId = null;

// Define the transition duration in milliseconds (should match CSS)
const TRANSITION_DURATION = 300; // 0.3s

// Make registerTabInitializer globally accessible
window.registerTabInitializer = function(tabName, initFunction) {
    window.tabInitializerMap.set(tabName, initFunction);
};

/**
 * Helper function to smoothly show an element.
 * Sets display:block, then triggers opacity/visibility transition.
 * @param {HTMLElement} element - The element to show.
 * @param {string} activeClass - The class to add to make it active (e.g., 'active', 'active-section-display').
 */
function showElement(element, activeClass) {
    if (!element) return;
    element.style.display = 'block';
    requestAnimationFrame(() => {
        element.classList.add(activeClass);
    });
}

/**
 * Helper function to smoothly hide an element.
 * Triggers opacity/visibility transition, then sets display:none after duration.
 * @param {HTMLElement} element - The element to hide.
 * @param {string} activeClass - The class to remove (e.g., 'active', 'active-section-display').
 */
function hideElement(element, activeClass) {
    if (!element) return;
    element.classList.remove(activeClass);
    setTimeout(() => {
        element.style.display = 'none';
    }, TRANSITION_DURATION);
}


/**
 * Helper function to close all main tab dropdowns (submenu-container)
 * and their respective expanded states.
 */
window.closeAllTopLevelDropdowns = function() {
    console.log('DEBUG: closeAllTopLevelDropdowns called.');
    document.querySelectorAll('#main-header .tab-item .submenu-container.active').forEach(submenu => {
        submenu.classList.remove('active');
        const parentButton = submenu.closest('.tab-item').querySelector('.tab-button');
        if (parentButton) {
            parentButton.classList.remove('expanded');
        }
        submenu.querySelectorAll('.nested-submenu-container.active').forEach(nestedSubmenu => {
            nestedSubmenu.classList.remove('active');
            const nestedParentButton = nestedSubmenu.closest('.nested-tab-item').querySelector('.nested-tab-button');
            if (nestedParentButton) {
                nestedParentButton.classList.remove('expanded');
            }
        });
    });
    activeNestedSubmenuId = null;
};

/**
 * Function to check if an element is part of an active dropdown or its toggle button,
 * or if it's part of the financial statement modal.
 * @param {HTMLElement} element - The element to check.
 * @returns {boolean} True if the element is inside an active dropdown/toggle or the FS modal.
 */
window.isClickInsideActiveDropdownOrToggleButton = function(element) {
    if (!element) return false;

    // Check for main navigation dropdowns and their toggles
    if (element.classList.contains('tab-button') || element.classList.contains('nested-tab-button')) {
        return true;
    }

    const activeSubmenus = document.querySelectorAll('#main-header .submenu-container.active');
    for (const submenu of activeSubmenus) {
        if (submenu.contains(element)) {
            return true;
        }
    }

    const activeNestedSubmenus = document.querySelectorAll('#main-header .nested-submenu-container.active');
    for (const nestedSubmenu of activeNestedSubmenus) {
        if (nestedSubmenu.contains(element)) {
            return true;
        }
    }

    const mobileNavMenu = document.getElementById('mobileNavMenu');
    if (mobileNavMenu && mobileNavMenu.classList.contains('active') && mobileNavMenu.contains(element)) {
        return true;
    }
    const openMobileMenuBtn = document.getElementById('openMobileMenu');
    if (openMobileMenuBtn && openMobileMenuBtn.contains(element)) {
        return true;
    }

    // NEW: Check if the clicked element is inside the subAccountModal or is a clickable main account row
    const subAccountModal = document.getElementById('subAccountModal');
    if (subAccountModal && subAccountModal.contains(element)) {
        return true;
    }
    // Also check if the clicked element is a main-account-clickable row
    // Use .closest() to check if the element or any of its ancestors has the class
    if (element.closest('.main-account-clickable')) {
        return true;
    }


    return false;
};


/**
 * Opens a main tab and manages the visibility of all main tab contents.
 * @param {string} tabName - The ID of the main tab content to open.
 */
window.openTab = function(tabName) {
    console.log(`openTab called for: ${tabName}`);

    const clickedButton = document.querySelector(`#main-header .tab-item [onclick*="openTab('${tabName}')"]`);
    const clickedTabItem = clickedButton ? clickedButton.closest('.tab-item') : null;
    const clickedSubmenu = clickedTabItem ? clickedTabItem.querySelector('.submenu-container') : null;
    const selectedTabContent = document.getElementById(tabName);

    // If clicking the currently active main tab button again, and its submenu is open, close it.
    if (tabName === currentActiveMainTabId && clickedButton && clickedButton.classList.contains('active')) {
        if (clickedSubmenu && clickedSubmenu.classList.contains('active')) {
            console.log(`  Toggling off already active main tab dropdown: ${tabName}`);
            clickedButton.classList.remove('expanded');
            clickedSubmenu.classList.remove('active');
            // If the submenu is closing, and it's the current main tab, we should NOT hide homeMain here.
            // HomeMain should only hide when a *sub-tab* is explicitly selected.
            return; // Exit, as we just closed the dropdown
        }
    }

    // Close all other main tab dropdowns
    window.closeAllTopLevelDropdowns();

    // Hide all main tab content EXCEPT homeMain initially.
    // HomeMain will only be hidden when a specific sub-tab is opened.
    document.querySelectorAll('.tab-content').forEach(tabContent => {
        if (tabContent.id !== 'homeMain') { // Keep homeMain visible for now
            hideElement(tabContent, 'active');
            console.log(`  Hiding main tab content: ${tabContent.id}`);
        }
    });

    // Hide all dashboard sections and sub-tab content wrappers
    document.querySelectorAll('.dashboard-section').forEach(section => {
        hideElement(section, 'active-section-display');
    });
    document.querySelectorAll('.sub-tab-content-wrapper > div').forEach(subTab => {
        hideElement(subTab, 'active-sub-tab-display');
    });


    if (selectedTabContent) {
        showElement(selectedTabContent, 'active');
        console.log(`  Showing selected main tab content: ${selectedTabContent.id}`);

        // If the selected main tab has a sub-tab wrapper, try to open its default sub-tab
        const subTabWrapper = selectedTabContent.querySelector('.sub-tab-content-wrapper');
        if (subTabWrapper) {
            let defaultSubItemId = null;
            if (tabName === 'auditToolMainPage') {
                defaultSubItemId = activeSubTabTracker['auditToolMainPage'] || 'agingConsolidatedSection';
            } else if (tabName === 'actgMain') {
                defaultSubItemId = activeSubTabTracker['actgMain'] || 'actgGl';
            } else if (tabName === 'operationsMain') {
                defaultSubItemId = activeSubTabTracker['operationsMain'] || 'operationsAgingReport';
            } else if (tabName === 'monitoringMain') { // NEW: Handle default sub-tab for monitoringMain
                defaultSubItemId = activeSubTabTracker['monitoringMain'] || 'monRegAud';
            } else if (tabName === 'adminMain') {
                defaultSubItemId = activeSubTabTracker['adminMain'] || 'adminProfile';
            }

            if (defaultSubItemId) {
                const defaultSubTabElement = document.getElementById(defaultSubItemId);
                if (defaultSubTabElement) {
                    showElement(defaultSubTabElement, 'active-sub-tab-display');
                    const defaultSubmenuItem = document.querySelector(`.submenu-item[onclick*="openSubTab('${tabName}', '${defaultSubItemId}')"]`);
                    if (defaultSubmenuItem) {
                        defaultSubmenuItem.classList.add('active');
                    }
                    const initFunction = window.tabInitializerMap.get(defaultSubItemId);
                    if (initFunction) {
                        initFunction();
                    }
                }
            }
        }
    }

    // Manage active state of the clicked main tab button and its dropdown
    if (clickedButton) {
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active')); // Remove active from all main buttons
        clickedButton.classList.add('active'); // Add active to the clicked main button

        if (clickedSubmenu) {
            clickedButton.classList.toggle('expanded');
            clickedSubmenu.classList.toggle('active');
            currentActiveMainTabId = tabName;
        } else {
            // If there's no submenu, directly initialize the tab content
            const initFunction = window.tabInitializerMap.get(tabName);
            if (initFunction) {
                initFunction();
            }
            currentActiveMainTabId = tabName;
        }
    }

    window.hideMessage();
};

/**
 * Toggles the visibility of nested submenus.
 * @param {Event} event - The click event.
 * @param {string} submenuId - The ID of the nested submenu container.
 */
window.toggleNestedSubmenu = function(event, submenuId) {
    event.stopPropagation();

    const clickedButton = event.currentTarget;
    const submenu = document.getElementById(submenuId);

    if (!submenu || !clickedButton) {
        console.error(`toggleNestedSubmenu: Submenu or button not found for ID: ${submenuId}`);
        return;
    }

    const isCurrentlyOpen = submenu.classList.contains('active');

    const parentSubmenu = clickedButton.closest('.submenu-container');
    if (parentSubmenu) {
        parentSubmenu.querySelectorAll('.nested-submenu-container').forEach(openNestedSub => {
            if (openNestedSub.id !== submenuId) {
                openNestedSub.classList.remove('active');
                const parentNestedButton = openNestedSub.closest('.nested-tab-item').querySelector('.nested-tab-button');
                if (parentNestedButton) {
                    parentNestedButton.classList.remove('expanded');
                }
            }
        });
    }

    submenu.classList.toggle('active');
    clickedButton.classList.toggle('expanded');

    if (!isCurrentlyOpen) {
        clickedButton.classList.add('active');
    } else {
        clickedButton.classList.remove('active');
    }

    let parentContentIdForNested;
    if (submenuId.startsWith('trnm')) {
        parentContentIdForNested = 'trnmMain';
    } else if (submenuId.startsWith('gl')) {
        parentContentIdForNested = 'glMain';
    } else if (submenuId.startsWith('lnacc')) {
        parentContentIdForNested = 'lnaccMain';
    } else if (submenuId.startsWith('svacc')) {
        parentContentIdForNested = 'svaccMain';
    } else if (submenuId.startsWith('admin')) {
        parentContentIdForNested = 'adminMain';
    }

    if (!isCurrentlyOpen) {
        activeNestedSubmenuId = submenuId;
        if (parentContentIdForNested) {
            const sectionId = parentContentIdForNested;
            const defaultSubItemId = activeSubTabTracker[parentContentIdForNested] ||
                                    (parentContentIdForNested === 'trnmMain' ? 'combine' :
                                    parentContentIdForNested === 'glMain' ? 'glDos' :
                                    parentContentIdForNested === 'lnaccMain' ? 'lnaccDos' :
                                    parentContentIdForNested === 'svaccMain' ? 'svaccDos' :
                                    parentContentIdForNested === 'adminMain' ? 'adminProfile' : null);
            
            if (defaultSubItemId) {
                let parentContainerForOpenSubTab = 'auditToolMainPage'; // Default for auditTool sub-items
                if (['trnmMain', 'glMain', 'lnaccMain', 'svaccMain', 'actgMain', 'operationsMain', 'monitoringMain', 'adminMain'].includes(parentContentIdForNested)) { // NEW: Added monitoringMain
                    parentContainerForOpenSubTab = parentContentIdForNested; // Use the actual parent for other modules
                }
                
                window.openSubTab(parentContainerForOpenSubTab, defaultSubItemId);
            } else {
                const sectionToShow = document.getElementById(sectionId);
                if(sectionToShow) {
                    showElement(sectionToShow, 'active-section-display');
                }
            }
        }
    } else {
        activeNestedSubmenuId = null;
        if (parentContentIdForNested) {
            const sectionToHide = document.getElementById(sectionId);
            if (sectionToHide) {
                hideElement(sectionToHide, 'active-section-display');
            }
            activeSubTabTracker[parentContentIdForNested] = null;
        }
    }
    window.hideMessage();
};

/**
 * Opens a sub-tab/section within a main container.
 * @param {string} parentContainerId - The ID of the parent main tab content.
 * @param {string} subItemId - The ID of the sub-tab/section content to display.
 * @param {string} [defaultSubSubItemId=null] - Optional: For sections that contain further nested sub-tabs.
 */
window.openSubTab = function(parentContainerId, subItemId, defaultSubSubItemId = null) {
    console.log(`openSubTab called for: parentContainerId=${parentContainerId}, subItemId=${subItemId}, defaultSubSubItemId=${defaultSubSubItemId}`);

    // Hide homeMain if it's currently active and a sub-tab is being opened
    const homeMain = document.getElementById('homeMain');
    if (homeMain && homeMain.classList.contains('active')) {
        hideElement(homeMain, 'active');
        console.log('  Hiding homeMain as a sub-tab is being opened.');
    }

    const isLevel2Container = ['trnmMainSection', 'glMainSection', 'lnaccMainSection', 'svaccMainSection', 'operationsDashboard', 'operationsReports', 'operationsAgingReport'].includes(subItemId);
    const isAdminMain = subItemId === 'adminMain';

    if (!isLevel2Container && !isAdminMain) {
        window.closeAllTopLevelDropdowns();
    }

    let currentActiveTrackerKey = parentContainerId;
    if (isLevel2Container) {
        currentActiveTrackerKey = subItemId.replace('Section', '');
        if (parentContainerId === 'operationsMain' || parentContainerId === 'adminMain') {
            currentActiveTrackerKey = parentContainerId;
        }
    } else if (isAdminMain) {
        currentActiveTrackerKey = 'adminMain';
    }


    if (activeSubTabTracker[currentActiveTrackerKey] === subItemId && !defaultSubSubItemId) {
        if (isAdminMain) {
            console.log(`  ${subItemId} is already active, preventing redundant action.`);
            window.hideMessage();
            return;
        } else {
            console.log(`  Toggling off already active sub-item: ${subItemId}`);

            const clickedSubmenuItem = document.querySelector(`.submenu-item[onclick*="openSubTab('${parentContainerId}', '${subItemId}')"]`);
            if (clickedSubmenuItem) {
                clickedSubmenuItem.classList.remove('active');
            }

            const targetContentElement = document.getElementById(subItemId);
            if (targetContentElement) {
                hideElement(targetContentElement, 'active-section-display');
            }

            if (parentContainerId !== 'auditToolMainPage') {
                const parentNestedButton = document.querySelector(`#${parentContainerId.replace('Main', 'SubmenuNested')} .nested-tab-button`);
                if (parentNestedButton) {
                    parentNestedButton.classList.remove('active');
                }
            }

            activeSubTabTracker[currentActiveTrackerKey] = null;
            window.hideMessage();
            return;
        }
    } else {
        activeSubTabTracker[currentActiveTrackerKey] = subItemId;
    }

    document.querySelectorAll('.submenu-item, .nested-submenu-container .submenu-item').forEach(item => {
        item.classList.remove('active');
    });

    document.querySelectorAll('#auditToolMainPage .dashboard-section').forEach(section => {
        hideElement(section, 'active-section-display');
    });
    document.querySelectorAll('.sub-tab-content-wrapper > div').forEach(child => {
        hideElement(child, 'active-sub-tab-display');
    });


    if (parentContainerId === 'auditToolMainPage') {
        const targetSection = document.getElementById(subItemId);
        if (targetSection) {
            showElement(targetSection, 'active-section-display');
            targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

            const subTabContentsWrapper = targetSection.querySelector('.sub-tab-content-wrapper');
            if (subTabContentsWrapper && defaultSubSubItemId) {
                const defaultContent = document.getElementById(defaultSubSubItemId);
                if (defaultContent) {
                    showElement(defaultContent, 'active-sub-tab-display');
                }
            }
        }
    } else {
        const mainParentTabContent = document.getElementById(parentContainerId);
        if (mainParentTabContent) {
            showElement(mainParentTabContent, 'active');
        }

        const mainParentSectionId = parentContainerId + 'Section';
        const mainParentSection = document.getElementById(mainParentSectionId);
        if (mainParentSection) {
            showElement(mainParentSection, 'active-section-display');
        }

        const selectedSubTabContent = document.getElementById(subItemId);
        if (selectedSubTabContent) {
            showElement(selectedSubTabContent, 'active-sub-tab-display');
        }
    }

    window.hideMessage();

    const clickedSubmenuItem = document.querySelector(`.submenu-item[onclick*="openSubTab('${parentContainerId}', '${subItemId}')"]`);
    if (clickedSubmenuItem) {
        clickedSubmenuItem.classList.add('active');
    }

    const initFunction = window.tabInitializerMap.get(subItemId);
    if (initFunction) {
        initFunction();
    }
};

/**
 * Opens a main tab from the mobile menu and toggles its corresponding submenu.
 * @param {Event} event - The click event.
 * @param {string} tabName - The ID of the main tab content to open.
 * @param {string} submenuId - The ID of the submenu container within the mobile menu.
 */
window.openMobileTabAndToggleSubmenu = function(event, tabName, submenuId) {
    event.stopPropagation();

    const clickedButton = event.currentTarget;
    const submenu = document.getElementById(submenuId);

    if (!submenu || !clickedButton) {
        console.error(`openMobileTabAndToggleSubmenu: Submenu or button not found for ID: ${submenuId}`);
        return;
    }

    const isCurrentlyOpen = submenu.classList.contains('active');
    const hasSubmenu = clickedButton.closest('.tab-item').classList.contains('has-submenu');

    document.querySelectorAll('.mobile-nav-menu .submenu-container.active').forEach(openSubmenu => {
        if (openSubmenu.id !== submenuId) {
            openSubmenu.classList.remove('active');
            const parentButton = openSubmenu.closest('.tab-item').querySelector('button');
            if(parentButton) {
                parentButton.classList.remove('active');
            }
        }
    });

    submenu.classList.toggle('active');
    clickedButton.classList.toggle('active');

    if (submenu.classList.contains('active')) {
        submenu.querySelectorAll('.nested-submenu-container.active').forEach(nestedSubmenu => {
            nestedSubmenu.classList.remove('active');
            const nestedParentButton = nestedSubmenu.closest('.nested-tab-item').querySelector('button');
            if(nestedParentButton) {
                nestedParentButton.classList.remove('active');
            }
        });
        // When opening a main tab from mobile, we want to show its content, but NOT hide homeMain yet.
        // HomeMain will only be hidden when a specific sub-tab is selected via openMobileSubTab.
        window.openTab(tabName);
    } else {
        const selectedTabContent = document.getElementById(tabName);
        // Only hide the main tab content if its submenu is being closed AND it's not homeMain
        if (selectedTabContent && selectedTabContent.id !== 'homeMain') {
            hideElement(selectedTabContent, 'active');
        }
    }

    if (!hasSubmenu) {
        const mobileNavMenu = document.getElementById('mobileNavMenu');
        if (mobileNavMenu) {
            mobileNavMenu.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    window.hideMessage();
};

/**
 * Opens a sub-tab/section from the mobile menu.
 * @param {string} parentContainerId - The ID of the parent main tab content.
 * @param {string} subItemId - The ID of the sub-tab/section content to display.
 */
window.openMobileSubTab = function(parentContainerId, subItemId) {
    console.log(`openMobileSubTab called for: parentContainerId=${parentContainerId}, subItemId=${subItemId}`);

    // Call openSubTab, which now handles hiding homeMain
    window.openSubTab(parentContainerId, subItemId);

    const mobileNavMenu = document.getElementById('mobileNavMenu');
    if (mobileNavMenu) {
        mobileNavMenu.classList.remove('active');
    }
    document.body.style.overflow = '';
    window.hideMessage();
};

/**
 * Toggles the visibility of nested submenus within the mobile menu.
 * @param {Event} event - The click event.
 * @param {string} submenuId - The ID of the nested submenu container.
 */
window.toggleMobileNestedSubmenu = function(event, submenuId) {
    event.stopPropagation();

    const clickedButton = event.currentTarget;
    const submenu = document.getElementById(submenuId);

    if (!submenu || !clickedButton) {
        console.error(`toggleMobileNestedSubmenu: Submenu or button not found for ID: ${submenuId}`);
        return;
    }

    const isCurrentlyOpen = submenu.classList.contains('active');

    document.querySelectorAll('.nested-submenu-container.active').forEach(openNestedSub => {
        if (openNestedSub.id !== submenuId) {
            openNestedSub.classList.remove('active');
            const parentNestedButton = openNestedSub.closest('.nested-tab-item').querySelector('button');
            if(parentNestedButton) {
                parentNestedButton.classList.remove('active');
            }
        }
    });


    submenu.classList.toggle('active');
    clickedButton.classList.toggle('active');

    if (!isCurrentlyOpen) {
        let parentContentIdForNested;
        if (submenuId.startsWith('trnm')) {
            parentContentIdForNested = 'trnmMain';
        } else if (submenuId.startsWith('gl')) {
            parentContentIdForNested = 'glMain';
        } else if (submenuId.startsWith('lnacc')) {
            parentContentIdForNested = 'lnaccMain';
        } else if (submenuId.startsWith('svacc')) {
            parentContentIdForNested = 'svaccMain';
        } else if (submenuId.startsWith('admin')) {
            parentContentIdForNested = 'adminMain';
        }

        if (parentContentIdForNested) {
            const parentContainerForOpenSubTab = (parentContentIdForNested === 'adminMain') ? parentContentIdForNested : 'auditToolMainPage';
            // When opening a nested submenu, we want to show its parent main tab, but NOT hide homeMain yet.
            // homeMain will only be hidden when a specific sub-tab is selected via openMobileSubTab.
            window.openTab(parentContainerForOpenSubTab);
        }
    }
    window.hideMessage();
};

// NEW: Function to load profile picture in the header
// Making this function globally accessible for admin_profile.js to call
window.loadHeaderProfilePicture = async function() {
    const headerProfilePic = document.getElementById('headerProfilePic');
    // Assuming username is available globally or via a meta tag/session variable
    // For now, let's get it from the session data pre-filled by PHP in the profile page, or a global JS var
    const usernameSpan = document.querySelector('#main-header .user-greeting .font-semibold');
    let username = '';
    if (usernameSpan) {
        // Extract username from the greeting text, assuming it's the content of the span
        username = usernameSpan.textContent.trim();
    }
    // Fallback to a hidden input or global variable if direct extraction is unreliable
    if (!username && document.getElementById('profileUsername')) {
        username = document.getElementById('profileUsername').value;
    }

    if (!username || !headerProfilePic) {
        console.warn("main.js: Username or headerProfilePic element not available to load header profile picture. Using placeholder.");
        // Ensure the placeholder is set if elements are missing
        if (headerProfilePic) {
            headerProfilePic.src = `https://placehold.co/32x32/cbd5e1/475569?text=P`;
        }
        return;
    }

    try {
        const response = await fetch(`${window.FLASK_API_BASE_URL || 'http://127.0.0.1:5000'}/get_profile_picture/${username}`, {
            credentials: 'include' // Ensure cookies are sent for this request
        });
        if (response.ok) {
            const data = await response.json();
            if (data.image_url) {
                // Add a cache buster to ensure the latest image is fetched
                headerProfilePic.src = data.image_url + '?' + new Date().getTime(); 
            } else {
                headerProfilePic.src = `https://placehold.co/32x32/cbd5e1/475569?text=P`; // Default placeholder
            }
        } else {
            console.warn("Failed to fetch header profile picture status, using default. Status:", response.status);
            headerProfilePic.src = `https://placehold.co/32x32/cbd5e1/475569?text=P`; // Fallback to default
        }
    } catch (error) {
        console.error("Error loading header profile picture:", error);
        headerProfilePic.src = `https://placehold.co/32x32/cbd5e1/475569?text=P`; // Fallback to default
    }
};


// Event listener to run when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Set 'Audit Tool' as the default active tab on page load
    // We want homeMain to be visible initially, so don't call openTab directly here
    // Instead, ensure homeMain is active via CSS/initial HTML state.
    // window.openTab('auditToolMainPage'); // Removed this line

    // Global click listener to close dropdowns when clicking outside
    document.addEventListener('click', (event) => {
        const mainHeader = document.getElementById('main-header');
        const clickedElement = event.target;

        if (!window.isClickInsideActiveDropdownOrToggleButton(clickedElement)) {
            window.closeAllTopLevelDropdowns();
        }
    });

    // Close dropdowns on window resize
    window.addEventListener('resize', () => {
        window.closeAllTopLevelDropdowns();
    });

    // NEW: Mobile menu toggle event listeners
    const openMobileMenuBtn = document.getElementById('openMobileMenu');
    const mobileNavMenu = document.getElementById('mobileNavMenu');

    if (openMobileMenuBtn) {
        openMobileMenuBtn.addEventListener('click', () => {
            mobileNavMenu.classList.toggle('active');

            if (mobileNavMenu.classList.contains('active')) {
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.overflow = '';
                mobileNavMenu.querySelectorAll('.submenu-container.active, .nested-submenu-container.active').forEach(submenu => {
                    submenu.classList.remove('active');
                    const parentButton = submenu.closest('.tab-item, .nested-tab-item').querySelector('button');
                    if(parentButton) {
                        parentButton.classList.remove('active');
                    }
                });
            }
        });
    }

    // Call loadHeaderProfilePicture on DOMContentLoaded
    window.loadHeaderProfilePicture();
});
