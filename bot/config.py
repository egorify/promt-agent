import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DB_PATH = os.getenv("DB_PATH", "data/bot.db")
MAX_CLARIFY_ROUNDS = 3
RATE_LIMIT_PER_HOUR = 20
