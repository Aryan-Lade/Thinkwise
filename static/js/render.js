/*
Blind Spot - AI Thinking Companion
Rendering logic for UI components
*/

import { state } from './state.js';

/**
 * Initialize rendering (call after state is initialized)
 */
export async function initRendering() {
    // Initial render
    renderLanding();
    console.log('Rendering module initialized');
}

/**
 * Render the landing page (initial state)
 */
function renderLanding() {
    // Form is already in HTML, just ensure it's ready
    state.elements.decisionInput.focus();
}

/**
 * Render analysis results in the results cards
 * @param {Object} analysis - Analysis response from API
 */
export function renderResults(analysis) {
    if (!analysis) return;

    // Store analysis in state for later use
    state.analysis = analysis;

    // Render each card
    renderFocusCard(analysis);
    renderMissingCard(analysis);
    renderAssumptionsCard(analysis);
    renderConflictsCard(analysis);
    renderQuestionsCard(analysis);
    renderBiasesCard(analysis);

    // Show results section
    state.elements.resultsSection.classList.remove('hidden');
}

/**
 * Render the "What you're focusing on" card
 * @param {Object} analysis - Analysis response
 */
function renderFocusCard(analysis) {
    const content = state.elements.focusCard.querySelector('.card-body');
    content.innerHTML = '';

    // Create sections for different types of information
    if (analysis.reasoning_map.stated_factors && analysis.reasoning_map.stated_factors.length > 0) {
        const factorsSection = document.createElement('div');
        factorsSection.className = 'info-section';
        factorsSection.innerHTML = `
            <h4 class="section-subtitle">Factors you mentioned:</h4>
            <ul class="info-list">
                ${analysis.reasoning_map.stated_factors.map(factor => `<li>${escapeHTML(factor)}</li>`).join('')}
            </ul>
        `;
        content.appendChild(factorsSection);
    }

    if (analysis.reasoning_map.stated_reasons && analysis.reasoning_map.stated_reasons.length > 0) {
        const reasonsSection = document.createElement('div');
        reasonsSection.className = 'info-section';
        reasonsSection.innerHTML = `
            <h4 class="section-subtitle">Your stated reasons:</h4>
            <ul class="info-list">
                ${analysis.reasoning_map.stated_reasons.map(reason => `<li>${escapeHTML(reason)}</li>`).join('')}
            </ul>
        `;
        content.appendChild(reasonsSection);
    }

    if (analysis.reasoning_map.most_visible_factors && analysis.reasoning_map.most_visible_factors.length > 0) {
        const visibleSection = document.createElement('div');
        visibleSection.className = 'info-section';
        visibleSection.innerHTML = `
            <h4 class="section-subtitle">What dominates your attention:</h4>
            <ul class="info-list">
                ${analysis.reasoning_map.most_visible_factors.map(factor => `<li>${escapeHTML(factor)}</li>`).join('')}
            </ul>
        `;
        content.appendChild(visibleSection);
    }

    if (analysis.reasoning_map.thin_or_missing_areas && analysis.reasoning_map.thin_or_missing_areas.length > 0) {
        const thinSection = document.createElement('div');
        thinSection.className = 'info-section';
        thinSection.innerHTML = `
            <h4 class="section-subtitle">Areas less developed in your thinking:</h4>
            <ul class="info-list">
                ${analysis.reasoning_map.thin_or_missing_areas.map(area => `<li>${escapeHTML(area)}</li>`).join('')}
            </ul>
        `;
        content.appendChild(thinSection);
    }

    // If no content, show placeholder
    if (content.children.length === 0) {
        content.innerHTML = '<p class="placeholder-text">No specific factors identified yet.</p>';
    }
}

/**
 * Render the "What might be missing" card
 * @param {Object} analysis - Analysis response
 */
function renderMissingCard(analysis) {
    const content = state.elements.missingCard.querySelector('.card-body');
    content.innerHTML = '';

    if (analysis.overlooked_factors && analysis.overlooked_factors.length > 0) {
        analysis.overlooked_factors.forEach(factor => {
            const factorElement = document.createElement('div');
            factorElement.className = 'factor-item';
            factorElement.innerHTML = `
                <h4 class="factor-title">${escapeHTML(factor.text)}</h4>
                <p class="factor-explanation">${escapeHTML(factor.why_it_matters)}</p>
                <div class="factor-actions">
                    <button class="btn btn-sm btn-outline toggle-btn"
                            data-factor-id="${factor.id}"
                            data-card="missing">
                        Already considered
                    </button>
                </div>
            `;
            content.appendChild(factorElement);
        });
    } else {
        content.innerHTML = '<p class="placeholder-text">No overlooked factors identified.</p>';
    }

    // Add event listeners to toggle buttons
    content.querySelectorAll('.toggle-btn').forEach(button => {
        button.addEventListener('click', () => toggleFactor(button));
    });
}

/**
 * Render the "Assumptions to examine" card
 * @param {Object} analysis - Analysis response
 */
function renderAssumptionsCard(analysis) {
    const content = state.elements.assumptionsCard.querySelector('.card-body');
    content.innerHTML = '';

    if (analysis.assumptions && analysis.assumptions.length > 0) {
        analysis.assumptions.forEach(assumption => {
            const assumptionElement = document.createElement('div');
            assumptionElement.className = 'assumption-item';
            assumptionElement.innerHTML = `
                <h4 class="assumption-title">${escapeHTML(assumption.text)}</h4>
                <p class="assumption-explanation">${escapeHTML(assumption.how_to_test)}</p>
                <div class="assumption-actions">
                    <button class="btn btn-sm btn-outline toggle-btn"
                            data-assumption-id="${assumption.id}"
                            data-card="assumptions">
                        Worth exploring
                    </button>
                </div>
            `;
            content.appendChild(assumptionElement);
        });
    } else {
        content.innerHTML = '<p class="placeholder-text">No assumptions identified.</p>';
    }

    // Add event listeners to toggle buttons
    content.querySelectorAll('.toggle-btn').forEach(button => {
        button.addEventListener('click', () => toggleAssumption(button));
    });
}

/**
 * Render the "Where your reasoning may pull against itself" card
 * @param {Object} analysis - Analysis response
 */
function renderConflictsCard(analysis) {
    const content = state.elements.conflictsCard.querySelector('.card-body');
    content.innerHTML = '';

    if (analysis.conflicts && analysis.conflicts.length > 0) {
        analysis.conflicts.forEach(conflict => {
            const conflictElement = document.createElement('div');
            conflictElement.className = 'conflict-item';
            conflictElement.innerHTML = `
                <div class="conflict-statements">
                    <p class="statement-a">"${escapeHTML(conflict.statement_a)}"</p>
                    <p class="statement-b">"${escapeHTML(conflict.statement_b)}"</p>
                </div>
                <p class="conflict-explanation">${escapeHTML(conflict.tension)}</p>
            `;
            content.appendChild(conflictElement);
        });
    } else {
        content.innerHTML = '<p class="placeholder-text">No conflicts identified.</p>';
    }
}

/**
 * Render the "Questions to sit with" card
 * @param {Object} analysis - Analysis response
 */
function renderQuestionsCard(analysis) {
    const content = state.elements.questionsCard.querySelector('.card-body');
    content.innerHTML = '';

    if (analysis.questions && analysis.questions.length > 0) {
        // Group questions by theme for better display
        const questionsByTheme = {};
        analysis.questions.forEach(question => {
            if (!questionsByTheme[question.theme]) {
                questionsByTheme[question.theme] = [];
            }
            questionsByTheme[question.theme].push(question);
        });

        Object.keys(questionsByTheme).forEach(theme => {
            const themeSection = document.createElement('div');
            themeSection.className = 'theme-section';

            const themeTitle = document.createElement('h4');
            themeTitle.className = 'theme-title';
            themeTitle.textContent = theme.charAt(0).toUpperCase() + theme.slice(1).replace('_', ' ');
            themeSection.appendChild(themeTitle);

            const questionsList = document.createElement('div');
            questionsList.className = 'questions-list';

            questionsByTheme[theme].forEach(question => {
                const questionElement = document.createElement('div');
                questionElement.className = 'question-item';
                questionElement.innerHTML = `
                    <p class="question-text">${escapeHTML(question.text)}</p>
                `;
                questionsList.appendChild(questionElement);
            });

            themeSection.appendChild(questionsList);
            content.appendChild(themeSection);
        });
    } else {
        content.innerHTML = '<p class="placeholder-text">No questions generated.</p>';
    }
}

/**
 * Render the "Possible thinking traps" card
 * @param {Object} analysis - Analysis response
 */
function renderBiasesCard(analysis) {
    const content = state.elements.biasesCard.querySelector('.card-body');
    content.innerHTML = '';

    if (analysis.possible_biases && analysis.possible_biases.length > 0) {
        analysis.possible_biases.forEach(bias => {
            const biasElement = document.createElement('div');
            biasElement.className = 'bias-item';
            biasElement.innerHTML = `
                <h4 class="bias-title">${escapeHTML(bias.name)}</h4>
                <p class="bias-explanation">${escapeHTML(bias.why_it_may_apply)}</p>
            `;
            content.appendChild(biasElement);
        });
    } else {
        content.innerHTML = '<p class="placeholder-text">No thinking patterns identified.</p>';
    }
}

/**
 * Render the reflection questions
 * @param {Array<Object>} questions - Array of question objects
 */
export function renderReflectionQuestions(questions) {
    const list = state.elements.questionsList;
    list.innerHTML = '';

    if (questions && questions.length > 0) {
        questions.forEach(question => {
            const questionItem = document.createElement('div');
            questionItem.className = 'question-item';
            questionItem.innerHTML = `
                <div class="question-header">
                    <span class="question-theme">${escapeHTML(question.theme.toUpperCase())}</span>
                    <p class="question-text">${escapeHTML(question.text)}</p>
                </div>
                <textarea
                    class="answer-input"
                    rows="3"
                    placeholder="Take your time to think about this question..."
                    data-question-id="${escapeHTML(question.id)}"
                ></textarea>
            `;
            list.appendChild(questionItem);
        });
    } else {
        list.innerHTML = '<p class="placeholder-text">No questions to reflect on.</p>';
    }
}

/**
 * Render the thinking summary
 * @param {Object|null} refinement - Refinement response (can be null)
 * @param {Array<Object>} answers - User answers to questions
 */
export function renderSummary(refinement, answers) {
    const content = state.elements.summaryContent;

    // If we have refinement data, use it; otherwise build from initial analysis
    if (refinement) {
        // Use refinement data
        content.innerHTML = refinement.thinking_summary || generateFallbackSummary(state.analysis, answers);
    } else {
        // Generate summary from initial analysis only
        content.innerHTML = generateFallbackSummary(state.analysis, answers);
    }
}

/**
 * Generate a fallback summary when refinement data isn't available
 * @param {Object} analysis - Initial analysis response
 * @param {Array<Object>} answers - User answers
 * @returns {string} HTML-formatted summary
 */
function generateFallbackSummary(analysis, answers) {
    if (!analysis) return '<p>No analysis data available.</p>';

    // Build summary similar to what the backend would generate
    const parts = [];

    parts.push('# My Thinking Summary');
    parts.push('');
    parts.push('This document captures your decision-making process and initial insights.');
    parts.push('');
    parts.push('---');
    parts.push('');

    parts.push('## Your Decision');
    parts.push('');
    parts.push(`**Decision:** ${escapeHTML(analysis.decision_restated)}`);
    if (state.details) {
        parts.push(`**Details:** ${escapeHTML(state.details)}`);
    }
    parts.push(`**Your reasons:** ${escapeHTML(state.reasons)}`);
    if (state.decisionType) {
        parts.push(`**Decision type:** ${escapeHTML(state.decisionType)}`);
    }
    parts.push('');

    parts.push('## What You\'re Focusing On');
    parts.push('');

    if (analysis.reasoning_map.stated_factors && analysis.reasoning_map.stated_factors.length > 0) {
        parts.push('**Factors you mentioned:**');
        analysis.reasoning_map.stated_factors.forEach(factor => {
            parts.push(`- ${escapeHTML(factor)}`);
        });
        parts.push('');
    }

    if (analysis.reasoning_map.stated_reasons && analysis.reasoning_map.stated_reasons.length > 0) {
        parts.push('**Your stated reasons:**');
        analysis.reasoning_map.stated_reasons.forEach(reason => {
            parts.push(`- ${escapeHTML(reason)}`);
        });
        parts.push('');
    }

    if (analysis.reasoning_map.most_visible_factors && analysis.reasoning_map.most_visible_factors.length > 0) {
        parts.push('**What dominates your attention:**');
        analysis.reasoning_map.most_visible_factors.forEach(factor => {
            parts.push(`- ${escapeHTML(factor)}`);
        });
        parts.push('');
    }

    // Add overlooked factors
    if (analysis.overlooked_factors && analysis.overlooked_factors.length > 0) {
        parts.push('## What Might Be Missing');
        parts.push('');
        analysis.overlooked_factors.forEach(factor => {
            parts.push(`### ${escapeHTML(factor.text)}`);
            parts.push('');
            parts.push(`*Why this matters:* ${escapeHTML(factor.why_it_matters)}`);
            parts.push('');
        });
    }

    // Add assumptions
    if (analysis.assumptions && analysis.assumptions.length > 0) {
        parts.push('## Assumptions to Examine');
        parts.push('');
        analysis.assumptions.forEach(assumption => {
            parts.push(`### ${escapeHTML(assumption.text)}`);
            parts.push('');
            parts.push(`*How to test this:* ${escapeHTML(assumption.how_to_test)}`);
            parts.push('');
        });
    }

    // Add conflicts
    if (analysis.conflicts && analysis.conflicts.length > 0) {
        parts.push('## Where Your Reasoning May Pull Against Itself');
        parts.push('');
        analysis.conflicts.forEach(conflict => {
            parts.push('### Tension between two statements:');
            parts.push('');
            parts.push(`> ${escapeHTML(conflict.statement_a)}`);
            parts.push(`> ${escapeHTML(conflict.statement_b)}`);
            parts.push('');
            parts.push(`*Why this tension exists:* ${escapeHTML(conflict.tension)}`);
            parts.push('');
        });
    }

    # Add questions if any
    if (analysis.questions && analysis.questions.length > 0) {
        parts.push('## Questions for Further Reflection');
        parts.push('');
        analysis.questions.forEach(question => {
            parts.push(`### ${escapeHTML(question.theme.charAt(0).toUpperCase() + question.theme.slice(1).replace('_', ' '))}: ${escapeHTML(question.text)}`);
            parts.push('');

            # Find user answer if available
            const userAnswer = answers.find(ans => ans.question_id === question.id);
            if (userAnswer && userAnswer.answer.trim()) {
                parts.push(`**Your response:** ${escapeHTML(userAnswer.answer)}`);
                parts.push('');
            } else {
                parts.push('*Your response: [Not answered]*');
                parts.push('');
            }
        });
    }

    parts.push('---');
    parts.push('');
    parts.push('**Remember:** This tool asks questions to help you think more deeply.');
    parts.push('The decision belongs entirely to you.');
    parts.push('');
    parts.push(`*Generated on: ${new Date().toLocaleString()}*`);

    return parts.join('\n');
}

/**
 * Toggle factor state (already considered/worth exploring)
 * @param {HTMLButtonElement} button - The button that was clicked
 */
function toggleFactor(button) {
    const isConsidered = button.textContent.includes('Already considered');
    const newText = isConsidered ? 'Worth exploring' : 'Already considered';
    button.textContent = newText;

    # Toggle button styling
    button.classList.toggle('btn-outline');
    button.classList.toggle('btn-secondary');

    # Update ARIA attributes for accessibility
    const isPressed = button.textContent === 'Already considered';
    button.setAttribute('aria-pressed', isPressed);
}

/**
 * Toggle assumption state (worth exploring)
 * @param {HTMLButtonElement} button - The button that was clicked
 */
function toggleAssumption(button) {
    const isExploring = button.textContent === 'Worth exploring';
    const newText = isExploring ? 'Explored' : 'Worth exploring';
    button.textContent = newText;

    # Toggle button styling
    button.classList.toggle('btn-outline');
    button.classList.toggle('btn-secondary');

    # Update ARIA attributes for accessibility
    const isPressed = button.textContent === 'Explored';
    button.setAttribute('aria-pressed', isPressed);
}

/**
 * Escape HTML special characters to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHTML(text) {
    if (text === null || text === undefined) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

/**
 * Format timestamp for display
 * @param {number} timestamp - Unix timestamp in seconds
 * @returns {string} Formatted date/time string
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp * 1000); # Convert to milliseconds
    return date.toLocaleString();
}

// Export functions for use in other modules
export { renderReflectionQuestions, renderSummary };