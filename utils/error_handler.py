"""
error_handler.py — Centralized Error Handling
================================================
This module defines custom exceptions and error handling utilities.

KEY CONCEPTS:
─────────────
1. CUSTOM EXCEPTIONS:
   Python lets you create your own exception types by extending
   the built-in Exception class. This makes error handling more
   specific and informative.

   Instead of:
       raise Exception("Something went wrong")  # ❌ Vague

   You can do:
       raise SearchError("Wikipedia API returned 404")  # ✅ Specific

   This lets callers catch specific error types:
       try:
           searcher.search(query)
       except SearchError:
           # Handle search failures specifically
       except LLMError:
           # Handle LLM failures differently

2. GRACEFUL DEGRADATION:
   When part of the system fails, the rest should keep working.
   Example: If Wikipedia is down but DuckDuckGo works, we should
   still produce a report using only the DuckDuckGo results.

3. INPUT VALIDATION:
   Always validate user input BEFORE processing it. This prevents:
   - Wasted API calls on empty queries
   - Security issues from malicious input
   - Confusing error messages from deeper in the code
"""


class ResearchAssistantError(Exception):
    """
    Base exception for all AI Research Assistant errors.

    All custom exceptions inherit from this class.
    This lets you catch ALL app-specific errors with one except:
        try:
            ...
        except ResearchAssistantError as e:
            # Catches SearchError, LLMError, etc.
    """
    pass


class SearchError(ResearchAssistantError):
    """
    Raised when a search operation fails.

    Examples:
    - Network timeout when calling Wikipedia API
    - DuckDuckGo rate limit exceeded
    - Search returned no results
    """
    pass


class LLMError(ResearchAssistantError):
    """
    Raised when the LLM (Gemini) operation fails.

    Examples:
    - Invalid API key
    - Rate limit exceeded
    - Model returned unparseable response
    """
    pass


class ValidationError(ResearchAssistantError):
    """
    Raised when user input fails validation.

    Examples:
    - Empty question
    - Question too long
    - Invalid characters
    """
    pass


class ConfigError(ResearchAssistantError):
    """
    Raised when there's a configuration problem.

    Examples:
    - Missing API key
    - Invalid environment variable value
    """
    pass


def validate_question(question: str) -> str:
    """
    Validate and clean the user's research question.

    This function runs BEFORE any API calls are made. It checks
    for common problems and raises clear error messages.

    Validation rules:
    1. Must not be empty or whitespace-only
    2. Must be at least 3 characters (a meaningful question)
    3. Must not exceed 500 characters (API limits)

    Args:
        question: The raw question from the user

    Returns:
        The cleaned (stripped) question string

    Raises:
        ValidationError: If the question fails any validation check
    """
    # ── Strip whitespace ───────────────────────────────────────────
    # .strip() removes leading/trailing spaces, tabs, newlines
    cleaned = question.strip()

    # ── Check: Not empty ───────────────────────────────────────────
    if not cleaned:
        raise ValidationError(
            "Question cannot be empty. "
            "Please provide a research question."
        )

    # ── Check: Minimum length ──────────────────────────────────────
    if len(cleaned) < 3:
        raise ValidationError(
            f"Question is too short ({len(cleaned)} chars). "
            "Please provide a more detailed research question."
        )

    # ── Check: Maximum length ──────────────────────────────────────
    if len(cleaned) > 500:
        raise ValidationError(
            f"Question is too long ({len(cleaned)} chars, max 500). "
            "Please shorten your question."
        )

    return cleaned


def handle_search_errors(source_name: str, error: Exception) -> None:
    """
    Handle and log search errors in a consistent way.

    Instead of each searcher having its own error handling logic,
    this function provides a standard way to handle search failures.

    Args:
        source_name: Name of the search source (e.g., "Wikipedia")
        error: The exception that occurred
    """
    error_messages = {
        "ConnectionError": f"Could not connect to {source_name}. Check your internet connection.",
        "TimeoutError": f"{source_name} took too long to respond. Try again later.",
        "HTTPError": f"{source_name} returned an error. The service may be down.",
    }

    error_type = type(error).__name__
    message = error_messages.get(
        error_type,
        f"Unexpected error from {source_name}: {str(error)}"
    )

    print(f"  ⚠ {message}")
