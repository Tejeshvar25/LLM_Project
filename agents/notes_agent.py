"""Notes agent — full CRUD backed by SQLite with optional AI-powered search."""
from __future__ import annotations

import json
import uuid
from datetime import datetime

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from agents.base import BaseAgent
from core.config import settings
from core.memory import memory


class NotesAgent(BaseAgent):
    """Create, read, update, delete, and query notes stored in SQLite."""

    def _db(self):
        return memory._get_conn()

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def create_note(
        self,
        title: str,
        content: str,
        tags: list[str] | None = None,
        user_id: str = settings.DEFAULT_USER_ID,
    ) -> dict:
        """Create a new note and return it."""
        now = datetime.utcnow().isoformat()
        note_id = str(uuid.uuid4())
        tags = tags or []
        with self._db() as conn:
            conn.execute(
                "INSERT INTO notes (id, user_id, title, content, tags, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (note_id, user_id, title, content, json.dumps(tags), now, now),
            )
        return {
            "id": note_id,
            "title": title,
            "content": content,
            "tags": tags,
            "created_at": now,
            "updated_at": now,
        }

    def get_note(self, note_id: str) -> dict | None:
        """Return a single note by ID, or ``None`` if not found."""
        with self._db() as conn:
            row = conn.execute(
                "SELECT * FROM notes WHERE id = ?", (note_id,)
            ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["tags"] = json.loads(d.get("tags", "[]"))
        return d

    def list_notes(
        self,
        user_id: str = settings.DEFAULT_USER_ID,
        filter_query: str = "",
    ) -> list[dict]:
        """Return all notes for a user, optionally filtered by keyword."""
        with self._db() as conn:
            if filter_query:
                rows = conn.execute(
                    "SELECT * FROM notes WHERE user_id = ? "
                    "AND (title LIKE ? OR content LIKE ?) "
                    "ORDER BY updated_at DESC",
                    (user_id, f"%{filter_query}%", f"%{filter_query}%"),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM notes WHERE user_id = ? ORDER BY updated_at DESC",
                    (user_id,),
                ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["tags"] = json.loads(d.get("tags", "[]"))
            result.append(d)
        return result

    def search_notes(
        self,
        query: str,
        user_id: str = settings.DEFAULT_USER_ID,
    ) -> list[dict]:
        """Alias for ``list_notes`` with a filter query."""
        return self.list_notes(user_id=user_id, filter_query=query)

    def update_note(
        self,
        note_id: str,
        title: str | None = None,
        content: str | None = None,
        tags: list[str] | None = None,
    ) -> dict | None:
        """Update one or more fields of a note.  Returns the updated note."""
        note = self.get_note(note_id)
        if not note:
            return None
        now = datetime.utcnow().isoformat()
        new_title = title if title is not None else note["title"]
        new_content = content if content is not None else note["content"]
        new_tags = tags if tags is not None else note["tags"]
        with self._db() as conn:
            conn.execute(
                "UPDATE notes SET title = ?, content = ?, tags = ?, updated_at = ? WHERE id = ?",
                (new_title, new_content, json.dumps(new_tags), now, note_id),
            )
        return {**note, "title": new_title, "content": new_content, "tags": new_tags, "updated_at": now}

    def delete_note(self, note_id: str) -> bool:
        """Delete a note.  Returns ``True`` if a row was deleted."""
        with self._db() as conn:
            cur = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        return cur.rowcount > 0

    # ── Analytics helpers ─────────────────────────────────────────────────────

    def get_recent_summaries(
        self,
        user_id: str = settings.DEFAULT_USER_ID,
        limit: int = 5,
    ) -> list[str]:
        """One-line summaries of the most recently updated notes (for briefing)."""
        notes = self.list_notes(user_id=user_id)[:limit]
        out = []
        for n in notes:
            snippet = n["content"][:80] + "…" if len(n["content"]) > 80 else n["content"]
            out.append(f"**{n['title']}**: {snippet}")
        return out

    # ── AI-powered queries ────────────────────────────────────────────────────

    def ai_answer_from_notes(
        self,
        question: str,
        user_id: str = settings.DEFAULT_USER_ID,
    ) -> str:
        """Use the LLM to answer a question based on all saved notes."""
        notes = self.list_notes(user_id=user_id)
        if not notes:
            return "No notes found. Create some notes first!"
        notes_text = "\n\n".join(
            f"[{n['title']}]\n{n['content']}" for n in notes[:12]
        )
        prompt = ChatPromptTemplate.from_template(
            "Based on the user's notes, answer: {question}\n\nNotes:\n{notes}\n\nAnswer concisely."
        )
        try:
            chain = prompt | self.llm | StrOutputParser()
            return chain.invoke({"question": question, "notes": notes_text})
        except Exception as exc:  # noqa: BLE001
            return f"❌ Error: {exc}"


notes_agent = NotesAgent()
