"""History handler — /history command."""
import logging

from telegram import Update
from telegram.ext import ContextTypes

from utils.constants import MAX_HISTORY_RESULTS, MSG_NO_HISTORY, MSG_HISTORY_HEADER, STATUS_EMOJI
from utils.firestore_client import FirestoreClient

logger = logging.getLogger(__name__)
fs_client = FirestoreClient()


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the last MAX_HISTORY_RESULTS completed jobs for this user."""
    user_id = str(update.effective_user.id)
    logger.info("User %s requested history", user_id)

    try:
        jobs = fs_client.get_jobs_by_user(user_id, limit=MAX_HISTORY_RESULTS)
    except Exception as exc:
        logger.exception("History query failed for user %s", user_id)
        await update.message.reply_text(f"❌ Failed to retrieve history: {exc}")
        return

    if not jobs:
        await update.message.reply_text(MSG_NO_HISTORY)
        return

    lines = [MSG_HISTORY_HEADER.format(count=len(jobs))]

    for i, job in enumerate(jobs, start=1):
        status = job.get("status", "unknown")
        job_id = job.get("jobId", "?")
        created = job.get("created_at")
        if created:
            # Firestore returns timezone-aware datetimes; handle naive datetimes defensively
            from datetime import timezone as _tz
            if created.tzinfo is None:
                created = created.replace(tzinfo=_tz.utc)
            created_str = created.strftime("%Y-%m-%d %H:%M UTC")
        else:
            created_str = "?"
        offer = job.get("offer_link")
        error = job.get("error")
        emoji = STATUS_EMOJI.get(status, "❓")

        lines.append(f"{i}. {emoji} `{job_id[:8]}...` — *{status}*")
        lines.append(f"   🕐 {created_str}")
        if offer:
            lines.append(f"   🔗 {offer}")
        if error:
            lines.append(f"   ⚠️ {error}")
        lines.append("")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
