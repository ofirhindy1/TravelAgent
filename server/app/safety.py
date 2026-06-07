"""
Safety constants and input-validation utilities.

All user-facing error strings live here so they can be reused across
agent.py and main.py without circular imports.
"""
import re

# ── Hard limits ────────────────────────────────────────────────────────────────
RECURSION_LIMIT    = 10          # max LangGraph steps per request
TOOL_TIMEOUT_SECS  = 5.0         # seconds before a tool call is forcibly aborted
TOKEN_BUDGET       = 50_000      # cumulative tokens allowed per thread (soft cap)
MAX_INPUT_LENGTH   = 2_000       # characters

# ── User-facing messages ───────────────────────────────────────────────────────
MSG_RECURSION = (
    "I'm sorry, I encountered a technical issue while processing your request. "
    "Please contact the developer for assistance."
)
MSG_BUDGET_EXCEEDED = (
    "You've reached the session limit for this conversation. "
    "Please start a new chat."
)
MSG_TOOL_TIMEOUT = (
    "The search is taking longer than expected. "
    "Please try again or refine your request."
)
MSG_INVALID_INPUT = (
    "Your message contains patterns that cannot be processed. "
    "Please ask a straightforward travel question."
)
MSG_INPUT_TOO_LONG = (
    f"Your message is too long (max {MAX_INPUT_LENGTH} characters). "
    "Please shorten it and try again."
)
MSG_CANCELLED = (
    "Your request was cancelled."
)

# ── Injection / abuse patterns ─────────────────────────────────────────────────
_INJECTION_RE = re.compile(
    r"ignore\s+(all\s+)?previous\s+instructions?"
    r"|you\s+are\s+now\s+"
    r"|forget\s+(everything|your\s+instructions?)"
    r"|new\s+instructions?:"
    r"|system\s+prompt"
    r"|<\s*script"           # XSS attempt
    r"|exec\s*\("            # code execution
    r"|eval\s*\("
    r"|__import__"
    r"|subprocess\s*\."
    r"|;\s*(?:DROP|INSERT|UPDATE|DELETE|SELECT)\s+"   # SQL injection
    r"|UNION\s+SELECT",
    re.IGNORECASE,
)


def validate_user_input(text: str) -> str | None:
    """
    Return None if the input looks safe.
    Return a user-facing error string if the input is suspicious or too long.
    """
    if len(text) > MAX_INPUT_LENGTH:
        return MSG_INPUT_TOO_LONG
    if _INJECTION_RE.search(text):
        return MSG_INVALID_INPUT
    return None
