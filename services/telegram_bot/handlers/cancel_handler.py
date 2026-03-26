import logging

from telegram import Update
from telegram.ext import ContextTypes

from utils.firestore_client import FirestoreClient

logger = logging.getLogger(__name__)
fs_client = FirestoreClient()


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel the most recent queued job for this user."""
    user_id = str(update.effective_user.id)
    try:
        jobs = fs_client.get_jobs_by_user(user_id, limit=1, status_filter="queued")
        if not jobs:
            await update.message.reply_text(
                "No queued jobs to cancel. Use /status to see your jobs."
            )
            return

        job = jobs[0]
        job_id = job.get("jobId")
        fs_client.update_job(job_id, {"status": "cancelled"})
        logger.info("Job %s cancelled by user %s", job_id, user_id)
        await update.message.reply_text(
            f"✅ Job `{job_id[:8]}...` has been cancelled.", parse_mode="Markdown"
        )
    except Exception as exc:
        logger.exception("Cancel command failed for user %s", user_id)
        await update.message.reply_text(f"❌ Failed to cancel job: {exc}")
