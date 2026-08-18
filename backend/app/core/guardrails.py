"""
Guardrails and safety utilities for input validation, prompt injection defense,
and output secret sanitization.
"""
import re
import logging

logger = logging.getLogger(__name__)

# Regular expressions for common prompt injection patterns
INJECTION_PATTERNS = [
    r"(?i)\bignore\s+(all\s+)?(previous|prior)\s+instructions?\b",
    r"(?i)\breveal\s+(your\s+)?(system\s+prompt|instructions?|api\s*key)\b",
    r"(?i)\bprint\s+(your\s+)?(system\s+prompt|env|environment|settings)\b",
    r"(?i)\b(system\s*prompt|system\s*instructions)\s*:",
    r"(?i)\bDAN\s+mode\b",
    r"(?i)\bjailbreak\b",
]

# Patterns for sensitive keys or internal tokens in output
SECRET_PATTERNS = [
    (r"gsk_[A-Za-z0-9_-]{20,}", "[REDACTED_GROQ_KEY]"),
    (r"AIzaSy[A-Za-z0-9_-]{33}", "[REDACTED_GEMINI_KEY]"),
    (r"sk-[A-Za-z0-9]{32,}", "[REDACTED_API_KEY]"),
]


def validate_and_sanitize_input(question: str, max_length: int = 2000) -> tuple[str, str | None]:
    """
    Validates user input length and checks for malicious prompt injection patterns.
    Returns (sanitized_question, error_message_or_None).
    """
    if not question or not question.strip():
        return "", "Question cannot be empty."

    question = question.strip()

    if len(question) > max_length:
        logger.warning(f"Input truncated from {len(question)} chars to {max_length} chars.")
        return "", f"Question is too long. Please keep your question under {max_length} characters."

    # Check for prompt injection
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, question):
            logger.warning(f"Prompt injection pattern detected: '{pattern}' in question: '{question[:50]}...'")
            return "", "Your question contains safety-restricted keywords or prompt manipulation attempts. Please rephrase your question."

    return question, None


def sanitize_output(text: str) -> str:
    """
    Scans LLM output or error messages and redacts sensitive API keys or secrets.
    """
    if not text:
        return ""

    sanitized = text
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = re.sub(pattern, replacement, sanitized)

    return sanitized
