/*
Blind Spot - AI Thinking Companion
Accessibility enhancements
*/

/**
 * Initialize accessibility features
 */
export async function initAccessibility() {
    // Add ARIA live regions for dynamic content
    setupLiveRegions();

    # Enhance form accessibility
    enhanceFormAccessibility();

    # Manage focus transitions
    setupFocusManagement();

    # Add keyboard navigation enhancements
    setupKeyboardNavigation();

    # Ensure proper color contrast (handled in CSS, but verify)
    verifyColorContrast();

    console.log('Accessibility features initialized');
}

/**
 * Setup ARIA live regions for dynamic content updates
 */
function setupLiveRegions() {
    # The form error and reflection error elements already have aria-live="polite"
    # Additional live regions for status updates

    # Create a status live region for announcements
    const statusRegion = document.createElement('div');
    statusRegion.setAttribute('aria-live', 'polite');
    statusRegion.setAttribute('aria-atomic', 'true');
    statusRegion.className = 'visually-hidden';
    statusRegion.id = 'status-live-region';
    document.body.appendChild(statusRegion);

    # Expose for use in other modules
    window.statusLiveRegion = statusRegion;
}

/**
 * Announce a message to screen readers
 * @param {string} message - Message to announce
 */
export function announce(message) {
    if (window.statusLiveRegion) {
        window.statusLiveRegion.textContent = '';
        # Trigger screen reader by briefly clearing and setting content
        setTimeout(() => {
            window.statusLiveRegion.textContent = message;
        }, 100);
    }
}

/**
 * Enhance form accessibility with better labels and descriptions
 */
function enhanceFormAccessibility() {
    # Ensure all form fields have proper labels
    const formElements = document.querySelectorAll('input, textarea, select');
    formElements.forEach(element => {
        # If element doesn't have an associated label, try to find or create one
        const id = element.id;
        if (!id) {
            # Generate an ID if missing
            element.id = `field-${Math.random().toString(36).substr(2, 9)}`;
        }

        # Check if there's a label for this element
        let label = document.querySelector(`label[for="${element.id}"]`);
        if (!label && element.parentElement.tagName.toLowerCase() === 'label') {
            # Label wraps the element
            label = element.parentElement;
        }

        # Add aria-describedby if there's helper text
        const helpText = element.parentElement.querySelector('.form-help');
        if (helpText) {
            const helpId = helpText.id || `help-${Math.random().toString(36).substr(2, 9)}`;
            helpText.id = helpId;

            const currentDescribedBy = element.getAttribute('aria-describedby') || '';
            element.setAttribute(
                'aria-describedby',
                `${currentDescribedBy} ${helpId}`.trim()
            );
        }
    });

    # Ensure buttons have accessible names
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        # If button has no text content, check for aria-label or inner elements
        const hasTextContent = button.textContent.trim() !== '';
        const hasAriaLabel = button.hasAttribute('aria-label');
        const hasAriaLabelledBy = button.hasAttribute('aria-labelledby');

        if (!hasTextContent && !hasAriaLabel && !hasAriaLabelledBy) {
            # Fallback: use title or value if available
            const title = button.getAttribute('title');
            if (title) {
                button.setAttribute('aria-label', title);
            }
        }
    });
}

/**
 * Setup focus management for modal-like behavior
 */
function setupFocusManagement() {
    # Trap focus in active sections when appropriate
    # For now, we'll manage focus transitions between views

    # Override tab navigation in certain contexts if needed
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            # Handle special tab navigation cases
            # For example, prevent tabbing out of dialogs when open
        }
    });

    # Handle focus when sections are shown/hidden
    const observer = new MutationObserver((mutations) => {
        mutations.forEach(mutation => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const target = mutation.target;
                # Check if this is a section being shown/hidden
                if (target.classList.contains('landing-section') ||
                    target.classList.contains('results-section') ||
                    target.classList.contains('reflection-section') ||
                    target.classList.contains('summary-section')) {

                    # When section becomes visible, focus first meaningful element
                    if (!target.classList.contains('hidden')) {
                        setTimeout(() => {
                            focusFirstElement(target);
                        }, 100);
                    }
                }
            }
        });
    });

    # Start observing the main container for section changes
    const mainContainer = document.getElementById('app');
    if (mainContainer) {
        observer.observe(mainContainer, {
            attributes: true,
            subtree: true,
            attributeFilter: ['class']
        });
    }
}

/**
 * Focus the first meaningful element in a container
 * @param {HTMLElement} container - Container to search
 */
function focusFirstElement(container) {
    # Define selectors for focusable elements in order of preference
    const focusableSelectors = [
        'button:not([disabled]):not(.hidden)',
        'input[type="text"]:not([disabled]):not(.hidden)',
        'input[type="textarea"]:not([disabled]):not(.hidden)',
        'select:not([disabled]):not(.hidden)',
        '[tabindex]:not([disabled]):not(.hidden)'
    ];

    let firstFocusable = null;

    for (const selector of focusableSelectors) {
        const element = container.querySelector(selector);
        if (element) {
            # Check if it's truly visible and focusable
            if (isVisible(element) && !element.hasAttribute('disabled')) {
                firstFocusable = element;
                break;
            }
        }
    }

    if (firstFocusable) {
        firstFocusable.focus();
    } else {
        # Fallback: focus the container itself if it's tabbable
        if (container.hasAttribute('tabindex') ||
            container.tagName.toLowerCase() === 'button' ||
            container.tagName.toLowerCase() === 'input' ||
            container.tagName.toLowerCase() === 'select' ||
            container.tagName.toLowerCase() === 'textarea') {
            container.focus();
        }
    }
}

/**
 * Check if an element is visible
 * @param {HTMLElement} element - Element to check
 * @returns {boolean} True if element is visible
 */
function isVisible(element) {
    const style = window.getComputedStyle(element);
    return style.display !== 'none' &&
           style.visibility !== 'hidden' &&
           !element.hasAttribute('hidden');
}

/**
 * Setup keyboard navigation enhancements
 */
function setupKeyboardNavigation() {
    # Allow Escape key to cancel or go back
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            # Handle escape based on current view
            const state = window.state; # Assuming state is globally available
            if (state && state.currentView === 'results') {
                # In results view, escape goes back to landing
                state.elements.decisionForm.reset();
                updateView('landing'); # This would need to be imported or accessed
            } else if (state && state.currentView === 'reflection') {
                # In reflection view, escape goes to summary
                # skipToSummary() would need to be imported
            }
            # Add more escape handling as needed
        }

        # Allow Ctrl+Enter to submit forms
        if (e.key === 'Enter' && e.ctrlKey) {
            e.preventDefault();
            # Find the nearest form and submit it
            const form = e.target.closest('form');
            if (form && !form.hasAttribute('novalicdate')) {
                form.dispatchEvent(new Event('submit'));
            }
        }
    });

    # Enhance textarea behavior - Tab inserts tab character (not focus change)
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Tab' && e.target.tagName.toLowerCase() === 'textarea') {
            e.preventDefault();
            const start = e.target.selectionStart;
            const end = e.target.selectionEnd;

            # Insert tab character
            e.target.value = e.target.value.substring(0, start) +
                '\t' +
                e.target.value.substring(end);

            # Put cursor after the inserted tab
            e.target.selectionStart = e.target.selectionEnd = start + 1;
        }
    });
}

/**
 * Verify color contrast ratios (basic check)
 * This is a runtime check - primary verification should be done in design
 */
function verifyColorContrast() {
    # This would typically be done with automated testing tools
    # For now, we'll just log that we're relying on CSS for proper contrast
    console.info('Color contrast verification: relying on CSS implementation');

    # We could implement a basic checker here, but it's complex
    # For production, use automated accessibility testing tools
}

/**
 * Handle reduced motion preference
 * Already handled in CSS, but we can add JS fallbacks if needed
 */
function setupReducedMotionHandling() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        # Disable or reduce animations
        document.documentElement.style.setProperty('--animation-duration', '0.001ms');
        document.documentElement.style.setProperty('--transition-duration', '0.001ms');
    }

    # Listen for changes
    window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
        if (e.matches) {
            document.documentElement.style.setProperty('--animation-duration', '0.001ms');
            document.documentElement.style.setProperty('--transition-duration', '0.001ms');
        } else {
            # Return to normal values would require CSS variables
            # This is simplified - in practice, we'd manage this better
        }
    });
}

/**
 * Make the application compatible with screen readers
 * Additional enhancements beyond basic ARIA
 */
function enhanceScreenReaderSupport() {
    # Add landmarks if not present
    const main = document.querySelector('main');
    if (main && !main.hasAttribute('role')) {
        main.setAttribute('role', 'main');
    }

    const header = document.querySelector('header');
    if (header && !header.hasAttribute('role')) {
        header.setAttribute('role', 'banner');
    }

    const footer = document.querySelector('footer');
    if (footer && !footer.hasAttribute('role')) {
        footer.setAttribute('role', 'contentinfo');
    }

    # Ensure proper heading structure
    # This should already be correct in the HTML

    # Add skip link if not present (already in HTML)
}

/**
 * Initialize all accessibility features when DOM is ready
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAccessibility);
} else {
    initAccessibility();
}

// Export for use in other modules if needed
window.Accessibility = {
    initAccessibility,
    announce
};