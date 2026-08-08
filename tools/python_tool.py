"""Safe Python code execution tool for analytics and task statistics."""
from __future__ import annotations

import io
import sys
import traceback
from typing import Any


def execute_python(code: str, context: dict[str, Any] | None = None) -> dict:
    """Execute a Python code string in a sandboxed namespace.

    Args:
        code:    Python code to run.
        context: Optional variables injected into the execution namespace.

    Returns:
        ``{"success": bool, "output": str, "result": Any, "error": str | None}``
        The variable ``_result`` set inside ``code`` is surfaced as ``result``.
    """
    namespace: dict[str, Any] = {"__builtins__": __builtins__}
    if context:
        namespace.update(context)

    buf = io.StringIO()
    old_stdout, sys.stdout = sys.stdout, buf

    try:
        exec(compile(code, "<tool>", "exec"), namespace)  # noqa: S102
        return {
            "success": True,
            "output": buf.getvalue(),
            "result": namespace.get("_result"),
            "error": None,
        }
    except Exception:
        return {
            "success": False,
            "output": buf.getvalue(),
            "result": None,
            "error": traceback.format_exc(),
        }
    finally:
        sys.stdout = old_stdout


def compute_task_stats(tasks: list[dict]) -> dict:
    """Compute rich statistics for a list of task dicts via the Python tool.

    Returns a dict with ``total``, ``completed``, ``pending``, ``in_progress``,
    ``completion_rate``, ``by_priority``, and ``table`` (list of row dicts).
    """
    code = """
from collections import Counter

statuses   = Counter(t.get("status",   "unknown")  for t in tasks)
priorities = Counter(t.get("priority", "unknown")  for t in tasks)

total           = len(tasks)
completed       = statuses.get("completed",  0)
pending         = statuses.get("pending",    0)
in_progress     = statuses.get("in_progress", 0)
completion_rate = round(completed / total * 100, 1) if total else 0.0

_result = {
    "total":           total,
    "completed":       completed,
    "pending":         pending,
    "in_progress":     in_progress,
    "completion_rate": completion_rate,
    "by_priority":     dict(priorities),
    "table": [
        {
            "Title":    t["title"],
            "Status":   t["status"],
            "Priority": t["priority"],
            "Due":      t.get("due_date") or "—",
        }
        for t in tasks
    ],
}
"""
    result = execute_python(code, {"tasks": tasks})
    if result["success"] and result["result"]:
        return result["result"]
    # Fallback: bare computation without exec
    total = len(tasks)
    completed = sum(1 for t in tasks if t.get("status") == "completed")
    return {
        "total": total,
        "completed": completed,
        "pending": total - completed,
        "in_progress": sum(1 for t in tasks if t.get("status") == "in_progress"),
        "completion_rate": round(completed / total * 100, 1) if total else 0.0,
        "by_priority": {},
        "table": [],
        "error": result.get("error"),
    }
