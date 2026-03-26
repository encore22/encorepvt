import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request, Response, status
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from handlers.cancel_handler import cancel_command
from handlers.help_handler import help_command
from handlers.history_handler import history_command
from handlers.start_handler import (
    WAITING_2FA,
    WAITING_EMAIL,
    WAITING_PASSWORD,
    cancel_conversation,
    receive_2fa_key,
    receive_email,
    receive_password,
    start,
)
from handlers.status_handler import status_command

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Build the telegram Application once at module level so it is shared across
# all requests (avoids re-creating the client on every webhook hit).
# ---------------------------------------------------------------------------

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

_telegram_app: Application = Application.builder().token(TOKEN).build()

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

_telegram_app.add_handler(conv_handler)
_telegram_app.add_handler(CommandHandler("status", status_command))
_telegram_app.add_handler(CommandHandler("cancel", cancel_command))
_telegram_app.add_handler(CommandHandler("history", history_command))
_telegram_app.add_handler(CommandHandler("help", help_command))

# ---------------------------------------------------------------------------
# FastAPI lifespan – manages startup / shutdown of the telegram Application
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    await _telegram_app.initialize()
    logger.info("Telegram Application initialised")
    yield
    await _telegram_app.shutdown()
    logger.info("Telegram Application shut down")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(title="Telegram Bot Webhook", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    """Health-check endpoint required by Cloud Run."""
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(request: Request) -> Response:
    """Receive an update from Telegram and process it."""
    try:
        data = await request.json()
        update = Update.de_json(data, _telegram_app.bot)
        if update is None:
            logger.warning("Received empty or unrecognised update payload")
            return Response(status_code=status.HTTP_200_OK)
        await _telegram_app.process_update(update)
    except Exception:
        logger.exception("Failed to process Telegram update")
        return Response(status_code=status.HTTP_200_OK)
    return Response(status_code=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Entry point (used when running directly: python app.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app:app", host="0.0.0.0", port=port, workers=1)
