"""Shared constants and message templates for the Telegram bot."""

# ---------------------------------------------------------------------------
# Conversation state identifiers
# ---------------------------------------------------------------------------
WAITING_EMAIL = 1
WAITING_PASSWORD = 2
WAITING_2FA = 3
CONVERSATION_COMPLETE = 4
CANCELLED = 5

# ---------------------------------------------------------------------------
# Validation limits
# ---------------------------------------------------------------------------
MIN_PASSWORD_LENGTH = 6
MAX_HISTORY_RESULTS = 10
CONVERSATION_TIMEOUT_SECONDS = 300  # 5 minutes

# ---------------------------------------------------------------------------
# Status labels → emoji mapping
# ---------------------------------------------------------------------------
STATUS_EMOJI: dict = {
    "queued": "⏳",
    "processing": "🔄",
    "in_progress": "🔄",
    "completed": "✅",
    "failed": "❌",
    "cancelled": "🚫",
    "timeout": "⏰",
}

# ---------------------------------------------------------------------------
# User-facing messages
# ---------------------------------------------------------------------------
MSG_WELCOME = (
    "🎉 *Welcome to Gmail Offer Automation!*\n\n"
    "This bot retrieves your Google One Gemini Pro 12-month free offer link.\n\n"
    "To get started:\n"
    "1. Use /start to begin\n"
    "2. Provide your Gmail credentials (password is encrypted)\n"
    "3. Enter your 2FA key from 2fa.live\n"
    "4. Wait 8-10 minutes for results\n\n"
    "*Available commands:*\n"
    "/start — Initialize and submit Gmail account\n"
    "/status — Check your job status\n"
    "/history — View past results\n"
    "/cancel — Cancel your queued job\n"
    "/help — Show all commands"
)

MSG_ENTER_EMAIL = "📧 Please enter your Gmail address:"

MSG_EMAIL_INVALID = (
    "❌ That doesn't look like a valid email address.\n"
    "Please enter a valid Gmail address (e.g. `user@gmail.com`):"
)

MSG_EMAIL_RECEIVED = "✅ Email received: `{email}`\n\n🔒 Now enter your Gmail password (will be encrypted and deleted from chat):"

MSG_PASSWORD_TOO_SHORT = (
    "❌ Password is too short (minimum {min_len} characters). Please try again:"
)

MSG_PASSWORD_RECEIVED = (
    "✅ Password received and will be encrypted.\n\n"
    "🔑 Now enter your 2FA secret key.\n"
    "Format: TOTP base32 key (e.g. `JBSWY3DPEHPK3PXP`)\n"
    "or from 2fa.live: `xxxxxx-xxxx-xxxx`"
)

MSG_2FA_INVALID = (
    "❌ Invalid 2FA key format. Please enter a valid TOTP base32 key\n"
    "(e.g. `JBSWY3DPEHPK3PXP`) or a 2fa.live key (e.g. `xxxxxx-xxxx-xxxx`):"
)

MSG_JOB_QUEUED = (
    "✅ Credentials received and encrypted.\n\n"
    "🔄 Job queued: `{job_id_short}...`\n\n"
    "⏳ Processing begins shortly. You'll be notified when your offer link "
    "is ready (estimated 7–10 minutes).\n\n"
    "Use /status to check progress."
)

MSG_JOB_SUBMIT_FAILED = "❌ Failed to queue job: {error}\n\nPlease try /start again."

MSG_NO_JOBS = "No jobs found for your account. Use /start to submit one."

MSG_NO_QUEUED_JOBS = "No queued jobs to cancel. Use /status to see your jobs."

MSG_JOB_CANCELLED = "✅ Job `{job_id_short}...` has been cancelled."

MSG_CANCEL_IN_PROGRESS_WARNING = (
    "⚠️ Job `{job_id_short}...` is currently *in progress* on a device.\n"
    "Cancelling now may leave the device in an inconsistent state.\n"
    "Job has been marked as cancelled regardless."
)

MSG_NO_HISTORY = (
    "📭 No history found.\n\n"
    "Use /start to submit your first job."
)

MSG_HISTORY_HEADER = "📜 *Your last {count} result(s):*\n"

MSG_OPERATION_CANCELLED = "❌ Operation cancelled. Use /start to begin again."

MSG_STATUS_QUEUED = "📍 Position in queue: #{position}\n⏱️ Estimated wait: {wait} minutes"

MSG_STATUS_IN_PROGRESS = (
    "🔄 *Job in progress*\n"
    "📱 Processing your account…\n"
    "⏱️ Time elapsed: {elapsed} minutes"
)

MSG_STATUS_COMPLETED = (
    "✅ *OFFER LINK READY:*\n"
    "{offer_link}\n\n"
    "⏱️ Processing time: {elapsed}"
)

MSG_STATUS_FAILED = "❌ Error: {error}\n🔄 Retry with /start"

MSG_FIRESTORE_ERROR = "❌ Service temporarily unavailable. Please try again shortly."

MSG_GENERIC_ERROR = "❌ An unexpected error occurred: {error}"
