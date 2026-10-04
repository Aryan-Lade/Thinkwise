# Security Policy

## Supported Versions

We provide security updates for the following versions of the Blind Spot AI Thinking Companion:

| Version | Supported          |
|---------|--------------------|
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

Please report suspected security vulnerabilities to security@aryanlade.com. You will receive a response within 48 hours. If the issue is confirmed, we will release a patch as soon as possible depending on complexity but historically within a few days.

Please do not report security vulnerabilities through public issue trackers or public forums.

We appreciate your efforts to responsibly disclose your findings, and will make every effort to acknowledge your contributions.

## Security Features

The Blind Spot application implements multiple layers of security to protect user data and ensure safe operation:

### Input Validation
- All user inputs are validated using Pydantic models with strict length limits
- Decision text: maximum 500 characters
- Details text: maximum 2000 characters  
- Reasons text: maximum 1000 characters
- All inputs are stripped of whitespace and checked for empty values

### Output Sanitization
- AI responses are scanned for directive language using pattern matching
- Any detected directive phrases are replaced with neutral placeholders
- Guardrails ensure the AI never provides recommendations or advice

### Secure Dependencies
- All dependencies are pinned to specific versions
- Regular dependency scanning using safety tools
- No known vulnerable dependencies in production

### Data Protection
- No personal data is stored permanently
- Session data is stored in memory with TTL (time-to-live) expiration
- No logging of user-provided decision content
- Error messages are sanitized to prevent information leakage

### API Security
- CORS policies restrict origins to trusted domains
- Rate limiting prevents abuse (100 requests per minute by default)
- Request size limits prevent oversized payloads
- HTTP security headers are implemented where appropriate

### AI Safety
- Crisis detection identifies potential self-harm or harmful intent
- Safety protocols provide appropriate resources instead of analysis
- Content filters prevent generation of harmful advice
- Temperature settings keep AI responses focused and predictable

### Deployment Security
- Containerized deployment with non-root user
- Minimal base image reduces attack surface
- Secrets managed through Google Secret Manager
- Regular security updates to base images

## Security Best Practices for Users

1. **Keep dependencies updated**: Regularly run `make deps-check` to check for outdated packages
2. **Monitor security advisories**: Watch for announcements about dependencies used
3. **Use environment variables**: Never commit secrets to version control
4. **Review logs**: Monitor application logs for unusual activity
5. **Regular penetration testing**: Consider periodic security assessments

## Common Vulnerabilities and Exposures (CVEs)

We actively monitor for CVEs affecting our dependencies and update promptly. Current status of major dependencies:

- FastAPI: No known critical CVEs
- Pydantic: No known critical CVEs  
- Google GenAI SDK: No known critical CVEs
- Uvicorn: No known critical CVEs

## Contact

For security-related inquiries, please contact: security@aryanlade.com

## Acknowledgments

We thank the open-source community for their security tools and practices that help keep this application secure.