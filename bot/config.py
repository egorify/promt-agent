import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DB_PATH = os.getenv("DB_PATH", "data/bot.db")
MAX_CLARIFY_ROUNDS = 3
RATE_LIMIT_PER_HOUR = 20

# USE_CLI_MODE=1 — использовать claude CLI (Pro подписка через claude login)
# USE_CLI_MODE=0 — использовать Anthropic API (требует ANTHROPIC_API_KEY)
USE_CLI_MODE = os.getenv("USE_CLI_MODE", "0") == "1"
