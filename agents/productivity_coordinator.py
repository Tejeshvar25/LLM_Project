"""ProductivityCoordinator — central orchestrator using LangChain LCEL.

Routing
-------
A lightweight LLM classifier maps every user message to one of seven intents:
  chat · knowledge · research · notes · tasks · email · briefing

Each intent is handled by a dedicated method that calls the appropriate agent.

Daily Briefing
--------------
Uses ``RunnableParallel`` to gather data from four sources concurrently, then
synthesises them into a ``DailyBriefing`` Pydantic model via the LLM.
"""
from __future__ import annotations

import json
import uuid
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel

from agents.base import BaseAgent
from agents.email_agent import email_agent
from agents.knowledge_agent import knowledge_agent
from agents.notes_agent import notes_agent
from agents.research_agent import research_agent
from agents.tasks_agent import tasks_agent
from core.config import settings
from core.memory import memory
from schemas.briefing import DailyBriefing

# ── Prompts ───────────────────────────────────────────────────────────────────

_CLASSIFIER_PROMPT = """\
Classify the user message below into exactly one routing category.

Categories:
  knowledge  – question about uploaded documents or personal knowledge base
  research   – question about external topics, news, or general information
  notes      – create / view / search / edit / delete notes
  tasks      – create / view / complete / delete tasks or to-dos
  email      – read, summarise, or draft an email
  briefing   – daily briefing, today's summary, or daily report request
  chat       – general conversation, greetings, or anything else

User message: {message}

Reply with ONE word only (no punctuation, no explanation)."""

_CHAT_PROMPT = """\
You are a helpful AI assistant — a "second brain" for a developer / student.
You have access to their personal knowledge base, notes, tasks, and email.

Recent conversation:
{history}

User: {message}

Respond helpfully and concisely. Ask one focused clarifying question if needed."""

_NOTES_PARSE_PROMPT = """\
Parse the user's intent for a notes operation.

User message: {message}

Return ONLY a JSON object with these fields (omit irrelevant ones):
{{
  "action":  "create" | "list" | "search" | "update" | "delete",
  "title":   "<note title if mentioned>",
  "content": "<note content if mentioned>",
  "query":   "<search term if searching>",
  "tags":    ["tag1", "tag2"]
}}"""

_TASKS_PARSE_PROMPT = """\
Parse the user's intent for a tasks operation.

User message: {message}

Return ONLY a JSON object:
{{
  "action":      "create" | "list" | "complete" | "delete" | "update",
  "title":       "<task title>",
  "description": "<description if any>",
  "priority":    "low" | "medium" | "high" | "critical",
  "due_date":    "YYYY-MM-DD or null"
}}"""

_BRIEFING_SYNTHESIS_PROMPT = """\
You are generating a daily briefing for a developer / student.

Here is today's data:

PENDING TASKS:
{tasks}

RECENT NOTES HIGHLIGHTS:
{notes}

IMPORTANT EMAILS:
{emails}

LATEST AI / TECH NEWS:
{research}

Generate an energising, actionable daily briefing. Respond with ONLY a valid JSON object:
{{
  "daily_summary":              "<2-3 sentence motivating overview>",
  "important_emails":           ["<short email action item>", ...],
  "pending_tasks":              ["<task with priority>", ...],
  "knowledge_base_highlights":  ["<insight from notes>", ...],
  "latest_research":            ["<tech trend>", ...],
  "recommendations":            ["<actionable recommendation>", ...],
  "next_actions":               ["<specific next step>", ...]
}}

Return ONLY the JSON — no markdown fences, no extra text."""


class ProductivityCoordinator(BaseAgent):
    """Routes user messages and orchestrates multi-agent workflows."""

    def __init__(self, user_id: str = settings.DEFAULT_USER_ID) -> None:
        super().__init__()
        self.user_id = user_id
        self._classifier = (
            ChatPromptTemplate.from_template(_CLASSIFIER_PROMPT)
            | self.llm
            | StrOutputParser()
        )
        self._chat_chain = (
            ChatPromptTemplate.from_template(_CHAT_PROMPT)
            | self.llm
            | StrOutputParser()
        )

    # ── Intent classification ─────────────────────────────────────────────────

    def _classify(self, message: str) -> str:
        valid = {"knowledge", "research", "notes", "tasks", "email", "briefing", "chat"}
        try:
            intent = self._classifier.invoke({"message": message}).strip().lower()
            return intent if intent in valid else "chat"
        except Exception:
            return "chat"

    # ── History helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _format_history(history: list[dict]) -> str:
        if not history:
            return "No prior conversation."
        lines = []
        for msg in history[-8:]:
            role = "User" if msg.get("role") == "user" else "Assistant"
            lines.append(f"{role}: {msg.get('content', '')}")
        return "\n".join(lines)

    # ── Intent handlers ───────────────────────────────────────────────────────

    def _handle_chat(self, message: str, history: list[dict]) -> dict:
        try:
            resp = self._chat_chain.invoke(
                {"message": message, "history": self._format_history(history)}
            )
            return {"type": "chat", "response": resp}
        except Exception as exc:
            return {"type": "chat", "response": f"❌ {exc}"}

    def _handle_knowledge(self, message: str) -> dict:
        result = knowledge_agent.answer(message)
        return {"type": "knowledge", **result}

    def _handle_research(self, message: str) -> dict:
        result = research_agent.research(message)
        return {"type": "research", "response": result["summary"], **result}

    def _handle_email(self, message: str) -> dict:
        # Check if user wants to draft
        lower = message.lower()
        if any(kw in lower for kw in ("draft", "write", "compose", "send")):
            draft = email_agent.draft_email(message)
            return {"type": "email", "action": "draft", "response": draft}
        result = email_agent.summarize_inbox()
        return {"type": "email", "action": "summary", "response": result.get("summary", ""), **result}

    def _handle_notes(self, message: str) -> dict:
        """Parse user intent and perform the appropriate notes operation."""
        try:
            chain = (
                ChatPromptTemplate.from_template(_NOTES_PARSE_PROMPT)
                | self.llm
                | StrOutputParser()
            )
            raw = chain.invoke({"message": message})
            start, end = raw.find("{"), raw.rfind("}") + 1
            parsed: dict = json.loads(raw[start:end]) if start >= 0 and end > start else {}
        except Exception:
            parsed = {}

        action = parsed.get("action", "list")

        if action == "create":
            title = parsed.get("title") or "Untitled Note"
            content = parsed.get("content") or ""
            raw_tags = parsed.get("tags", [])
            tags = [t.strip() for t in raw_tags] if isinstance(raw_tags, list) else []
            note = notes_agent.create_note(title, content, tags, self.user_id)
            return {"type": "notes", "action": "created", "response": f"✅ Note created: **{title}**", "data": note}

        if action in ("search", "find"):
            query = parsed.get("query") or parsed.get("title") or message
            results = notes_agent.search_notes(query, self.user_id)
            return {"type": "notes", "action": "search", "response": f"Found **{len(results)}** note(s) matching '{query}'", "data": results}

        if action == "delete":
            title = parsed.get("title", "")
            matches = notes_agent.list_notes(self.user_id, filter_query=title)
            if matches:
                notes_agent.delete_note(matches[0]["id"])
                return {"type": "notes", "action": "deleted", "response": f"🗑️ Deleted note: **{matches[0]['title']}**"}
            return {"type": "notes", "action": "not_found", "response": "No matching note found."}

        # Default: list
        all_notes = notes_agent.list_notes(self.user_id)
        return {"type": "notes", "action": "list", "response": f"You have **{len(all_notes)}** note(s).", "data": all_notes}

    def _handle_tasks(self, message: str) -> dict:
        """Parse user intent and perform the appropriate tasks operation."""
        try:
            chain = (
                ChatPromptTemplate.from_template(_TASKS_PARSE_PROMPT)
                | self.llm
                | StrOutputParser()
            )
            raw = chain.invoke({"message": message})
            start, end = raw.find("{"), raw.rfind("}") + 1
            parsed: dict = json.loads(raw[start:end]) if start >= 0 and end > start else {}
        except Exception:
            parsed = {}

        action = parsed.get("action", "list")

        if action == "create":
            title = parsed.get("title") or "New Task"
            task = tasks_agent.add_task(
                title=title,
                description=parsed.get("description", ""),
                priority=parsed.get("priority", "medium"),
                due_date=parsed.get("due_date"),
                user_id=self.user_id,
            )
            return {"type": "tasks", "action": "created", "response": f"✅ Task added: **{title}**", "data": task}

        if action == "complete":
            title_kw = parsed.get("title", "")
            pending = tasks_agent.list_tasks(self.user_id, filter="pending")
            match = next((t for t in pending if title_kw.lower() in t["title"].lower()), None)
            if match:
                tasks_agent.mark_complete(match["id"])
                return {"type": "tasks", "action": "completed", "response": f"✅ Marked complete: **{match['title']}**"}
            return {"type": "tasks", "action": "not_found", "response": "No matching pending task found."}

        if action == "delete":
            title_kw = parsed.get("title", "")
            all_t = tasks_agent.list_tasks(self.user_id)
            match = next((t for t in all_t if title_kw.lower() in t["title"].lower()), None)
            if match:
                tasks_agent.delete_task(match["id"])
                return {"type": "tasks", "action": "deleted", "response": f"🗑️ Deleted: **{match['title']}**"}
            return {"type": "tasks", "action": "not_found", "response": "No matching task found."}

        # Default: list
        all_tasks = tasks_agent.list_tasks(self.user_id)
        return {"type": "tasks", "action": "list", "response": f"You have **{len(all_tasks)}** task(s).", "data": all_tasks}

    # ── Public API ────────────────────────────────────────────────────────────

    def handle_user_message(self, message: str, state: dict) -> dict:
        """Route a user message to the appropriate agent and return a result dict.

        Args:
            message: The raw user input.
            state:   Streamlit session_state dict (used for session_id + history).

        Returns:
            A dict with at minimum ``"type"`` and ``"response"`` keys.
        """
        session_id: str = state.get("session_id", "default")
        history: list[dict] = state.get("chat_history_raw", [])

        intent = self._classify(message)

        if intent == "knowledge":
            result = self._handle_knowledge(message)
        elif intent == "research":
            result = self._handle_research(message)
        elif intent == "notes":
            result = self._handle_notes(message)
        elif intent == "tasks":
            result = self._handle_tasks(message)
        elif intent == "email":
            result = self._handle_email(message)
        elif intent == "briefing":
            briefing = self.generate_daily_briefing(self.user_id, state)
            result = {
                "type": "briefing",
                "response": "Your daily briefing is ready! 🌅",
                "briefing": briefing,
            }
        else:
            result = self._handle_chat(message, history)

        # Persist to SQLite
        try:
            memory.add_message(self.user_id, "user", message, session_id)
            resp_text = result.get("response", "")
            if isinstance(resp_text, str):
                memory.add_message(self.user_id, "assistant", resp_text, session_id)
        except Exception:
            pass

        result["intent"] = intent
        return result

    def generate_daily_briefing(self, user_id: str, state: dict) -> DailyBriefing:
        """Generate a ``DailyBriefing`` using ``RunnableParallel`` data gathering.

        Four data sources are queried concurrently:
        - Pending tasks from TasksAgent
        - Recent note summaries from NotesAgent
        - Important email summaries from EmailAgent
        - AI/tech news from ResearchAgent

        The LLM then synthesises all inputs into a ``DailyBriefing`` object.

        Args:
            user_id: The user whose data to gather.
            state:   Streamlit session_state (unused here, kept for signature parity).

        Returns:
            A populated ``DailyBriefing`` Pydantic model.
        """
        uid = user_id or self.user_id

        parallel = RunnableParallel(
            tasks=RunnableLambda(lambda _: tasks_agent.get_pending_summaries(uid)),
            notes=RunnableLambda(lambda _: notes_agent.get_recent_summaries(uid)),
            emails=RunnableLambda(lambda _: email_agent.get_important_summaries()),
            research=RunnableLambda(lambda _: research_agent.get_tech_news_summary()),
        )

        gathered: dict[str, list[str]] = parallel.invoke({})

        def _join(items: list[str], fallback: str = "None") -> str:
            return "\n".join(f"• {i}" for i in items) if items else fallback

        try:
            chain = (
                ChatPromptTemplate.from_template(_BRIEFING_SYNTHESIS_PROMPT)
                | self.llm
                | StrOutputParser()
            )
            raw = chain.invoke(
                {
                    "tasks": _join(gathered.get("tasks", []), "No pending tasks"),
                    "notes": _join(gathered.get("notes", []), "No recent notes"),
                    "emails": _join(gathered.get("emails", []), "No important emails"),
                    "research": _join(gathered.get("research", []), "No research data"),
                }
            )
            start, end = raw.find("{"), raw.rfind("}") + 1
            data: dict = json.loads(raw[start:end]) if start >= 0 and end > start else {}

            return DailyBriefing(
                daily_summary=data.get("daily_summary", "Briefing generated."),
                important_emails=data.get("important_emails", gathered.get("emails", [])),
                pending_tasks=data.get("pending_tasks", gathered.get("tasks", [])),
                knowledge_base_highlights=data.get("knowledge_base_highlights", gathered.get("notes", [])),
                latest_research=data.get("latest_research", gathered.get("research", [])),
                recommendations=data.get("recommendations", []),
                next_actions=data.get("next_actions", []),
            )

        except Exception as exc:  # noqa: BLE001
            # Graceful fallback — assemble from gathered data without synthesis
            return DailyBriefing(
                daily_summary=(
                    f"Here is your daily briefing (LLM synthesis failed: {exc}). "
                    "Raw data is shown below."
                ),
                important_emails=gathered.get("emails", []),
                pending_tasks=gathered.get("tasks", []),
                knowledge_base_highlights=gathered.get("notes", []),
                latest_research=gathered.get("research", []),
                recommendations=["Review pending tasks", "Check email inbox", "Update your notes"],
                next_actions=["Start on highest-priority task", "Reply to important emails"],
            )
