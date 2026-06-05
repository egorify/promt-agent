# Telegram AI Prompt Generation Agent

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-v20+-green.svg)](https://github.com/python-telegram-bot/python-telegram-bot)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Telegram bot that helps users generate professional AI prompts for ChatGPT, Claude, Gemini, Mistral and other models through an interactive conversational flow.

## Why This Project Exists

Most people don't get great results from AI models — not because the models are bad, but because writing effective prompts is a skill. **promt-agent** bridges that gap: it interviews you about your task, asks smart clarifying questions, and produces a structured, model-optimized prompt ready to paste into any AI chat.

No more staring at a blank text box wondering how to phrase your request.

## Features

- **Conversational prompt generation** — asks clarifying questions (up to 3 rounds) before generating
- **Multi-model support** — GPT-4o, Claude 3.5, Gemini 1.5, Mistral, Llama 3
- **Model-specific optimizations** — XML tags for Claude, system prompt formatting for GPT-4o, etc.
- **Structured output** — every prompt includes ROLE, CONTEXT, TASK, REQUIREMENTS, OUTPUT FORMAT sections
- **Prompt history** — SQLite storage, last 10 prompts per user
- **Improve & regenerate** — inline buttons to refine, regenerate, or rate prompts
- **Star rating system** — rate generated prompts for quality tracking
- **Rate limiting** — 20 requests per hour per user (configurable)
- **Fully async** — built on python-telegram-bot v20+ with aiosqlite

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Telegram | python-telegram-bot v20+ (async) |
| LLM | Anthropic Claude API |
| Database | SQLite via aiosqlite |
| State | In-memory FSM for session management |

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/egorify/promt-agent.git
cd promt-agent
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your tokens
```

Required environment variables:
- `TELEGRAM_TOKEN` — get from [@BotFather](https://t.me/BotFather)
- `ANTHROPIC_API_KEY` — get from [console.anthropic.com](https://console.anthropic.com)

### 3. Run

```bash
python -m bot.main
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and quick start |
| `/new` | Start a new prompt generation session |
| `/model` | Choose the target AI model |
| `/history` | View your last 10 generated prompts |
| `/settings` | Language and output format settings |
| `/feedback` | Rate your last generated prompt |
| `/help` | Usage help |

## How It Works

```
User: "I need a prompt for writing marketing copy"
Bot:  "What's the target audience?"
User: "Small business owners, 30-50 years old"
Bot:  "What tone do you want — professional, casual, or persuasive?"
User: "Professional but friendly"
Bot:  "Any specific product or service?"
User: "Accounting software"
---
Bot generates:
  ROLE: You are an experienced B2B marketing copywriter...
  CONTEXT: Targeting small business owners aged 30-50...
  TASK: Write marketing copy for accounting software...
  REQUIREMENTS: Professional but friendly tone, focus on time-saving...
  OUTPUT FORMAT: 3 variations: email subject line, landing page hero, ad copy
```

## Project Structure

```
promt-agent/
├── bot/
│   ├── main.py              # Entry point
│   ├── config.py            # Config from environment variables
│   ├── database.py          # SQLite async DB layer
│   ├── states.py            # FSM states and in-memory session store
│   ├── keyboards.py         # All inline keyboards
│   ├── handlers/
│   │   ├── commands.py      # /start /new /model /history /help /settings /feedback
│   │   ├── dialog.py        # Main dialog FSM handler
│   │   └── callbacks.py     # Inline button callback handlers
│   └── services/
│       ├── llm.py           # Anthropic API integration
│       └── prompt_builder.py # Prompt formatting utilities
├── .env.example             # Example environment file
├── requirements.txt         # Python dependencies
├── LICENSE                  # MIT License
└── README.md                # This file
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_TOKEN` | *(required)* | Telegram bot token |
| `ANTHROPIC_API_KEY` | *(required)* | Anthropic API key |
| `DB_PATH` | `data/bot.db` | SQLite database path |
| `MAX_CLARIFY_ROUNDS` | `3` | Maximum clarification rounds |
| `RATE_LIMIT_PER_HOUR` | `20` | Max requests per user per hour |

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
