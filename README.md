# Telegram AI Prompt Generation Agent

A Telegram bot that helps users generate professional AI prompts for ChatGPT, Claude, Gemini, Mistral and other models by asking clarifying questions and generating structured prompts.

## Features

- Conversational prompt generation with clarifying questions (up to 3 rounds)
- Support for multiple AI models: GPT-4o, Claude 3.5, Gemini 1.5, Mistral, Llama 3
- Structured prompt output with ROLE, CONTEXT, TASK, REQUIREMENTS, OUTPUT FORMAT sections
- Model-specific optimizations (XML tags for Claude, system prompt for GPT-4o, etc.)
- Prompt history stored in SQLite (last 10 prompts per user)
- Improve and regenerate prompts via inline buttons
- Star rating system for prompts
- Rate limiting (20 requests per hour per user)
- Fully async with python-telegram-bot v20+

## Tech Stack

- Python 3.11+
- python-telegram-bot v20+ (async)
- Anthropic API (claude-sonnet-4-6)
- SQLite via aiosqlite
- In-memory FSM for session state management

## Project Structure

```
bot/
├── main.py              # Entry point
├── config.py            # Config from environment variables
├── database.py          # SQLite async DB layer
├── states.py            # FSM states and in-memory session store
├── keyboards.py         # All inline keyboards
├── handlers/
│   ├── commands.py      # /start /new /model /history /help /settings /feedback
│   ├── dialog.py        # Main dialog FSM handler
│   └── callbacks.py     # Inline button callback handlers
└── services/
    ├── llm.py           # Anthropic API integration
    └── prompt_builder.py # Prompt formatting utilities
```

## Setup

1. Clone the repository and navigate to the project directory.

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env`:
   ```
   TELEGRAM_TOKEN=your_telegram_bot_token_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   DB_PATH=data/bot.db
   ```

5. Run the bot:
   ```bash
   python -m bot.main
   ```

## Getting API Keys

- **Telegram Bot Token**: Create a bot via [@BotFather](https://t.me/BotFather) on Telegram
- **Anthropic API Key**: Sign up at [console.anthropic.com](https://console.anthropic.com)

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and quick start guide |
| `/new` | Start a new prompt generation session |
| `/model` | Choose the target AI model |
| `/history` | View your last 10 generated prompts |
| `/settings` | Language and output format settings |
| `/feedback` | Rate your last generated prompt |
| `/help` | Usage help |

## How It Works

1. User describes their task
2. The bot (powered by Claude) asks 2-3 clarifying questions
3. After receiving enough context (max 3 clarification rounds), it generates a structured prompt
4. User can improve, regenerate, save, or rate the prompt via inline buttons

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_TOKEN` | (required) | Telegram bot token |
| `ANTHROPIC_API_KEY` | (required) | Anthropic API key |
| `DB_PATH` | `data/bot.db` | SQLite database path |
| `MAX_CLARIFY_ROUNDS` | `3` | Maximum clarification rounds before forcing generation |
| `RATE_LIMIT_PER_HOUR` | `20` | Max requests per user per hour |
