/*
Blind Spot - AI Thinking Companion
Main application controller
*/

import { initState } from './state.js';
import { initAPI } from './api.js';
import { initRendering } from './render.js';
import { initAccessibility } from './a11y.js';

/**
 * Initialize the application
 */
async function initApp() {
    try {
        // Initialize modules in order
        await initState();
        await initAPI();
        await initRendering();
        await initAccessibility();

        console.log('Blind Spot AI Thinking Companion initialized');
    } catch (error) {
        console.error('Failed to initialize app:', error);
        showErrorState('Failed to initialize application. Please refresh and try again.');
    }
}

/**
 * Show error state in the UI
 * @param {string} message - Error message to display
 */
function showErrorState(message) {
    const app = document.getElementById('app');
    if (app) {
        app.innerHTML = `
            <div class="error-state">
                <h2>Application Error</h2>
                <p>${message}</p>
                <button onclick="location.reload()">Try Again</button>
            </div>
        `;
    }
}

// Initialize app when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

// Export for use in other modules if needed
window.BlindSpot = {
    initApp
};