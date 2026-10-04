"""
Application constants
"""

# HTTP Status Codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_CONFLICT = 409
HTTP_TOO_MANY_REQUESTS = 429
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_SERVICE_UNAVAILABLE = 503

# Rate Limiting
RATE_LIMIT_HEADER_LIMIT = "X-RateLimit-Limit"
RATE_LIMIT_HEADER_REMAINING = "X-RateLimit-Remaining"
RATE_LIMIT_HEADER_RESET = "X-RateLimit-Reset"
RATE_LIMIT_HEADER_RETRY_AFTER = "Retry-After"

# Cache Keys
CACHE_KEY_ANALYZE_PREFIX = "analyze:"
CACHE_KEY_REFINE_PREFIX = "refine:"

# Session
SESSION_ID_LENGTH = 32
SESSION_TTL_HOURS = 24

# Validation Limits
MAX_DECISION_LENGTH = 500
MAX_DETAILS_LENGTH = 2000
MAX_REASONS_LENGTH = 1000
MIN_DECISION_LENGTH = 5
MIN_REASONS_LENGTH = 5

# Gemini
GEMINI_DEFAULT_TEMPERATURE = 0.7
GEMINI_MAX_OUTPUT_TOKENS = 2048
GEMINI_TOP_P = 0.8
GEMINI_TOP_K = 40

# Security
ALLOWED_ORIGINS = ["*"]  # Should be restricted in production
SECURE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

# Content Security Policy
CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data: https:; "
    "connect-src 'self'; "
    "frame-ancestors 'none';"
)

# Decision Types
DECISION_TYPES = [
    "career",
    "education",
    "financial",
    "startup",
    "personal",
    "relationship",
    "health",
    "purchase",
    "other",
]

# Default Values
DEFAULT_GEMINI_MODEL = "gemini-flash-lite-latest"
DEFAULT_CACHE_TTL = 300  # 5 minutes
DEFAULT_CACHE_MAXSIZE = 100  # Maximum cache entries
DEFAULT_SESSION_TTL_HOURS = 24  # Session TTL in hours
DEFAULT_RATE_LIMIT = 100  # requests per minute
