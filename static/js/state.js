/*
Blind Spot - AI Thinking Companion
Application state management
*/

let state = {
    // UI state
    currentView: 'landing', // landing, loading, results, reflection, summary
    isLoading: false,

    // Data state
    decision: '',
    details: '',
    reasons: '',
    decisionType: '',

    // Analysis results
    analysis: null,
    refinement: null,

    // Session management
    sessionId: null,

    // UI elements (will be populated in init)
    elements: {}
};

/**
 * Initialize application state
 */
export async function initState() {
    // Cache DOM elements
    state.elements = {
        // Form elements
        decisionForm: document.getElementById('decision-form'),
        decisionInput: document.getElementById('decision-input'),
        detailsInput: document.getElementById('details-input'),
        reasonsInput: document.getElementById('reasons-input'),
        decisionTypeSelect: document.getElementById('decision-type-select'),
        analyzeButton: document.getElementById('analyze-button'),
        exampleButton: document.getElementById('example-button'),
        formError: document.getElementById('form-error'),

        // Loading elements
        loadingSection: document.getElementById('loading-section'),

        // Results elements
        resultsSection: document.getElementById('results-section'),
        focusCard: document.getElementById('focus-card'),
        missingCard: document.getElementById('missing-card'),
        assumptionsCard: document.getElementById('assumptions-card'),
        conflictsCard: document.getElementById('conflicts-card'),
        questionsCard: document.getElementById('questions-card'),
        biasesCard: document.getElementById('biases-card'),

        // Reflection elements
        reflectionSection: document.getElementById('reflection-section'),
        reflectionForm: document.getElementById('reflection-form'),
        questionsList: document.getElementById('questions-list'),
        reflectButton: document.getElementById('reflect-button'),
        skipReflectionButton: document.getElementById('skip-reflection-button'),
        reflectionError: document.getElementById('reflection-error'),

        // Summary elements
        summarySection: document.getElementById('summary-section'),
        summaryContent: document.getElementById('summary-content'),
        copySummaryButton: document.getElementById('copy-summary-button'),
        downloadSummaryButton: document.getElementById('download-summary-button'),
        newAnalysisButton: document.getElementById('new-analysis-button'),

        // Banner
        resultsBanner: document.querySelector('.results-banner')
    };

    // Set up event listeners
    setupEventListeners();

    // Check for example flag in URL (for testing)
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('example') === 'internship') {
        await loadInternshipExample();
    }

    console.log('Application state initialized');
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Form submission
    state.elements.decisionForm.addEventListener('submit', handleFormSubmit);

    // Example button
    state.elements.exampleButton.addEventListener('click', loadInternshipExample);

    // Reflection form
    state.elements.reflectionForm.addEventListener('submit', handleReflectionSubmit);
    state.elements.skipReflectionButton.addEventListener('click', skipToSummary);

    // Summary actions
    state.elements.copySummaryButton.addEventListener('click', copySummaryToClipboard);
    state.elements.downloadSummaryButton.addEventListener('click', downloadSummary);
    state.elements.newAnalysisButton.addEventListener('click', resetForNewAnalysis);

    // Handle Enter key in textareas
    const textareas = [
        state.elements.decisionInput,
        state.elements.detailsInput,
        state.elements.reasonsInput
    ];

    textareas.forEach(textarea => {
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                state.elements.decisionForm.dispatchEvent(new Event('submit'));
            }
        });
    });
}

/**
 * Handle form submission for initial analysis
 * @param {Event} event - Form submit event
 */
async function handleFormSubmit(event) {
    event.preventDefault();

    // Clear previous errors
    state.elements.formError.classList.remove('visible');
    state.elements.formError.textContent = '';

    // Gather form data
    const decision = state.elements.decisionInput.value.trim();
    const details = state.elements.detailsInput.value.trim() || null;
    const reasons = state.elements.reasonsInput.value.trim();
    const decisionType = state.elements.decisionTypeSelect.value;

    // Validate
    if (!decision) {
        showFormError('Please describe the decision you are considering');
        state.elements.decisionInput.focus();
        return;
    }

    if (!reasons) {
        showFormError('Please describe your reasons for leaning this way');
        state.elements.reasonsInput.focus();
        return;
    }

    // Update state
    state.decision = decision;
    state.details = details;
    state.reasons = reasons;
    state.decisionType = decisionType;

    // Start analysis
    await startAnalysis();
}

/**
 * Show form error message
 * @param {string} message - Error message to display
 */
function showFormError(message) {
    state.elements.formError.textContent = message;
    state.elements.formError.classList.add('visible');
    state.elements.decisionInput.focus();
}

/**
 * Start the analysis process
 */
async function startAnalysis() {
    try {
        setLoading(true);
        updateView('loading');

        // Call API to analyze decision
        const analysis = await analyzeDecisionAPI(
            state.decision,
            state.details,
            state.reasons,
            state.decisionType
        );

        // Store results
        state.analysis = analysis;
        state.sessionId = analysis.session_id;

        // Move to results view
        setLoading(false);
        updateView('results');

        // Render results
        renderResults(analysis);

    } catch (error) {
        console.error('Analysis failed:', error);
        setLoading(false);
        showErrorMessage(`Analysis failed: ${error.message || 'Unknown error'}`);
    }
}

/**
 * Load the internship example
 */
async function loadInternshipExample() {
    // Set form values to match the internship example from the problem statement
    state.elements.decisionInput.value = "Whether to accept a 6-month internship offer";
    state.elements.detailsInput.value = "Good stipend, close to home, working hours 9-5, role in software development, learning opportunities include industry tools, college schedule has classes Monday-Thursday";
    state.elements.reasonsInput.value = "Mainly considering it because the stipend is good, the company is close to home, and it will provide industry experience";
    state.elements.decisionTypeSelect.value = "career";

    // Focus on the analyze button
    state.elements.analyzeButton.focus();

    // Show a brief hint
    const originalText = state.elements.exampleButton.textContent;
    state.elements.exampleButton.textContent = "Example loaded!";
    setTimeout(() => {
        state.elements.exampleButton.textContent = originalText;
    }, 1500);
}

/**
 * Handle reflection form submission
 * @param {Event} event - Form submit event
 */
async function handleReflectionSubmit(event) {
    event.preventDefault();

    // Clear previous errors
    state.elements.reflectionError.classList.remove('visible');
    state.elements.reflectionError.textContent = '';

    // Gather answers
    const answerElements = document.querySelectorAll('.answer-input');
    const answers = [];

    let hasEmptyAnswer = false;
    answerElements.forEach((element, index) => {
        const answer = element.value.trim();
        if (!answer) {
            hasEmptyAnswer = true;
            element.classList.add('invalid');
        } else {
            element.classList.remove('invalid');
            answers.push({
                question_id: element.dataset.questionId,
                answer: answer
            });
        }
    });

    if (hasEmptyAnswer) {
        showReflectionError('Please provide answers to all questions');
        return;
    }

    try {
        setLoading(true);

        // Call API to refine analysis
        const refinement = await refineAnalysisAPI(state.sessionId, answers);

        // Store results
        state.refinement = refinement;

        // Move to summary view
        setLoading(false);
        updateView('summary');

        // Render summary
        renderSummary(refinement, answers);

    } catch (error) {
        console.error('Refinement failed:', error);
        setLoading(false);
        showReflectionError(`Refinement failed: ${error.message || 'Unknown error'}`);
    }
}

/**
 * Show reflection error message
 * @param {string} message - Error message to display
 */
function showReflectionError(message) {
    state.elements.reflectionError.textContent = message;
    state.elements.reflectionError.classList.add('visible');

    // Focus on first invalid input
    const firstInvalid = document.querySelector('.answer-input.invalid');
    if (firstInvalid) {
        firstInvalid.focus();
    }
}

/**
 * Skip reflection and go directly to summary
 */
function skipToSummary() {
    // Create empty answers array
    const answers = [];

    // Use initial analysis for summary
    updateView('summary');
    renderSummary(null, answers);
}

/**
 * Copy summary to clipboard
 */
function copySummaryToClipboard() {
    const summaryText = state.elements.summaryContent.textContent;

    navigator.clipboard.writeText(summaryText).then(() => {
        // Show success feedback
        const originalText = state.elements.copySummaryButton.textContent;
        state.elements.copySummaryButton.textContent = 'Copied!';
        setTimeout(() => {
            state.elements.copySummaryButton.textContent = originalText;
        }, 1500);
    }).catch(err => {
        console.error('Failed to copy:', err);
        showToast('Failed to copy to clipboard');
    });
}

/**
 * Download summary as markdown file
 */
function downloadSummary() {
    const summaryText = state.elements.summaryContent.textContent;
    const blob = new Blob([summaryText], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);

    // Create a filename based on timestamp and decision
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-');
    const decisionSnippet = state.decision
        .substring(0, 20)
        .toLowerCase()
        .replace(/[^a-z0-9]/g, '-');
    const filename = `blind-spot-summary-${timestamp}-${decisionSnippet}.md`;

    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    // Show success feedback
    const originalText = state.elements.downloadSummaryButton.textContent;
    state.elements.downloadSummaryButton.textContent = 'Downloaded!';
    setTimeout(() => {
        state.elements.downloadSummaryButton.textContent = originalText;
    }, 1500);
}

/**
 * Reset application for new analysis
 */
function resetForNewAnalysis() {
    // Clear form
    state.elements.decisionForm.reset();

    // Reset state
    state.decision = '';
    state.details = '';
    state.reasons = '';
    state.decisionType = '';
    state.analysis = null;
    state.refinement = null;
    state.sessionId = null;

    // Go back to landing view
    updateView('landing');

    // Focus on decision input
    state.elements.decisionInput.focus();
}

/**
 * Update the current view
 * @param {string} view - View to show (landing, loading, results, reflection, summary)
 */
function updateView(view) {
    // Hide all sections
    document.getElementById('landing-section').classList.add('hidden');
    document.getElementById('loading-section').classList.add('hidden');
    document.getElementById('results-section').classList.add('hidden');
    document.getElementById('reflection-section').classList.add('hidden');
    document.getElementById('summary-section').classList.add('hidden');

    // Show selected section
    const sectionMap = {
        landing: 'landing-section',
        loading: 'loading-section',
        results: 'results-section',
        reflection: 'reflection-section',
        summary: 'summary-section'
    };

    const sectionId = sectionMap[view];
    if (sectionId) {
        document.getElementById(sectionId).classList.remove('hidden');
    }

    state.currentView = view;

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Set loading state
 * @param {boolean} isLoading - Whether to show loading state
 */
function setLoading(isLoading) {
    state.isLoading = isLoading;
    state.elements.analyzeButton.disabled = isLoading;
    state.elements.exampleButton.disabled = isLoading;

    if (isLoading) {
        state.elements.analyzeButton.innerHTML = '<span class="spinner"></span> Analyzing...';
        state.elements.exampleButton.innerHTML = '<span class="spinner"></span>';
    } else {
        state.elements.analyzeButton.textContent = 'Analyze My Thinking';
        state.elements.exampleButton.textContent = 'Try the internship example';
    }
}

/**
 * Show error message in loading state
 * @param {string} message - Error message
 */
function showErrorMessage(message) {
    // TODO: Implement proper error UI in loading state
    console.error('Error:', message);
    alert(`Error: ${message}`); // Fallback for now
    updateView('landing');
}

/**
 * Show toast notification (simple implementation)
 * @param {string} message - Message to show
 */
function showToast(message) {
    // Simple toast implementation
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.backgroundColor = 'var(--bg-tertiary)';
    toast.style.color = 'var(--text-primary)';
    toast.style.padding = 'var(--spacing-sm) var(--spacing-lg)';
    toast.style.borderRadius = 'var(--radius-md)';
    toast.style.boxShadow = 'var(--shadow-md)';
    toast.style.zIndex = '1000';

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Initialize when called
export { state };