import logging
import os

import requests

logger = logging.getLogger(__name__)


def send_telegram_notification(user_id: str, message: str) -> bool:
    """Send a Telegram message to a user via the Bot API."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not set; cannot send notification")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": user_id,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.error("Failed to send Telegram notification to %s: %s", user_id, exc)
        return False
