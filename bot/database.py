import os
import aiosqlite
from datetime import datetime
from bot.config import DB_PATH


async def init_db() -> None:
    """Initialize database and create tables if they don't exist."""
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                username TEXT,
                language TEXT DEFAULT 'ru',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT NOT NULL,
                target_model TEXT,
                task_type TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                user_id BIGINT NOT NULL,
                content TEXT NOT NULL,
                rating INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES sessions(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        await db.commit()


async def upsert_user(user_id: int, username: str | None) -> None:
    """Insert or update user record."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (id, username) VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET username=excluded.username
        """, (user_id, username))
        await db.commit()


async def create_session(user_id: int, target_model: str | None = None, task_type: str | None = None) -> int:
    """Create a new session and return its id."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO sessions (user_id, target_model, task_type) VALUES (?, ?, ?)
        """, (user_id, target_model, task_type))
        await db.commit()
        return cursor.lastrowid


async def update_session(session_id: int, target_model: str | None = None, task_type: str | None = None, status: str | None = None) -> None:
    """Update session fields."""
    async with aiosqlite.connect(DB_PATH) as db:
        if target_model is not None:
            await db.execute("UPDATE sessions SET target_model=? WHERE id=?", (target_model, session_id))
        if task_type is not None:
            await db.execute("UPDATE sessions SET task_type=? WHERE id=?", (task_type, session_id))
        if status is not None:
            await db.execute("UPDATE sessions SET status=? WHERE id=?", (status, session_id))
        await db.commit()


async def save_message(session_id: int, role: str, content: str) -> None:
    """Save a message to the messages table."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)
        """, (session_id, role, content))
        await db.commit()


async def save_prompt(session_id: int, user_id: int, content: str) -> int:
    """Save generated prompt, return its id."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO prompts (session_id, user_id, content) VALUES (?, ?, ?)
        """, (session_id, user_id, content))
        await db.commit()
        return cursor.lastrowid


async def update_prompt_rating(user_id: int, rating: int) -> bool:
    """Update rating of the most recent prompt for user. Returns True if updated."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT id FROM prompts WHERE user_id=? ORDER BY created_at DESC LIMIT 1
        """, (user_id,))
        row = await cursor.fetchone()
        if not row:
            return False
        await db.execute("UPDATE prompts SET rating=? WHERE id=?", (rating, row[0]))
        await db.commit()
        return True


async def get_user_prompts(user_id: int, limit: int = 10) -> list[dict]:
    """Fetch last N prompts for user."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT p.id, p.content, p.rating, p.created_at, s.target_model, s.task_type
            FROM prompts p
            JOIN sessions s ON p.session_id = s.id
            WHERE p.user_id=?
            ORDER BY p.created_at DESC
            LIMIT ?
        """, (user_id, limit))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_user_language(user_id: int) -> str:
    """Get user language preference."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT language FROM users WHERE id=?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else "ru"


async def update_user_language(user_id: int, language: str) -> None:
    """Update user language preference."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET language=? WHERE id=?", (language, user_id))
        await db.commit()
