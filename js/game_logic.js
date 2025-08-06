// audit_tool/js/game_logic.js
// This file contains all the generic 2D game logic for loading screens.

(function() {
    // Game UI Elements (will be initialized by startGame with specific IDs)
    let gameCanvas;
    let ctx;
    let gameScoreDisplay;
    let gameLoadingOverlay;
    // These will be initialized within startGame or fetchAndDisplayLeaderboard
    let trnmLeaderboard;
    let leaderboardTableBody;
    let closeLeaderboardBtn;

    // Game Variables
    let currentScore = 0;
    let catcher;
    let fallingObjects = [];
    let gameLoopInterval; // requestAnimationFrame ID
    let gameRunning = false;
    let spawnObjectInterval; // setInterval ID

    // Game Constants
    const CATCHER_WIDTH = 80;
    const CATCHER_HEIGHT = 20;
    const CATCHER_COLOR = '#4CAF50'; // Green
    const OBJECT_SIZE = 40; // Size for falling images/bombs
    const INITIAL_FALL_SPEED = 1; // Pixels per frame
    const SPEED_INCREASE_RATE = 0.0005; // How much speed increases per frame per frame
    const SPAWN_INTERVAL = 1000; // Milliseconds between new object spawns
    const BOMB_CHANCE = 0.2; // 20% chance for a bomb to spawn

    // Paths to profile images (assuming they are in images/profile/ relative to htdocs)
    const PROFILE_IMAGE_PATHS = [
        'images/profile/amarga3000.jpg',
        'images/profile/cjbgallur.jpg',
        'images/profile/desamb.png',
        'images/profile/fransteak.jpg',
        'images/profile/nasrimah.laguindab.png',
        'images/profile/rheasai.jpg',
        'images/profile/Sabelita.png'
    ];
    let profileImages = []; // Array to store loaded Image objects
    let bombImage; // Image object for the bomb

    /**
     * SVG for a simple bomb icon.
     * @param {number} size - The desired size of the SVG.
     * @param {string} color - The fill color of the bomb.
     * @returns {string} The SVG string.
     */
    function getBombSVG(size, color = 'red') {
        return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="15" r="7" fill="${color}"/>
            <path d="M12 8V4M14 6L16 4M10 6L8 4" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 15C12 15 10.5 13 12 11C13.5 13 12 15 12 15Z" fill="white"/>
        </svg>`;
    }

    /**
     * Loads all necessary game images.
     * @returns {Promise<void>} A promise that resolves when all images are loaded.
     */
    async function loadGameImages() {
        const imagePromises = PROFILE_IMAGE_PATHS.map(path => {
            return new Promise((resolve, reject) => {
                const img = new Image();
                // Construct absolute URL for images if needed, or ensure base path is correct
                img.src = `${window.location.origin}/audit_tool/${path}`; // Assuming images are relative to audit_tool
                img.onload = () => resolve(img);
                img.onerror = () => {
                    console.warn(`Failed to load image: ${img.src}. Using placeholder.`);
                    const placeholder = new Image();
                    placeholder.src = `https://placehold.co/${OBJECT_SIZE}x${OBJECT_SIZE}/cccccc/333333?text=IMG`;
                    placeholder.onload = () => resolve(placeholder);
                    placeholder.onerror = () => reject(new Error(`Failed to load placeholder for ${img.src}`));
                };
            });
        });

        const bombSVG = getBombSVG(OBJECT_SIZE, 'red');
        const bombImagePromise = new Promise((resolve, reject) => {
            const img = new Image();
            img.src = 'data:image/svg+xml;base64,' + btoa(bombSVG);
            img.onload = () => resolve(img);
            img.onerror = () => {
                console.error("Failed to load bomb SVG. Using fallback.");
                const fallback = new Image();
                fallback.src = `https://placehold.co/${OBJECT_SIZE}x${OBJECT_SIZE}/ff0000/ffffff?text=BOMB`;
                fallback.onload = () => resolve(fallback);
                fallback.onerror = () => reject(new Error("Failed to load bomb fallback"));
            };
        });

        const loadedImages = await Promise.allSettled([...imagePromises, bombImagePromise]); // Use allSettled to handle individual image load failures gracefully
        
        // Filter out rejected promises and assign images
        const successfulImages = loadedImages.filter(result => result.status === 'fulfilled').map(result => result.value);
        
        if (successfulImages.length > 0) {
            bombImage = successfulImages.pop(); // Last one is bombImage
            profileImages = successfulImages;
            console.log("Game images loaded successfully.");
        } else {
            console.error("No game images could be loaded successfully.");
        }
    }

    /**
     * Starts the game loop and displays the game overlay.
     * @param {string} canvasId - The ID of the canvas element.
     * @param {string} scoreDisplayId - The ID of the score display element.
     * @param {string} overlayId - The ID of the loading overlay element.
     */
    function startGame(canvasId, scoreDisplayId, overlayId) {
        console.log(`Game Logic: startGame called for Canvas ID: ${canvasId}, Score ID: ${scoreDisplayId}, Overlay ID: ${overlayId}`);

        // Ensure elements are fetched AFTER they are expected to be in the DOM
        gameLoadingOverlay = document.getElementById(overlayId);
        gameCanvas = document.getElementById(canvasId);
        gameScoreDisplay = document.getElementById(scoreDisplayId);
        
        // Initialize leaderboard elements here, ensuring they exist
        trnmLeaderboard = document.getElementById('trnmLeaderboard');
        leaderboardTableBody = document.getElementById('leaderboardTableBody');
        closeLeaderboardBtn = document.getElementById('closeLeaderboardBtn');

        if (!gameCanvas || !gameLoadingOverlay || !gameScoreDisplay) {
            console.error(`Game Logic: Missing core game elements. Canvas: ${!!gameCanvas}, Overlay: ${!!gameLoadingOverlay}, Score Display: ${!!gameScoreDisplay}. Cannot start game.`);
            return;
        }
        
        if (!ctx) { // Get context only once
            ctx = gameCanvas.getContext('2d');
        }
        
        if (gameRunning) {
            console.log("Game Logic: Game already running, not starting again.");
            return;
        }

        currentScore = 0; // Reset score for new game
        gameScoreDisplay.textContent = `Score: ${currentScore}`;
        fallingObjects = [];
        catcher = { x: gameCanvas.width / 2 - CATCHER_WIDTH / 2, y: gameCanvas.height - CATCHER_HEIGHT - 10, width: CATCHER_WIDTH, height: CATCHER_HEIGHT, speed: 10 };
        currentFallSpeed = INITIAL_FALL_SPEED; // Reset speed for new game

        gameLoadingOverlay.classList.remove('hidden');
        // Ensure leaderboard is hidden when game starts
        if (trnmLeaderboard) {
            trnmLeaderboard.classList.add('hidden');
        }

        gameRunning = true;
        gameLoopInterval = requestAnimationFrame(gameLoop);
        spawnObjectInterval = setInterval(spawnFallingObject, SPAWN_INTERVAL);

        gameCanvas.addEventListener('mousemove', handleMouseMove);
        gameCanvas.addEventListener('touchmove', handleTouchMove, { passive: false });

        // Add event listener for the close leaderboard button
        if (closeLeaderboardBtn) {
            closeLeaderboardBtn.onclick = () => { // Use onclick to prevent multiple listeners if called repeatedly
                if (trnmLeaderboard) {
                    trnmLeaderboard.classList.add('hidden');
                }
            };
        } else {
            console.warn("Game Logic: Close leaderboard button not found.");
        }

        // Ensure images are loaded before starting game, or load them if not already
        if (profileImages.length === 0 || !bombImage) {
            console.warn("Game Logic: Game images not loaded during startGame, attempting to load now...");
            loadGameImages().then(() => {
                console.log("Game Logic: Game images loaded (late start).");
            }).catch(err => {
                console.error("Game Logic: Failed to load game images during late load:", err);
            });
        }
        console.log("Game Logic: Game started.");
    }

    /**
     * Stops the game loop and hides the game overlay.
     */
    function stopGame() {
        console.log("Game Logic: stopGame called.");
        if (!gameRunning) {
            console.log("Game Logic: Game not running, nothing to stop.");
            return;
        }

        cancelAnimationFrame(gameLoopInterval);
        clearInterval(spawnObjectInterval);
        gameLoadingOverlay.classList.add('hidden');
        gameRunning = false;
        gameCanvas.removeEventListener('mousemove', handleMouseMove);
        gameCanvas.removeEventListener('touchmove', handleTouchMove);
        ctx.clearRect(0, 0, gameCanvas.width, gameCanvas.height); // Clear canvas
        fallingObjects = []; // Clear falling objects
        console.log("Game Logic: Game stopped.");
    }

    /**
     * Game loop function.
     */
    let currentFallSpeed = INITIAL_FALL_SPEED;
    function gameLoop() {
        if (!gameRunning) return;

        ctx.clearRect(0, 0, gameCanvas.width, gameCanvas.height); // Clear canvas

        // Draw catcher
        ctx.fillStyle = CATCHER_COLOR;
        ctx.fillRect(catcher.x, catcher.y, catcher.width, catcher.height);

        // Update and draw falling objects
        for (let i = fallingObjects.length - 1; i >= 0; i--) {
            const obj = fallingObjects[i];
            obj.y += currentFallSpeed;

            if (obj.image) { // Ensure image is loaded before drawing
                ctx.drawImage(obj.image, obj.x, obj.y, obj.size, obj.size);
            } else {
                // Fallback drawing if image somehow failed to load
                ctx.fillStyle = obj.isBomb ? 'red' : 'blue';
                ctx.fillRect(obj.x, obj.y, obj.size, obj.size);
            }

            // Collision detection with catcher
            if (obj.y + obj.size > catcher.y &&
                obj.x < catcher.x + catcher.width &&
                obj.x + obj.size > catcher.x) {
                
                if (obj.isBomb) {
                    currentScore -= 1;
                } else {
                    currentScore += 1;
                }
                gameScoreDisplay.textContent = `Score: ${currentScore}`;
                fallingObjects.splice(i, 1);
            }
            // Object missed or fell off screen
            else if (obj.y > gameCanvas.height) {
                if (!obj.isBomb) { // Penalty only for missing good items
                    currentScore -= 1;
                    gameScoreDisplay.textContent = `Score: ${currentScore}`;
                }
                fallingObjects.splice(i, 1);
            }
        }

        currentFallSpeed += SPEED_INCREASE_RATE;

        gameLoopInterval = requestAnimationFrame(gameLoop);
    }

    /**
     * Spawns a new falling object (profile picture or bomb).
     */
    function spawnFallingObject() {
        if (!gameRunning) return;

        const isBomb = Math.random() < BOMB_CHANCE;
        const imageToUse = isBomb ? bombImage : profileImages[Math.floor(Math.random() * profileImages.length)];

        if (!imageToUse) {
            console.warn("Image not ready for spawning, skipping object.");
            return;
        }

        // Calculate spawn X range to ensure objects are fully reachable by catcher.
        // Max X for object's left edge should be `gameCanvas.width - CATCHER_WIDTH`.
        const maxSpawnX = gameCanvas.width - CATCHER_WIDTH;
        const x = Math.random() * maxSpawnX;

        fallingObjects.push({
            x: x,
            y: 0,
            size: OBJECT_SIZE,
            image: imageToUse,
            isBomb: isBomb
        });
    }

    /**
     * Handles mouse movement for the catcher.
     * @param {MouseEvent} event - The mouse event.
     */
    function handleMouseMove(event) {
        const rect = gameCanvas.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        catcher.x = mouseX - catcher.width / 2;
        if (catcher.x < 0) catcher.x = 0;
        if (catcher.x + catcher.width > gameCanvas.width) catcher.x = gameCanvas.width - catcher.width;
    }

    /**
     * Handles touch movement for the catcher (for mobile responsiveness).
     * @param {TouchEvent} event - The touch event.
     */
    function handleTouchMove(event) {
        event.preventDefault(); // Prevent scrolling
        const rect = gameCanvas.getBoundingClientRect();
        const touchX = event.touches[0].clientX - rect.left;
        catcher.x = touchX - catcher.width / 2;
        if (catcher.x < 0) catcher.x = 0;
        if (catcher.x + catcher.width > gameCanvas.width) catcher.x = gameCanvas.width - catcher.width;
    }

    // Expose game control functions and score globally
    window.gameLogic = {
        startGame: startGame,
        stopGame: stopGame,
        get score() { return currentScore; }, // Expose score as a getter
        submitAndFetchLeaderboard: async function(finalScore) {
            console.log("Game Logic: Submitting score to leaderboard:", finalScore);
            const username = window.sessionStorage.getItem('username');
            let playerName = username || 'Guest'; // Default to username or 'Guest'

            // Attempt to fetch First Name from user profile
            if (username) {
                try {
                    const userProfileResponse = await fetch(`${window.FLASK_API_BASE_URL}/get_user_profile/${username}`);
                    if (userProfileResponse.ok) {
                        const userProfileData = await userProfileResponse.json();
                        if (userProfileData.success && userProfileData.user && userProfileData.user['First Name']) {
                            playerName = userProfileData.user['First Name'];
                            console.log("Game Logic: Fetched player name (First Name):", playerName);
                        }
                    } else {
                        console.warn(`Game Logic: Failed to fetch user profile (${userProfileResponse.status}) for leaderboard. Using username or 'Guest'.`);
                    }
                } catch (error) {
                    console.error("Game Logic: Error fetching user profile for leaderboard:", error);
                }
            }

            try {
                const submitResponse = await fetch(`${window.FLASK_API_BASE_URL}/submit_game_score`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: playerName, score: finalScore }) // Use fetched playerName (First Name)
                });
                const submitResult = await submitResponse.json();
                if (submitResult.success) {
                    console.log("Game Logic: Score submitted successfully:", submitResult.message);
                } else {
                    console.error("Game Logic: Failed to submit score:", submitResult.message);
                }
            } catch (error) {
                console.error("Game Logic: Error submitting score:", error);
            }

            await window.gameLogic.fetchAndDisplayLeaderboard();
        },
        fetchAndDisplayLeaderboard: async function() {
            console.log("Game Logic: Fetching leaderboard data...");
            // Re-fetch references to ensure they are current in case of dynamic DOM changes
            trnmLeaderboard = document.getElementById('trnmLeaderboard');
            leaderboardTableBody = document.getElementById('leaderboardTableBody');

            if (!leaderboardTableBody || !trnmLeaderboard) {
                console.error("Game Logic: Leaderboard elements not found (trnmLeaderboard or leaderboardTableBody). Cannot fetch/display leaderboard.");
                return;
            }

            leaderboardTableBody.innerHTML = '<tr><td colspan="2" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">Loading leaderboard...</td></tr>';
            trnmLeaderboard.classList.remove('hidden'); // Show leaderboard container

            try {
                const response = await fetch(`${window.FLASK_API_BASE_URL}/get_leaderboard`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();

                leaderboardTableBody.innerHTML = ''; // Clear loading message

                if (data.success && data.leaderboard.length > 0) {
                    data.leaderboard.forEach((entry, index) => {
                        const tr = document.createElement('tr');
                        tr.className = 'hover:bg-gray-100 ' + (index % 2 === 0 ? 'bg-white' : 'bg-gray-50');
                        tr.innerHTML = `
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${entry.NAME}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">${entry.SCORE}</td>
                        `;
                        leaderboardTableBody.appendChild(tr);
                    });
                    console.log("Game Logic: Leaderboard loaded successfully.");
                } else {
                    leaderboardTableBody.innerHTML = '<tr><td colspan="2" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">No scores yet.</td></tr>';
                    console.log("Game Logic: No leaderboard scores available.");
                }
            } catch (error) {
                console.error("Game Logic: Error fetching leaderboard:", error);
                leaderboardTableBody.innerHTML = '<tr><td colspan="2" class="px-6 py-4 whitespace-nowrap text-center text-red-500">Failed to load leaderboard.</td></tr>';
            }
        }
    };

    // Pre-load images when the script loads, ensuring DOM is ready for initial element access
    window.addEventListener('DOMContentLoaded', () => {
        loadGameImages().catch(err => console.error("Game Logic: Initial game image load failed:", err));
    });

})(); // End IIFE
