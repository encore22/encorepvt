import logging
import os
import re
import uuid
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from utils.encryption import encrypt_value
from utils.firestore_client import FirestoreClient

logger = logging.getLogger(__name__)

WAITING_EMAIL = 1
WAITING_PASSWORD = 2
WAITING_2FA = 3

fs_client = FirestoreClient()


_EMAIL_RE = re.compile(
    r'^[a-zA-Z0-9][a-zA-Z0-9._%+\-]*@[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?'
    r'(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,63}$'
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point: greet user and ask for email."""
    user = update.effective_user
    logger.info("User %s started conversation", user.id)
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Welcome to the Gmail Automation System!\n\n"
        "I will retrieve your Google One Gemini Pro offer link.\n\n"
        "Please send your Gmail address:"
    )
    return WAITING_EMAIL


async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validate and store email, ask for password."""
    email = update.message.text.strip()
    if not _EMAIL_RE.match(email):
        await update.message.reply_text(
            "❌ That doesn't look like a valid email address. Please try again:"
        )
        return WAITING_EMAIL

    context.user_data["email"] = email
    logger.info("Received email for user %s", update.effective_user.id)
    await update.message.reply_text(
        f"✅ Email received: `{email}`\n\nNow send your Gmail password:",
        parse_mode="Markdown",
    )
    return WAITING_PASSWORD


async def receive_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store password (will be encrypted), ask for 2FA key."""
    password = update.message.text.strip()
    if len(password) < 6:
        await update.message.reply_text(
            "❌ Password seems too short. Please try again:"
        )
        return WAITING_PASSWORD

    context.user_data["password"] = password
    # Attempt to delete the message containing the password for security
    try:
        await update.message.delete()
    except Exception:
        pass

    await update.message.reply_text(
        "✅ Password received.\n\n"
        "Now send your 2FA secret key (TOTP base32 key, e.g., `JBSWY3DPEHPK3PXP`):",
        parse_mode="Markdown",
    )
    return WAITING_2FA


async def receive_2fa_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Encrypt all credentials and submit job to Firestore queue."""
    two_fa_key = update.message.text.strip().upper().replace(" ", "")
    context.user_data["two_fa_key"] = two_fa_key

    try:
        await update.message.delete()
    except Exception:
        pass

    email = context.user_data["email"]
    password = context.user_data["password"]
    user_id = str(update.effective_user.id)
    job_id = str(uuid.uuid4())

    try:
        email_enc = encrypt_value(email)
        password_enc = encrypt_value(password)
        two_fa_enc = encrypt_value(two_fa_key)

        job_data = {
            "jobId": job_id,
            "user_id": user_id,
            "email_encrypted": email_enc,
            "password_encrypted": password_enc,
            "two_fa_encrypted": two_fa_enc,
            "status": "queued",
            "retry_count": 0,
            "created_at": datetime.now(timezone.utc),
            "completed_at": None,
            "device_id": None,
            "offer_link": None,
            "error": None,
        }

        fs_client.create_job(job_id, job_data)
        logger.info("Job %s created for user %s", job_id, user_id)

        await update.message.reply_text(
            f"✅ Credentials received and encrypted.\n\n"
            f"🔄 Job queued: `{job_id[:8]}...`\n\n"
            f"⏳ Processing will begin shortly. You will be notified when your "
            f"offer link is ready (estimated 7-10 minutes).\n\n"
            f"Use /status to check progress.",
            parse_mode="Markdown",
        )
    except Exception as exc:
        logger.exception("Failed to create job for user %s", user_id)
        await update.message.reply_text(
            f"❌ Failed to queue job: {exc}\n\nPlease try /start again."
        )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel_conversation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Cancel the conversation."""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Operation cancelled. Use /start to begin again."
    )
    return ConversationHandler.END
