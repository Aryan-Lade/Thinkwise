# Blind Spot: AI Thinking Companion

**Live Demo URL:** [INSERT YOUR CLOUD RUN URL HERE]

**GitHub Repository:** https://github.com/Aryan-Lade/Thinkwise

## Project Overview

Blind Spot is an AI-powered thinking companion designed to help users identify blind spots in their reasoning when making decisions. Rather than providing advice or recommendations, the system maps what users are focusing on, reveals overlooked factors, questions unstated assumptions, highlights conflicts in reasoning, and asks thoughtful questions to promote deeper reflection.

The application helps users think more critically about decisions by making their implicit thought processes explicit, without making the decision for them.

## Key Features

- **Decision Analysis**: Users describe their decision, known details, and reasons for leaning a certain way
- **Blind Spot Identification**: AI identifies overlooked factors, assumptions, and reasoning conflicts
- **Reflective Questioning**: Generates thoughtful, non-leading questions for deeper reflection
- **Iterative Refinement**: Users can answer questions to refine the analysis in subsequent rounds
- **Thinking Summary**: Creates a personalized markdown summary of the entire thinking process
- **Example Scenarios**: One-click loading of example decisions (internship, career change, purchase)
- **Privacy-Focused**: No personal data storage; all processing is session-based and temporary
- **Accessible**: WCAG 2.1 AA compliant with proper keyboard navigation, screen reader support, and color contrast
- **Secure**: Input validation, output sanitization, rate limiting, and crisis detection
- **Deployed**: Running on Google Cloud Run in the asia-south1 region

## Technical Implementation

- **Backend**: Python 3.12 with FastAPI, Pydantic v2, and Google Gemini API
- **Frontend**: Semantic HTML5, modern CSS3, and vanilla JavaScript ES modules
- **AI Integration**: Structured output via Gemini API with schema validation and response guards
- **Security**: Input validation, output sanitization, rate limiting, and crisis detection
- **Deployment**: Docker container deployed to Google Cloud Run
- **Testing**: Comprehensive test suite with unit, integration, and security tests

## Compliance with Requirements

This implementation addresses all requirements specified in the problem statement:

- **R1-R5**: Complete reasoning mapping, overlooked factor identification, assumption questioning, conflict detection, and question generation
- **R6**: Three-level protection against recommendations (system instruction, schema validation, output guard)
- **R7**: Reflection loop allows users to refine analysis based on their answers
- **R8**: Personal thinking summary available for copy/download as markdown
- **R9**: Works for any decision type with graceful handling of vague inputs
- **R10**: Safety protocols detect crisis indicators and provide supportive responses
- **R11**: Meaningful AI use through structured analysis, not generic chatbot

## Usage Instructions

1. Visit the live demo URL
2. Describe your decision in the provided form
3. Add any known details and your reasons for leaning a certain way
4. Optionally select a decision type
5. Click "Analyze My Thinking" to begin
6. Review the analysis cards showing what you might be overlooking
7. Answer the reflective questions to deepen your analysis
8. Generate your personalized thinking summary
9. Copy or download your summary for future reference

## Design Notes

- Interface closely follows the visual design of the DealMind reference implementation
- Dark theme with appropriate color contrast (WCAG 2.1 AA compliant)
- Responsive design works from mobile (320px) to desktop screens
- Subtle animations respect reduced motion preferences
- Accessible forms with proper labels, error handling, and focus management
- Semantic HTML structure with appropriate landmarks and heading hierarchy

## Data Flow

1. User submits decision details via web form
2. Backend validates input and checks for safety concerns
3. If safe, request is sent to Gemini AI with structured prompt
4. AI returns JSON analysis following predefined schema
5. Response is checked for directive language and sanitized if needed
6. Results are cached for performance and stored in session
7. User can refine analysis by answering questions
8. Final thinking summary is generated and presented to user