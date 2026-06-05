"""
Entry point for the Telegram AI Prompt Generation Bot.
"""
import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# Load environment variables from .env file before importing config
load_dotenv()

from bot.config import TELEGRAM_TOKEN, ALLOWED_USER_IDS
from bot.database import init_db
from bot.handlers.commands import (
    cmd_start,
    cmd_new,
    cmd_model,
    cmd_history,
    cmd_help,
    cmd_settings,
    cmd_feedback,
)
from bot.handlers.dialog import handle_message
from bot.handlers.callbacks import handle_callback

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """Initialise the database after application starts."""
    await init_db()
    logger.info("Database initialised successfully.")


def main() -> None:
    if not TELEGRAM_TOKEN:
        raise ValueError(
            "TELEGRAM_TOKEN is not set. Please configure it in .env or environment variables."
        )

    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .build()
    )

    user_filter = filters.User(user_id=list(ALLOWED_USER_IDS)) if ALLOWED_USER_IDS else filters.ALL

    # Command handlers
    application.add_handler(CommandHandler("start", cmd_start, filters=user_filter))
    application.add_handler(CommandHandler("new", cmd_new, filters=user_filter))
    application.add_handler(CommandHandler("model", cmd_model, filters=user_filter))
    application.add_handler(CommandHandler("history", cmd_history, filters=user_filter))
    application.add_handler(CommandHandler("help", cmd_help, filters=user_filter))
    application.add_handler(CommandHandler("settings", cmd_settings, filters=user_filter))
    application.add_handler(CommandHandler("feedback", cmd_feedback, filters=user_filter))

    # Inline keyboard callback handler
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Text message handler (must be last)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND & user_filter, handle_message)
    )

    logger.info("Bot starting...")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
