"""Input validation helpers for the Telegram bot."""

import re

from utils.constants import MIN_PASSWORD_LENGTH

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
_EMAIL_RE = re.compile(
    r'^[a-zA-Z0-9][a-zA-Z0-9._%+\-]*'
    r'@[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?'
    r'(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*'
    r'\.[a-zA-Z]{2,63}$'
)


def is_valid_email(email: str) -> bool:
    """Return True if *email* looks like a valid e-mail address."""
    return bool(_EMAIL_RE.match(email.strip()))


# ---------------------------------------------------------------------------
# Password
# ---------------------------------------------------------------------------

def is_valid_password(password: str) -> bool:
    """Return True if *password* meets the minimum length requirement."""
    return len(password) >= MIN_PASSWORD_LENGTH


# ---------------------------------------------------------------------------
# 2FA / TOTP key
# ---------------------------------------------------------------------------
# Accepts:
#  • Standard base32 TOTP secret (letters A-Z and digits 2-7, at least 16 chars)
#  • 2fa.live style keys  e.g.  xxxxxx-xxxx-xxxx  (hex segments separated by dashes)
_BASE32_RE = re.compile(r'^[A-Z2-7]{16,}$')
_2FA_LIVE_RE = re.compile(r'^[0-9A-Fa-f]{6}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}$')


def is_valid_2fa_key(key: str) -> bool:
    """Return True if *key* looks like a valid TOTP secret or 2fa.live token."""
    normalized = key.strip().upper().replace(" ", "")
    return bool(_BASE32_RE.match(normalized) or _2FA_LIVE_RE.match(normalized))
