from enum import Enum, auto


class SessionState(Enum):
    IDLE = auto()
    COLLECTING_TASK = auto()
    CLARIFYING = auto()
    GENERATING = auto()
    REVIEW = auto()


# In-memory session storage keyed by telegram user_id
# Each session is a dict with keys:
#   state: SessionState
#   session_id: int | None
#   target_model: str | None
#   task_type: str | None
#   messages: list[dict]  # [{role, content}] for LLM
#   clarify_rounds: int
#   last_prompt: str | None
user_sessions: dict[int, dict] = {}


def get_session(user_id: int) -> dict:
    """Get or create a session for user."""
    if user_id not in user_sessions:
        user_sessions[user_id] = _default_session()
    return user_sessions[user_id]


def reset_session(user_id: int) -> dict:
    """Reset session to default state."""
    user_sessions[user_id] = _default_session()
    return user_sessions[user_id]


def _default_session() -> dict:
    return {
        "state": SessionState.IDLE,
        "session_id": None,
        "target_model": None,
        "task_type": None,
        "messages": [],
        "clarify_rounds": 0,
        "last_prompt": None,
    }
