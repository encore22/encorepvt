import logging

import pyotp
import requests

logger = logging.getLogger(__name__)

TWO_FA_LIVE_URL = "https://2fa.live/tok/{secret}"
REQUEST_TIMEOUT = 10


def get_totp_code(secret: str) -> str:
    """
    Get current TOTP code. Generates locally via pyotp by default.

    SECURITY NOTE: 2fa.live is a third-party service; calling it sends the
    TOTP secret externally. It is disabled by default. Set
    TOTP_USE_2FA_LIVE=1 to enable it (not recommended for production).

    Args:
        secret: Base32 TOTP secret key (e.g., JBSWY3DPEHPK3PXP)

    Returns:
        6-digit TOTP code as string
    """
    import os
    if os.environ.get("TOTP_USE_2FA_LIVE", "").lower() in ("1", "true", "yes"):
        try:
            code = _get_from_2fa_live(secret)
            if code and len(code) == 6 and code.isdigit():
                logger.info("TOTP code obtained from 2fa.live")
                return code
            logger.warning("2fa.live returned invalid code: %r, falling back to pyotp", code)
        except Exception as exc:
            logger.warning("2fa.live request failed (%s), falling back to pyotp", exc)

    return _get_from_pyotp(secret)


def _get_from_2fa_live(secret: str) -> str:
    """Query 2fa.live API for the current TOTP token."""
    url = TWO_FA_LIVE_URL.format(secret=secret.strip().upper())
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    # Response: {"token": "123456", "ttl": 25}
    token = data.get("token", "")
    return str(token).strip()


def _get_from_pyotp(secret: str) -> str:
    """Generate TOTP code locally using pyotp."""
    totp = pyotp.TOTP(secret.strip().upper())
    code = totp.now()
    logger.info("TOTP code generated locally via pyotp")
    return code
