from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def model_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting target AI model."""
    buttons = [
        [
            InlineKeyboardButton("GPT-4o", callback_data="model:gpt4o"),
            InlineKeyboardButton("Claude 3.5", callback_data="model:claude35"),
        ],
        [
            InlineKeyboardButton("Gemini 1.5", callback_data="model:gemini15"),
            InlineKeyboardButton("Mistral", callback_data="model:mistral"),
        ],
        [
            InlineKeyboardButton("Llama 3", callback_data="model:llama3"),
            InlineKeyboardButton("Другая", callback_data="model:other"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def task_type_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting task type."""
    buttons = [
        [
            InlineKeyboardButton("✍️ Написание текста", callback_data="task:writing"),
            InlineKeyboardButton("📊 Анализ данных", callback_data="task:analysis"),
        ],
        [
            InlineKeyboardButton("💻 Код", callback_data="task:code"),
            InlineKeyboardButton("🖼️ Изображения", callback_data="task:images"),
        ],
        [
            InlineKeyboardButton("🔧 Другое", callback_data="task:other"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def after_prompt_keyboard() -> InlineKeyboardMarkup:
    """Action buttons shown after prompt generation."""
    buttons = [
        [
            InlineKeyboardButton("✏️ Улучшить", callback_data="action:improve"),
            InlineKeyboardButton("🔄 Новый вариант", callback_data="action:regenerate"),
        ],
        [
            InlineKeyboardButton("💾 Сохранить", callback_data="action:save"),
            InlineKeyboardButton("⭐ Оценить", callback_data="action:rate"),
        ],
        [
            InlineKeyboardButton("🆕 Новая задача", callback_data="action:new"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def rating_keyboard() -> InlineKeyboardMarkup:
    """Star rating keyboard."""
    buttons = [
        [
            InlineKeyboardButton("⭐", callback_data="rating:1"),
            InlineKeyboardButton("⭐⭐", callback_data="rating:2"),
            InlineKeyboardButton("⭐⭐⭐", callback_data="rating:3"),
            InlineKeyboardButton("⭐⭐⭐⭐", callback_data="rating:4"),
            InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="rating:5"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def start_keyboard() -> InlineKeyboardMarkup:
    """Quick start keyboard for /start command."""
    buttons = [
        [
            InlineKeyboardButton("🚀 Начать генерацию", callback_data="action:new"),
            InlineKeyboardButton("🤖 Выбрать модель", callback_data="action:choose_model"),
        ],
        [
            InlineKeyboardButton("📚 История", callback_data="action:history"),
            InlineKeyboardButton("❓ Помощь", callback_data="action:help"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def settings_keyboard() -> InlineKeyboardMarkup:
    """Settings keyboard."""
    buttons = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
        ],
        [
            InlineKeyboardButton("📄 Формат: Markdown", callback_data="format:markdown"),
            InlineKeyboardButton("📝 Формат: Текст", callback_data="format:text"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def cancel_keyboard() -> InlineKeyboardMarkup:
    """Simple cancel keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Отмена", callback_data="action:cancel")]
    ])


MODEL_NAMES = {
    "gpt4o": "GPT-4o",
    "claude35": "Claude 3.5 Sonnet",
    "gemini15": "Gemini 1.5 Pro",
    "mistral": "Mistral Large",
    "llama3": "Llama 3",
    "other": "Другая модель",
}

TASK_NAMES = {
    "writing": "Написание текста",
    "analysis": "Анализ данных",
    "code": "Код",
    "images": "Изображения",
    "other": "Другое",
}
