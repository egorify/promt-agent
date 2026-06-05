"""
Inline button callback handlers.
"""
import logging

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot import database as db
from bot.states import get_session, reset_session, SessionState
from bot.keyboards import (
    after_prompt_keyboard,
    cancel_keyboard,
    model_keyboard,
    rating_keyboard,
    start_keyboard,
    task_type_keyboard,
    MODEL_NAMES,
    TASK_NAMES,
)
from bot.services.llm import get_llm_response, is_final_prompt
from bot.services.prompt_builder import build_context_header

logger = logging.getLogger(__name__)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route all callback queries to appropriate handlers."""
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    user = update.effective_user

    if data.startswith("model:"):
        await _handle_model_selection(query, user.id, data.split(":", 1)[1])
    elif data.startswith("task:"):
        await _handle_task_selection(query, user.id, data.split(":", 1)[1])
    elif data.startswith("action:"):
        await _handle_action(query, context, user.id, data.split(":", 1)[1])
    elif data.startswith("rating:"):
        await _handle_rating(query, user.id, int(data.split(":", 1)[1]))
    elif data.startswith("lang:"):
        await _handle_language(query, user.id, data.split(":", 1)[1])
    elif data.startswith("format:"):
        await _handle_format(query, user.id, data.split(":", 1)[1])
    else:
        logger.warning("Unknown callback data: %s", data)


async def _handle_model_selection(query, user_id: int, model_key: str) -> None:
    """Handle AI model selection."""
    session = get_session(user_id)
    model_name = MODEL_NAMES.get(model_key, model_key)
    session["target_model"] = model_name

    # Update DB session if active
    if session.get("session_id"):
        await db.update_session(session["session_id"], target_model=model_name)

    text = (
        f"✅ Выбрана модель: *{model_name}*\n\n"
        "Теперь опишите задачу, для которой нужен промт, "
        "или нажмите /new для начала новой сессии."
    )
    try:
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    # If in IDLE, move to collecting
    if session["state"] == SessionState.IDLE:
        session["state"] = SessionState.COLLECTING_TASK


async def _handle_task_selection(query, user_id: int, task_key: str) -> None:
    """Handle task type selection."""
    session = get_session(user_id)
    task_name = TASK_NAMES.get(task_key, task_key)
    session["task_type"] = task_name
    session["state"] = SessionState.COLLECTING_TASK

    if session.get("session_id"):
        await db.update_session(session["session_id"], task_type=task_name)

    text = (
        f"✅ Тип задачи: *{task_name}*\n\n"
        "Теперь подробно опишите вашу задачу. Что именно вы хотите получить от AI?"
    )
    try:
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def _handle_action(query, context, user_id: int, action: str) -> None:
    """Handle action buttons after prompt generation."""
    session = get_session(user_id)

    if action == "new":
        reset_session(user_id)
        new_session = get_session(user_id)
        new_session["state"] = SessionState.COLLECTING_TASK
        text = (
            "🆕 *Новая сессия*\n\n"
            "Опишите задачу, для которой нужен промт:"
        )
        try:
            await query.edit_message_text(
                text, parse_mode=ParseMode.MARKDOWN, reply_markup=task_type_keyboard()
            )
        except Exception:
            await query.message.reply_text(
                text, parse_mode=ParseMode.MARKDOWN, reply_markup=task_type_keyboard()
            )

    elif action == "cancel":
        reset_session(user_id)
        text = "❌ Сессия отменена. Используйте /new для начала новой генерации."
        try:
            await query.edit_message_text(text)
        except Exception:
            await query.message.reply_text(text)

    elif action == "choose_model":
        text = "🤖 Выберите целевую AI-модель:"
        try:
            await query.edit_message_text(
                text, reply_markup=model_keyboard()
            )
        except Exception:
            await query.message.reply_text(text, reply_markup=model_keyboard())

    elif action == "history":
        await _show_history(query, user_id)

    elif action == "help":
        text = (
            "❓ *Помощь*\n\n"
            "1. Нажмите /new или «Начать генерацию»\n"
            "2. Опишите вашу задачу\n"
            "3. Ответьте на уточняющие вопросы\n"
            "4. Получите готовый промт!\n\n"
            "Команды: /new /model /history /settings /feedback"
        )
        try:
            await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    elif action == "improve":
        await _handle_improve(query, context, user_id, session)

    elif action == "regenerate":
        await _handle_regenerate(query, context, user_id, session)

    elif action == "save":
        await _handle_save(query, user_id, session)

    elif action == "rate":
        text = "⭐ Оцените сгенерированный промт:"
        try:
            await query.edit_message_reply_markup(reply_markup=rating_keyboard())
        except Exception:
            await query.message.reply_text(text, reply_markup=rating_keyboard())


async def _handle_improve(query, context, user_id: int, session: dict) -> None:
    """Improve the last generated prompt."""
    if not session.get("last_prompt") or not session.get("session_id"):
        await query.message.reply_text(
            "❌ Нет активного промта для улучшения. Начните новую сессию: /new"
        )
        return

    improve_msg = (
        "Пожалуйста, улучши промт: добавь больше деталей, примеров и конкретных инструкций. "
        "Сделай его более профессиональным и эффективным."
    )
    await db.save_message(session["session_id"], "user", improve_msg)
    session["messages"].append({"role": "user", "content": improve_msg})
    session["state"] = SessionState.GENERATING

    await context.bot.send_chat_action(
        chat_id=query.message.chat_id, action="typing"
    )

    try:
        response_text = await get_llm_response(
            messages=session["messages"],
            target_model=session.get("target_model"),
        )
    except Exception as exc:
        logger.exception("LLM improve failed: %s", exc)
        session["state"] = SessionState.REVIEW
        await query.message.reply_text(
            "❌ Ошибка при улучшении промта. Попробуйте ещё раз."
        )
        return

    await db.save_message(session["session_id"], "assistant", response_text)
    session["messages"].append({"role": "assistant", "content": response_text})
    session["state"] = SessionState.REVIEW

    if is_final_prompt(response_text):
        session["last_prompt"] = response_text
        await db.save_prompt(session["session_id"], user_id, response_text)

    try:
        await query.message.reply_text(
            response_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=after_prompt_keyboard(),
        )
    except Exception:
        await query.message.reply_text(
            response_text, reply_markup=after_prompt_keyboard()
        )


async def _handle_regenerate(query, context, user_id: int, session: dict) -> None:
    """Generate an alternative version of the prompt."""
    if not session.get("last_prompt") or not session.get("session_id"):
        await query.message.reply_text(
            "❌ Нет активного промта. Начните новую сессию: /new"
        )
        return

    regen_msg = (
        "Сгенерируй альтернативный вариант промта с другим подходом и структурой. "
        "Сохрани основную цель, но измени стиль и акценты."
    )
    await db.save_message(session["session_id"], "user", regen_msg)
    session["messages"].append({"role": "user", "content": regen_msg})
    session["state"] = SessionState.GENERATING

    await context.bot.send_chat_action(
        chat_id=query.message.chat_id, action="typing"
    )

    try:
        response_text = await get_llm_response(
            messages=session["messages"],
            target_model=session.get("target_model"),
        )
    except Exception as exc:
        logger.exception("LLM regenerate failed: %s", exc)
        session["state"] = SessionState.REVIEW
        await query.message.reply_text(
            "❌ Ошибка при генерации альтернативы. Попробуйте ещё раз."
        )
        return

    await db.save_message(session["session_id"], "assistant", response_text)
    session["messages"].append({"role": "assistant", "content": response_text})
    session["state"] = SessionState.REVIEW

    if is_final_prompt(response_text):
        session["last_prompt"] = response_text
        await db.save_prompt(session["session_id"], user_id, response_text)

    try:
        await query.message.reply_text(
            response_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=after_prompt_keyboard(),
        )
    except Exception:
        await query.message.reply_text(
            response_text, reply_markup=after_prompt_keyboard()
        )


async def _handle_save(query, user_id: int, session: dict) -> None:
    """Confirm prompt was saved."""
    if session.get("last_prompt") and session.get("session_id"):
        # Check if already saved
        prompts = await db.get_user_prompts(user_id, limit=1)
        if prompts:
            await query.answer("✅ Промт сохранён в историю!", show_alert=True)
        else:
            await db.save_prompt(session["session_id"], user_id, session["last_prompt"])
            await query.answer("✅ Промт сохранён!", show_alert=True)
    else:
        await query.answer("❌ Нет промта для сохранения.", show_alert=True)


async def _handle_rating(query, user_id: int, rating: int) -> None:
    """Save user rating for the last prompt."""
    updated = await db.update_prompt_rating(user_id, rating)
    stars = "⭐" * rating
    if updated:
        text = f"Спасибо за оценку {stars}! Это помогает улучшать качество."
        await query.answer(f"Оценка {stars} сохранена!", show_alert=False)
        try:
            await query.edit_message_reply_markup(reply_markup=after_prompt_keyboard())
        except Exception:
            pass
        await query.message.reply_text(text)
    else:
        await query.answer("❌ Не удалось сохранить оценку.", show_alert=True)


async def _handle_language(query, user_id: int, lang: str) -> None:
    """Update user language preference."""
    await db.update_user_language(user_id, lang)
    lang_display = "🇷🇺 Русский" if lang == "ru" else "🇬🇧 English"
    await query.answer(f"Язык изменён: {lang_display}", show_alert=False)
    try:
        await query.edit_message_text(
            f"✅ Язык изменён на *{lang_display}*",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception:
        pass


async def _handle_format(query, user_id: int, fmt: str) -> None:
    """Handle output format change."""
    fmt_display = "Markdown" if fmt == "markdown" else "Текст"
    await query.answer(f"Формат: {fmt_display}", show_alert=False)
    try:
        await query.edit_message_text(
            f"✅ Формат вывода изменён на *{fmt_display}*",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception:
        pass


async def _show_history(query, user_id: int) -> None:
    """Show last 10 prompts inline."""
    from bot.services.prompt_builder import format_prompt_for_display

    prompts = await db.get_user_prompts(user_id, limit=10)
    if not prompts:
        try:
            await query.edit_message_text(
                "📭 У вас пока нет сохранённых промтов.\n\nИспользуйте /new для создания!"
            )
        except Exception:
            await query.message.reply_text(
                "📭 У вас пока нет сохранённых промтов."
            )
        return

    await query.message.reply_text(
        f"📚 *Ваши последние промты* ({len(prompts)} шт.):",
        parse_mode=ParseMode.MARKDOWN,
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
            await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await query.message.reply_text(text)
