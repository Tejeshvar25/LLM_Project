"""Tasks agent — full CRUD + stats backed by SQLite."""
from __future__ import annotations

import json
import uuid
from datetime import datetime

from agents.base import BaseAgent
from core.config import settings
from core.memory import memory

PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class TasksAgent(BaseAgent):
    """Create, read, update, delete, and analyse tasks stored in SQLite."""

    def _db(self):
        return memory._get_conn()

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def add_task(
        self,
        title: str,
        description: str = "",
        status: str = "pending",
        priority: str = "medium",
        due_date: str | None = None,
        tags: list[str] | None = None,
        user_id: str = settings.DEFAULT_USER_ID,
    ) -> dict:
        """Create a new task and return it."""
        now = datetime.utcnow().isoformat()
        task_id = str(uuid.uuid4())
        tags = tags or []
        with self._db() as conn:
            conn.execute(
                "INSERT INTO tasks "
                "(id, user_id, title, description, status, priority, due_date, tags, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    task_id, user_id, title, description,
                    status, priority, due_date, json.dumps(tags), now, now,
                ),
            )
        return {
            "id": task_id, "title": title, "description": description,
            "status": status, "priority": priority, "due_date": due_date,
            "tags": tags, "created_at": now, "updated_at": now,
            "completed": status == "completed",
        }

    def get_task(self, task_id: str) -> dict | None:
        """Return a single task by ID."""
        with self._db() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["tags"] = json.loads(d.get("tags", "[]"))
        d["completed"] = d["status"] == "completed"
        return d

    def list_tasks(
        self,
        user_id: str = settings.DEFAULT_USER_ID,
        filter: str | None = None,
    ) -> list[dict]:
        """Return tasks for a user, optionally filtered by status string.

        ``filter`` can be ``"pending"``, ``"completed"``, ``"in_progress"``,
        ``"cancelled"``, or ``None`` / ``"all"`` for everything.
        """
        with self._db() as conn:
            if filter and filter != "all":
                rows = conn.execute(
                    "SELECT * FROM tasks WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                    (user_id, filter),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,),
                ).fetchall()

        result = []
        for r in rows:
            d = dict(r)
            d["tags"] = json.loads(d.get("tags", "[]"))
            d["completed"] = d["status"] == "completed"
            result.append(d)

        # Sort by priority then due date
        result.sort(
            key=lambda t: (
                PRIORITY_ORDER.get(t.get("priority", "medium"), 2),
                t.get("due_date") or "9999",
            )
        )
        return result

    def update_task(self, task_id: str, **kwargs) -> dict | None:
        """Update allowed task fields.  Returns the updated task or ``None``."""
        task = self.get_task(task_id)
        if not task:
            return None
        now = datetime.utcnow().isoformat()
        allowed = {"title", "description", "status", "priority", "due_date", "tags"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if "tags" in updates and isinstance(updates["tags"], list):
            updates["tags"] = json.dumps(updates["tags"])
        if not updates:
            return task
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [now, task_id]
        with self._db() as conn:
            conn.execute(
                f"UPDATE tasks SET {set_clause}, updated_at = ? WHERE id = ?", values
            )
        return self.get_task(task_id)

    def mark_complete(self, task_id: str) -> dict | None:
        """Mark a task as completed."""
        return self.update_task(task_id, status="completed")

    def delete_task(self, task_id: str) -> bool:
        """Delete a task.  Returns ``True`` if deleted."""
        with self._db() as conn:
            cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cur.rowcount > 0

    # ── Analytics ─────────────────────────────────────────────────────────────

    def stats(self, user_id: str = settings.DEFAULT_USER_ID) -> dict:
        """Compute task statistics for the Python tool."""
        from tools.python_tool import compute_task_stats

        all_tasks = self.list_tasks(user_id=user_id)
        return compute_task_stats(all_tasks)

    def get_pending_summaries(
        self,
        user_id: str = settings.DEFAULT_USER_ID,
        limit: int = 10,
    ) -> list[str]:
        """One-line summaries of pending tasks sorted by priority (for briefing)."""
        pending = self.list_tasks(user_id=user_id, filter="pending")[:limit]
        out = []
        for t in pending:
            due = f" (due {t['due_date']})" if t.get("due_date") else ""
            out.append(f"[{t['priority'].upper()}] {t['title']}{due}")
        return out


tasks_agent = TasksAgent()
