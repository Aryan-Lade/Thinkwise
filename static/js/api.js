/*
Blind Spot - AI Thinking Companion
API service for communicating with the backend
*/

const API_BASE = '/api/v1';

/**
 * Initialize API service (placeholder for future enhancements)
 */
export async function initAPI() {
    // Test API connectivity
    try {
        const response = await fetch('/health');
        if (!response.ok) {
            throw new Error(`Health check failed: ${response.status}`);
        }
        console.log('API connectivity verified');
    } catch (error) {
        console.warn('API health check failed:', error);
        // Don't fail initialization - might be offline or CORS issue in dev
    }
}

/**
 * Analyze a decision via the API
 * @param {string} decision - The decision being considered
 * @param {string|null} details - Additional details about the decision
 * @param {string} reasons - Reasons for leaning a certain way
 * @param {string|null} decisionType - Type of decision
 * @returns {Promise<Object>} Analysis response
 */
export async function analyzeDecisionAPI(decision, details, reasons, decisionType) {
    const response = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            decision: decision,
            details: details,
            reasons: reasons,
            decision_type: decisionType
        }),
        credentials: 'same-origin'
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
            errorData.detail ||
            `Analysis failed: ${response.status} ${response.statusText}`
        );
    }

    return await response.json();
}

/**
 * Refine analysis based on user answers
 * @param {string} sessionId - Session identifier from initial analysis
 * @param {Array<Object>} answers - Array of {question_id, answer} objects
 * @returns {Promise<Object>} Refined analysis response
 */
export async function refineAnalysisAPI(sessionId, answers) {
    const response = await fetch(`${API_BASE}/refine`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            session_id: sessionId,
            answers: answers
        }),
        credentials: 'same-origin'
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
            errorData.detail ||
            `Refinement failed: ${response.status} ${response.statusText}`
        );
    }

    return await response.json();
}

/**
 * Get health status from API
 * @returns {Promise<Object>} Health response
 */
export async function getHealthStatus() {
    const response = await fetch('/health', {
        credentials: 'same-origin'
    });

    if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
    }

    return await response.json();
}

// Helper function to handle API errors
export function handleApiError(error) {
    console.error('API Error:', error);

    // Network errors
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Unable to connect to the server. Please check your internet connection and try again.');
    }

    // Re-throw other errors
    throw error;
}