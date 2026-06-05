"""
Handlers for bot commands: /start /new /model /history /help /settings /feedback
"""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot import database as db
from bot.states import get_session, reset_session, SessionState
from bot.keyboards import (
    start_keyboard, model_keyboard, task_type_keyboard,
    settings_keyboard, after_prompt_keyboard
)
from bot.services.prompt_builder import format_prompt_for_display


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    await db.upsert_user(user.id, user.username)
    session = reset_session(user.id)

    text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "Я — *AI Prompt Generator*, твой помощник в создании профессиональных промтов "
        "для ChatGPT, Claude, Gemini, Mistral и других AI-моделей.\n\n"
        "🎯 *Что я умею:*\n"
        "• Задавать уточняющие вопросы для понимания твоей задачи\n"
        "• Генерировать структурированные промты под конкретную модель\n"
        "• Улучшать и адаптировать промты\n"
        "• Сохранять историю твоих промтов\n\n"
        "🚀 *Как начать:*\n"
        "Просто нажми кнопку *«Начать генерацию»* или опиши свою задачу текстом.\n\n"
        "Команды:\n"
        "/new — новая сессия генерации\n"
        "/model — выбрать целевую AI-модель\n"
        "/history — последние 10 промтов\n"
        "/settings — настройки\n"
        "/help — помощь"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=start_keyboard())


async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /new command - start a new prompt generation session."""
    user = update.effective_user
    await db.upsert_user(user.id, user.username)
    session = reset_session(user.id)
    session["state"] = SessionState.COLLECTING_TASK

    text = (
        "🆕 *Новая сессия генерации*\n\n"
        "Опишите задачу, для которой нужен промт. Чем подробнее — тем лучше!\n\n"
        "Например:\n"
        "_«Хочу промт для написания продающих постов в Instagram для фитнес-клуба»_\n"
        "_«Нужен промт для анализа финансовых отчётов и выявления аномалий»_\n\n"
        "Или сначала выберите тип задачи:"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=task_type_keyboard())


async def cmd_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /model command - show model selection keyboard."""
    text = (
        "🤖 *Выбор целевой AI-модели*\n\n"
        "Для какой модели будем генерировать промт?\n"
        "Это поможет мне адаптировать структуру и формат."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=model_keyboard())


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /history command - show last 10 prompts."""
    user = update.effective_user
    prompts = await db.get_user_prompts(user.id, limit=10)

    if not prompts:
        await update.message.reply_text(
            "📭 У вас пока нет сохранённых промтов.\n\n"
            "Используйте /new чтобы создать первый!",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    await update.message.reply_text(
        f"📚 *Ваши последние промты* ({len(prompts)} шт.):\n",
        parse_mode=ParseMode.MARKDOWN
    )

    for i, prompt in enumerate(prompts, 1):
        text = format_prompt_for_display(
            content=prompt["content"],
            index=i,
            created_at=prompt["created_at"],
            target_model=prompt["target_model"],
            rating=prompt["rating"],
        )
        try:
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            # Fall back to plain text if markdown fails
            await update.message.reply_text(text)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    text = (
        "❓ *Помощь по боту*\n\n"
        "*Основные команды:*\n"
        "/start — приветствие и быстрый старт\n"
        "/new — начать новую сессию генерации промта\n"
        "/model — выбрать целевую AI-модель\n"
        "/history — просмотр последних 10 промтов\n"
        "/settings — настройки языка и формата\n"
        "/feedback — оставить отзыв\n"
        "/help — эта справка\n\n"
        "*Как работает генерация:*\n"
        "1. Опишите задачу текстом\n"
        "2. Я задам 2–3 уточняющих вопроса\n"
        "3. Получите готовый структурированный промт\n"
        "4. Улучшайте или сохраняйте результат\n\n"
        "*Советы:*\n"
        "• Чем детальнее описание — тем лучше результат\n"
        "• Укажите целевую модель через /model заранее\n"
        "• После получения промта можно попросить улучшить его\n\n"
        "*Поддерживаемые модели:* GPT-4o, Claude 3.5, Gemini 1.5, Mistral, Llama 3"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /settings command."""
    user = update.effective_user
    lang = await db.get_user_language(user.id)
    lang_display = "🇷🇺 Русский" if lang == "ru" else "🇬🇧 English"

    text = (
        f"⚙️ *Настройки*\n\n"
        f"Текущий язык: {lang_display}\n"
        f"Формат вывода: Markdown\n\n"
        "Выберите параметр для изменения:"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=settings_keyboard())


async def cmd_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /feedback command."""
    user = update.effective_user
    session = get_session(user.id)

    if not session.get("last_prompt"):
        await update.message.reply_text(
            "📝 *Отзыв*\n\n"
            "Сначала создайте промт, а затем оставьте оценку.\n"
            "Используйте /new для начала.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    text = (
        "⭐ *Оцените последний промт*\n\n"
        "Насколько полезным оказался сгенерированный промт?\n"
        "Ваша оценка помогает нам улучшать качество!"
    )
    from bot.keyboards import rating_keyboard
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=rating_keyboard())
