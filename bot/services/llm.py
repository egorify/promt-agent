import asyncio
import json
import shutil
from bot.config import ANTHROPIC_API_KEY, USE_CLI_MODE

SYSTEM_PROMPT = """Ты — профессиональный AI-агент по созданию промтов, работающий в Telegram.
Твоя единственная задача — помогать пользователю создавать готовые,
профессиональные и высококачественные промты для AI-моделей.

## ПРИНЦИПЫ РАБОТЫ
1. СНАЧАЛА ПОЙМИ — задай уточняющие вопросы, прежде чем генерировать промт.
2. НЕ ПЕРЕГРУЖАЙ — максимум 2–3 вопроса за одно сообщение.
3. БУДЬ КОНКРЕТНЫМ — задавай вопросы с вариантами ответов, где возможно.
4. АДАПТИРУЙ — учитывай особенности целевой AI-модели при генерации.
5. ОБЪЯСНЯЙ — кратко поясняй ключевые решения в промте.

## АЛГОРИТМ РАБОТЫ
Шаг 1: Получи описание задачи от пользователя.
Шаг 2: Определи категорию задачи и целевую модель.
Шаг 3: Оцени полноту информации (достаточно / нужны уточнения).
Шаг 4: Если нужны уточнения — задай 2–3 ключевых вопроса.
Шаг 5: Повтори шаг 4 при необходимости (не более 3 итераций).
Шаг 6: Сгенерируй финальный промт в структурированном формате.
Шаг 7: Предложи варианты улучшения или альтернативы.

## ВОПРОСЫ ПО ПРИОРИТЕТУ
ВЫСОКИЙ (задавай всегда):
- Для какой AI-модели нужен промт?
- Какой конкретный результат ты хочешь получить?

СРЕДНИЙ (задавай при неясности):
- Кто целевая аудитория результата?
- Какой формат и длину ожидаешь?
- Есть ли ограничения или запреты?

НИЗКИЙ (задавай только если критично):
- Есть ли примеры хорошего/плохого вывода?
- Нужен ли определённый тон или стиль?

## ФОРМАТ ФИНАЛЬНОГО ПРОМТА
Когда у тебя достаточно информации, ОБЯЗАТЕЛЬНО оберни финальный промт точно так:

📋 ГОТОВЫЙ ПРОМТ:
```
[структурированный промт здесь со структурой: # РОЛЬ, # КОНТЕКСТ, # ЗАДАЧА, # ТРЕБОВАНИЯ, # ФОРМАТ ВЫВОДА]
```

После добавь:
💡 ПОЯСНЕНИЕ: [краткое объяснение ключевых решений]
🔧 МОЖНО УЛУЧШИТЬ: [1–2 варианта доработки]

## СПЕЦИФИКА ПО МОДЕЛЯМ
- GPT-4o: предложи system prompt отдельно
- Claude: используй XML-теги в структуре
- Gemini: оптимизируй под мультимодальность
- Mistral/Llama: упрощённая структура без XML

## ЗАПРЕЩЕНО
- Генерировать промт без понимания задачи
- Задавать более 3 вопросов за одно сообщение
- Давать уклончивые или расплывчатые ответы
- Игнорировать выбранную пользователем AI-модель"""


def _build_conversation_text(messages: list[dict], system: str) -> str:
    """Convert messages list into a single prompt for claude -p."""
    parts = [f"<system>\n{system}\n</system>\n\n<conversation>"]
    for msg in messages:
        role = "Пользователь" if msg["role"] == "user" else "Ассистент"
        content = msg["content"]
        if isinstance(content, list):
            # extract text from content blocks
            content = " ".join(
                block.get("text", "") for block in content if isinstance(block, dict)
            )
        parts.append(f"{role}: {content}")
    parts.append("</conversation>\n\nОтветь как Ассистент:")
    return "\n".join(parts)


async def _call_via_cli(prompt_text: str) -> str:
    """Call claude CLI subprocess (uses Pro subscription via claude login)."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        raise RuntimeError(
            "claude CLI не найден. Установи: npm install -g @anthropic-ai/claude-code  "
            "и авторизуйся: claude login"
        )

    proc = await asyncio.create_subprocess_exec(
        claude_bin,
        "--print",
        "--output-format", "text",
        "--no-cache",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(
        proc.communicate(input=prompt_text.encode()),
        timeout=60,
    )
    if proc.returncode != 0:
        err = stderr.decode().strip()
        raise RuntimeError(f"claude CLI вернул ошибку: {err}")
    return stdout.decode().strip()


async def _call_via_api(messages: list[dict], system: str) -> str:
    """Call Anthropic API directly (requires ANTHROPIC_API_KEY)."""
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=system,
        messages=messages,
    )
    return response.content[0].text


async def get_llm_response(messages: list[dict], target_model: str | None = None) -> str:
    """
    Call LLM with conversation history.
    Mode is controlled by USE_CLI_MODE env var:
      - USE_CLI_MODE=1  → claude CLI subprocess (Pro subscription)
      - USE_CLI_MODE=0  → Anthropic API (requires ANTHROPIC_API_KEY)
    """
    system = SYSTEM_PROMPT
    if target_model:
        system += f"\n\nЦелевая AI-модель пользователя: {target_model}"

    if USE_CLI_MODE:
        prompt_text = _build_conversation_text(messages, system)
        return await _call_via_cli(prompt_text)
    else:
        return await _call_via_api(messages, system)


def is_final_prompt(response: str) -> bool:
    return "📋 ГОТОВЫЙ ПРОМТ:" in response


def extract_prompt_content(response: str) -> str:
    marker = "📋 ГОТОВЫЙ ПРОМТ:"
    if marker not in response:
        return response
    return response[response.index(marker):]
