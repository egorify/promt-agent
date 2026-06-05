"""
Main dialog FSM handler - processes user messages through the prompt generation flow.
"""
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot import database as db
from bot.states import get_session, reset_session, SessionState
from bot.keyboards import after_prompt_keyboard, cancel_keyboard, model_keyboard
from bot.services.llm import get_llm_response, is_final_prompt
from bot.services.prompt_builder import build_context_header
from bot.config import MAX_CLARIFY_ROUNDS, RATE_LIMIT_PER_HOUR

logger = logging.getLogger(__name__)

# In-memory rate limiting: {user_id: [timestamp, ...]}
_rate_limit_store: dict[int, list[datetime]] = defaultdict(list)


def _check_rate_limit(user_id: int) -> bool:
    """Returns True if user is within rate limit, False if exceeded."""
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=1)
    timestamps = _rate_limit_store[user_id]
    # Remove old entries
    _rate_limit_store[user_id] = [t for t in timestamps if t > cutoff]
    if len(_rate_limit_store[user_id]) >= RATE_LIMIT_PER_HOUR:
        return False
    _rate_limit_store[user_id].append(now)
    return True


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all incoming text messages based on user FSM state."""
    user = update.effective_user
    text = update.message.text.strip()

    if not text:
        return

    # Rate limiting check
    if not _check_rate_limit(user.id):
        await update.message.reply_text(
            "⚠️ Вы превысили лимит запросов (20 в час). Пожалуйста, подождите немного."
        )
        return

    # Ensure user exists in DB
    await db.upsert_user(user.id, user.username)

    session = get_session(user.id)
    state = session["state"]

    if state == SessionState.IDLE:
        # Start collecting task
        session["state"] = SessionState.COLLECTING_TASK
        await _process_task_input(update, context, user.id, text, session)

    elif state == SessionState.COLLECTING_TASK:
        await _process_task_input(update, context, user.id, text, session)

    elif state == SessionState.CLARIFYING:
        await _process_clarification(update, context, user.id, text, session)

    elif state == SessionState.REVIEW:
        # User sends a follow-up after receiving the prompt - treat as clarification request
        await _process_clarification(update, context, user.id, text, session)

    elif state == SessionState.GENERATING:
        await update.message.reply_text(
            "⏳ Подождите, идёт генерация промта..."
        )
    else:
        # Default: start new task
        session["state"] = SessionState.COLLECTING_TASK
        await _process_task_input(update, context, user.id, text, session)


async def _process_task_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    text: str,
    session: dict,
) -> None:
    """Process initial task description from user."""
    # Create a new DB session if needed
    if session["session_id"] is None:
        session_id = await db.create_session(
            user_id,
            target_model=session.get("target_model"),
            task_type=session.get("task_type"),
        )
        session["session_id"] = session_id
    else:
        session_id = session["session_id"]

    # Add context header if model/task selected
    context_header = build_context_header(
        session.get("target_model"), session.get("task_type")
    )
    user_message = context_header + text

    # Save to DB and session memory
    await db.save_message(session_id, "user", text)
    session["messages"].append({"role": "user", "content": user_message})

    await _call_llm_and_respond(update, context, user_id, session)


async def _process_clarification(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    text: str,
    session: dict,
) -> None:
    """Process user answer to clarifying questions."""
    session_id = session["session_id"]
    if session_id is None:
        # Shouldn't happen, but reset gracefully
        session["state"] = SessionState.COLLECTING_TASK
        await update.message.reply_text(
            "Что-то пошло не так. Пожалуйста, опишите задачу заново.",
            reply_markup=cancel_keyboard(),
        )
        return

    await db.save_message(session_id, "user", text)
    session["messages"].append({"role": "user", "content": text})
    session["clarify_rounds"] += 1

    await _call_llm_and_respond(update, context, user_id, session)


async def _call_llm_and_respond(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    session: dict,
) -> None:
    """Call LLM, save response, update state, and reply to user."""
    session["state"] = SessionState.GENERATING

    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    try:
        response_text = await get_llm_response(
            messages=session["messages"],
            target_model=session.get("target_model"),
        )
    except Exception as exc:
        logger.exception("LLM call failed: %s", exc)
        session["state"] = SessionState.CLARIFYING
        await update.message.reply_text(
            "❌ Произошла ошибка при обращении к AI. Пожалуйста, попробуйте ещё раз.\n\n"
            "Если ошибка повторяется, начните новую сессию командой /new",
            reply_markup=cancel_keyboard(),
        )
        return

    # Save assistant message to DB and session
    session_id = session["session_id"]
    await db.save_message(session_id, "assistant", response_text)
    session["messages"].append({"role": "assistant", "content": response_text})

    if is_final_prompt(response_text):
        # Prompt generated!
        session["state"] = SessionState.REVIEW
        session["last_prompt"] = response_text

        # Save prompt to DB
        await db.save_prompt(session_id, user_id, response_text)
        await db.update_session(session_id, status="completed")

        # Send the response with action keyboard
        await _send_long_message(
            update,
            response_text,
            reply_markup=after_prompt_keyboard(),
        )
    else:
        # Still clarifying
        if session["clarify_rounds"] >= MAX_CLARIFY_ROUNDS:
            # Force generation on next round by adding instruction
            force_msg = (
                "\n\n[Системное сообщение: у тебя достаточно информации. "
                "Немедленно сгенерируй финальный промт в требуемом формате с маркером «📋 ГОТОВЫЙ ПРОМТ:»]"
            )
            session["messages"].append({"role": "user", "content": force_msg})
            session["clarify_rounds"] = 0  # reset to allow re-entry

        session["state"] = SessionState.CLARIFYING
        await _send_long_message(update, response_text, reply_markup=cancel_keyboard())


async def _send_long_message(
    update: Update,
    text: str,
    reply_markup=None,
    chunk_size: int = 4000,
) -> None:
    """Send a potentially long message, splitting if needed."""
    if len(text) <= chunk_size:
        try:
            await update.message.reply_text(
                text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup
            )
        except Exception:
            await update.message.reply_text(text, reply_markup=reply_markup)
        return

    # Split into chunks
    chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    for i, chunk in enumerate(chunks):
        kb = reply_markup if i == len(chunks) - 1 else None
        try:
            await update.message.reply_text(
                chunk, parse_mode=ParseMode.MARKDOWN, reply_markup=kb
            )
        except Exception:
            await update.message.reply_text(chunk, reply_markup=kb)
