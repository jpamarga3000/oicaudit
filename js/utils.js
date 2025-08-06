// js/utils.js

// Make messageTimeoutId globally accessible through the window object if needed by other scripts,
// otherwise, it can remain local to the IIFE. For now, keeping it local.
let messageTimeoutId;

/**
 * Displays a message in the designated message area.
 * @param {string} text - The message to display.
 * @param {string} type - The type of message ('success', 'error', 'info', 'loading').
 * @param {string} [outputPath=''] - Optional: The path to the output folder for success messages.
 * @param {number} [duration=3000] - Duration in milliseconds for success/info messages.
 * Error/loading messages will stay until explicitly hidden.
 */
window.showMessage = function(text, type, outputPath = '', duration = 3000) {
    // Clear any existing timeout to prevent messages from disappearing prematurely
    if (messageTimeoutId) {
        clearTimeout(messageTimeoutId);
        messageTimeoutId = null; // Clear the ID after clearing timeout
    }

    const messageDiv = document.getElementById('message');
    if (!messageDiv) {
        console.error("Error: Message div with ID 'message' not found in the DOM.");
        return;
    }

    // Clear previous content
    messageDiv.innerHTML = '';

    // Create a container for text and close button
    const contentWrapper = document.createElement('div');
    contentWrapper.className = 'flex items-center justify-between w-full';
    messageDiv.appendChild(contentWrapper);

    // Set message text
    const messageTextSpan = document.createElement('span');
    messageTextSpan.textContent = text;
    contentWrapper.appendChild(messageTextSpan);

    // Add close button
    const closeButton = document.createElement('button');
    closeButton.innerHTML = '&times;'; // 'x' icon
    closeButton.className = 'text-gray-500 hover:text-gray-700 text-2xl leading-none ml-4';
    closeButton.style.background = 'none';
    closeButton.style.border = 'none';
    closeButton.style.cursor = 'pointer';
    closeButton.onclick = window.hideMessage; // Attach hideMessage function to click
    contentWrapper.appendChild(closeButton);


    // Add link to output folder for success messages
    if (type === 'success' && outputPath) {
        const linkBreak = document.createElement('br');
        messageDiv.appendChild(linkBreak);

        const outputLink = document.createElement('a');
        // Use encodeURIComponent for path components to handle spaces/special chars
        // Note: file:/// protocol might be restricted by browser security for direct opening
        outputLink.href = `file:///${outputPath.replace(/\\/g, '/')}`; // Convert backslashes to forward slashes for file URI
        outputLink.textContent = 'Open Output Folder';
        outputLink.style.color = '#4f46e5'; // Example link color
        outputLink.style.textDecoration = 'underline';
        outputLink.style.cursor = 'pointer';
        outputLink.target = '_blank'; // Try to open in a new tab/window (might not work for file://)

        messageDiv.appendChild(outputLink);

        const securityNote = document.createElement('p');
        securityNote.style.fontSize = '0.8em';
        securityNote.style.marginTop = '0.5em';
        securityNote.style.color = '#4a5568'; // Darker gray for readability
        securityNote.textContent = '(If link doesn\'t open, copy path to file explorer)';
        messageDiv.appendChild(securityNote);
    }

    // Set message classes for styling
    messageDiv.className = ''; // Clear existing classes first
    messageDiv.classList.add('message-common'); // Apply common styles first
    if (type === 'success') {
        messageDiv.classList.add('message-success');
    } else if (type === 'error') {
        messageDiv.classList.add('message-error');
    } else if (type === 'info') {
        messageDiv.classList.add('message-info');
    } else if (type === 'loading') {
        messageDiv.classList.add('message-loading');
    }

    // Trigger fade-in by adding 'active' class
    messageDiv.classList.add('active'); // This will trigger the opacity/visibility transition

    // Automatically hide success/info messages after a duration, ONLY if no output path is provided
    if ((type === 'success' || type === 'info') && !outputPath) {
        messageTimeoutId = setTimeout(() => {
            window.hideMessage();
        }, duration);
    }
    // Error and loading messages, or success/info messages WITH a link, will remain until explicitly hidden
    // (e.g., by a new showMessage call or manual hideMessage() if you add a close button later)
};

/**
 * Hides the message div.
 */
window.hideMessage = function() {
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
        // Trigger fade-out by removing 'active' class
        messageDiv.classList.remove('active');
        // Clear any pending timeout
        if (messageTimeoutId) {
            clearTimeout(messageTimeoutId);
            messageTimeoutId = null;
        }
    }
};

/**
 * Displays or hides a global loading indicator.
 * @param {boolean} show - True to show the loading indicator, false to hide it.
 */
window.showLoading = function(show) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (!loadingIndicator) {
        console.warn("Loading indicator element with ID 'loadingIndicator' not found. Please ensure it's in your HTML.");
        return;
    }

    if (show) {
        loadingIndicator.classList.add('active');
        document.body.style.overflow = 'hidden'; // Prevent scrolling when loading
    } else {
        loadingIndicator.classList.remove('active');
        document.body.style.overflow = ''; // Restore scrolling
    }
};

/**
 * Hides the global loading indicator.
 */
window.hideLoading = function() {
    window.showLoading(false);
};


/**
 * Renders the list of selected files in the UI.
 * @param {File[]} filesArray - The array of File objects to display.
 * @param {string} displayElementId - The ID of the HTML element where files should be displayed.
 * @param {function(number): void} removeCallback - A callback function to execute when a file's remove button is clicked.
 * It receives the index of the file to remove.
 */
window.renderSelectedFiles = function(filesArray, displayElementId, removeCallback) {
    const displayElement = document.getElementById(displayElementId);
    if (!displayElement) {
        console.error(`Error: Display element with ID '${displayElementId}' not found.`);
        return;
    }

    displayElement.innerHTML = ''; // Clear existing content

    if (filesArray.length === 0) {
        displayElement.textContent = 'No files selected.';
        displayElement.classList.remove('text-blue-800');
        displayElement.classList.add('text-gray-500');
        return;
    }

    displayElement.classList.remove('text-gray-500');
    displayElement.classList.add('text-blue-800');

    filesArray.forEach((file, index) => {
        const fileEntry = document.createElement('div');
        fileEntry.className = 'flex items-center justify-between py-1 px-2 border-b border-blue-200 last:border-b-0';
        fileEntry.innerHTML = `
            <span>${file.name}</span>
            <button type="button" class="text-red-500 hover:text-red-700 ml-2 text-lg font-bold" data-index="${index}">
                &times;
            </button>
        `;
        displayElement.appendChild(fileEntry);
    });

    // Attach event listeners to the newly created remove buttons
    displayElement.querySelectorAll('button[data-index]').forEach(button => {
        button.addEventListener('click', (event) => {
            const indexToRemove = parseInt(event.target.dataset.index);
            removeCallback(indexToRemove); // Call the tab-specific removal logic
        });
    });
};

// Define the base URL for your Flask API globally
// IMPORTANT: Replace '192.168.1.100' with the actual IP address of your server laptop.
// Ensure your Python Flask app is running on this server at port 5000.
window.FLASK_API_BASE_URL = 'http://192.168.68.118:5000';
    