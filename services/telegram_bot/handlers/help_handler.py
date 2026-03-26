"""Help handler — /help command."""
import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

_HELP_TEXT = (
    "ℹ️ *Gmail Offer Automation — Commands*\n\n"
    "*/start*\n"
    "  Begin the submission flow. The bot will ask for your Gmail address, "
    "password (encrypted & auto-deleted from chat), and 2FA key in sequence, "
    "then queue a job.\n\n"
    "*/status*\n"
    "  Check the status of your most recent jobs.\n"
    "  Possible statuses: ⏳ queued · 🔄 processing · ✅ completed · ❌ failed\n\n"
    "*/history*\n"
    "  View your last 10 job results including offer links and any error messages.\n\n"
    "*/cancel*\n"
    "  Cancel your currently queued job. In-progress jobs will be marked cancelled "
    "but may not stop immediately.\n\n"
    "*/help*\n"
    "  Show this help message.\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "💡 *Usage example:*\n"
    "1. Send /start\n"
    "2. Enter `user@gmail.com`\n"
    "3. Enter your password\n"
    "4. Enter your 2FA key (e.g. `JBSWY3DPEHPK3PXP`)\n"
    "5. Wait ~8-10 minutes, then use /status or /history to retrieve your link.\n\n"
    "🔒 Passwords are AES-256-GCM encrypted and the message is deleted immediately "
    "after receipt — plaintext credentials are never stored."
)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the help message."""
    logger.info("User %s requested help", update.effective_user.id)
    await update.message.reply_text(_HELP_TEXT, parse_mode="Markdown")
