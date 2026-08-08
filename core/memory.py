"""SQLite-backed memory for conversation history, user profile, notes, and tasks.

A single ``SQLiteMemory`` instance (``memory``) is shared across the app.
All CRUD for notes and tasks goes through the same SQLite file so foreign-key
consistency is trivial.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any

from core.config import settings


class SQLiteMemory:
    """Manages all persistent storage: conversations, profile, notes, tasks."""

    def __init__(self, db_path: str = settings.SQLITE_PATH) -> None:
        self.db_path = db_path
        self._init_db()

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        """Return a connection with Row factory enabled."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        """Create all tables if they do not exist."""
        with self._get_conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id          TEXT PRIMARY KEY,
                    user_id     TEXT NOT NULL,
                    role        TEXT NOT NULL,
                    content     TEXT NOT NULL,
                    session_id  TEXT NOT NULL,
                    created_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS user_profile (
                    user_id     TEXT PRIMARY KEY,
                    profile_json TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS notes (
                    id          TEXT PRIMARY KEY,
                    user_id     TEXT NOT NULL,
                    title       TEXT NOT NULL,
                    content     TEXT NOT NULL,
                    tags        TEXT NOT NULL DEFAULT '[]',
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id          TEXT PRIMARY KEY,
                    user_id     TEXT NOT NULL,
                    title       TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    status      TEXT NOT NULL DEFAULT 'pending',
                    priority    TEXT NOT NULL DEFAULT 'medium',
                    due_date    TEXT,
                    tags        TEXT NOT NULL DEFAULT '[]',
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                );
                """
            )

    # ── Conversation history ─────────────────────────────────────────────────

    def add_message(
        self,
        user_id: str,
        role: str,
        content: str,
        session_id: str,
    ) -> None:
        """Append one message to the conversation log."""
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO conversations (id, user_id, role, content, session_id, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    user_id,
                    role,
                    content,
                    session_id,
                    datetime.utcnow().isoformat(),
                ),
            )

    def get_recent_messages(
        self,
        user_id: str,
        session_id: str,
        limit: int = 20,
    ) -> list[dict]:
        """Return the most recent ``limit`` messages for a session (oldest first)."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT role, content, created_at FROM conversations "
                "WHERE user_id = ? AND session_id = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (user_id, session_id, limit),
            ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def get_sessions(self, user_id: str, limit: int = 10) -> list[dict]:
        """Return recent session summaries (id, start time, message count)."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT
                    session_id,
                    MIN(created_at) AS started,
                    COUNT(*)        AS messages,
                    MAX(CASE WHEN role = 'user' THEN content ELSE '' END) AS last_user_msg
                FROM conversations
                WHERE user_id = ?
                GROUP BY session_id
                ORDER BY started DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── User profile ─────────────────────────────────────────────────────────

    def get_profile(self, user_id: str) -> dict:
        """Return the user's profile dict (defaults if not set)."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT profile_json FROM user_profile WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if row:
            return json.loads(row["profile_json"])
        return {
            "name": "User",
            "style": "concise",
            "interests": [],
            "technologies": [],
        }

    def update_profile(self, user_id: str, profile: dict) -> None:
        """Upsert the user's profile."""
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO user_profile (user_id, profile_json, updated_at) "
                "VALUES (?, ?, ?)",
                (user_id, json.dumps(profile), datetime.utcnow().isoformat()),
            )


# Singleton shared across the app
memory = SQLiteMemory()
