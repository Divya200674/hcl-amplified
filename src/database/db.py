import json
import sqlite3
from pathlib import Path

from src.models.learner import LearnerProfile, LearningGoal, SkillLevel

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "learner.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                user_id TEXT PRIMARY KEY,
                profile_json TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                status TEXT NOT NULL,
                score REAL,
                completed_at TIMESTAMP,
                UNIQUE(user_id, item_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def save_profile(profile: LearnerProfile) -> None:
    init_db()
    payload = profile.model_dump(mode="json")
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO profiles (user_id, profile_json, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                profile_json = excluded.profile_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (profile.user_id, json.dumps(payload)),
        )
        conn.commit()


def load_profile(user_id: str = "default_user") -> LearnerProfile | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT profile_json FROM profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    if not row:
        return None
    data = json.loads(row["profile_json"])
    goals = [LearningGoal(**g) for g in data.get("goals", [])]
    data["goals"] = goals
    data["skill_level"] = SkillLevel(data.get("skill_level", "beginner"))
    return LearnerProfile(**data)


def save_progress(user_id: str, item_id: str, status: str, score: float | None = None) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO progress (user_id, item_id, status, score, completed_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, item_id) DO UPDATE SET
                status = excluded.status,
                score = excluded.score,
                completed_at = CURRENT_TIMESTAMP
            """,
            (user_id, item_id, status, score),
        )
        conn.commit()


def get_progress(user_id: str) -> dict[str, dict]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT item_id, status, score FROM progress WHERE user_id = ?",
            (user_id,),
        ).fetchall()
    return {row["item_id"]: {"status": row["status"], "score": row["score"]} for row in rows}


def save_chat_message(user_id: str, role: str, content: str) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )
        conn.commit()


def get_chat_history(user_id: str, limit: int = 50) -> list[dict[str, str]]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM chat_history
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]
