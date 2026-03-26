import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)

from handlers.start_handler import (
    start,
    receive_email,
    receive_password,
    receive_2fa_key,
    cancel_conversation,
    WAITING_EMAIL,
    WAITING_PASSWORD,
    WAITING_2FA,
)
from handlers.status_handler import status_command
from handlers.cancel_handler import cancel_command

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)
            ],
            WAITING_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password)
            ],
            WAITING_2FA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_2fa_key)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("cancel", cancel_command))

    logger.info("Telegram bot starting...")
    application.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
