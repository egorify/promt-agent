"""
Utility functions for building and formatting prompts.
"""
from datetime import datetime


def format_prompt_for_display(content: str, index: int | None = None, created_at: str | None = None, target_model: str | None = None, rating: int | None = None) -> str:
    """Format a saved prompt entry for display in history."""
    lines = []
    if index is not None:
        lines.append(f"*{index}.*")
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at)
            lines.append(f"📅 {dt.strftime('%d.%m.%Y %H:%M')}")
        except ValueError:
            lines.append(f"📅 {created_at}")
    if target_model:
        lines.append(f"🤖 Модель: {target_model}")
    if rating:
        stars = "⭐" * rating
        lines.append(f"Оценка: {stars}")
    lines.append("")

    # Truncate very long prompts for history display
    preview = content
    if len(content) > 500:
        preview = content[:500] + "...\n_(показан фрагмент)_"
    lines.append(preview)
    return "\n".join(lines)


def build_context_header(target_model: str | None, task_type: str | None) -> str:
    """Build a context header string for injecting into LLM message."""
    parts = []
    if target_model:
        parts.append(f"Целевая модель: {target_model}")
    if task_type:
        parts.append(f"Тип задачи: {task_type}")
    if parts:
        return "[Контекст сессии: " + ", ".join(parts) + "]\n\n"
    return ""
