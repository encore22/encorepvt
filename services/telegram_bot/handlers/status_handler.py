import logging

from telegram import Update
from telegram.ext import ContextTypes

from utils.firestore_client import FirestoreClient

logger = logging.getLogger(__name__)
fs_client = FirestoreClient()


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return status of the most recent job for this user."""
    user_id = str(update.effective_user.id)
    try:
        jobs = fs_client.get_jobs_by_user(user_id, limit=5)
        if not jobs:
            await update.message.reply_text(
                "No jobs found for your account. Use /start to submit one."
            )
            return

        lines = ["📋 *Your recent jobs:*\n"]
        for job in jobs:
            status = job.get("status", "unknown")
            job_id = job.get("jobId", "?")
            created = job.get("created_at")
            created_str = created.strftime("%Y-%m-%d %H:%M UTC") if created else "?"
            offer = job.get("offer_link")
            error = job.get("error")

            status_emoji = {
                "queued": "⏳",
                "processing": "🔄",
                "completed": "✅",
                "failed": "❌",
                "timeout": "⏰",
            }.get(status, "❓")

            lines.append(f"{status_emoji} `{job_id[:8]}...` — {status}")
            lines.append(f"   Created: {created_str}")
            if offer:
                lines.append(f"   🔗 Link: {offer}")
            if error:
                lines.append(f"   ⚠️ Error: {error}")
            lines.append("")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as exc:
        logger.exception("Status command failed for user %s", user_id)
        await update.message.reply_text(f"❌ Failed to retrieve status: {exc}")
