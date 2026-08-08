"""Email agent: summarises a simulated inbox and drafts professional emails."""
from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from agents.base import BaseAgent

# ── Stub inbox ────────────────────────────────────────────────────────────────
# Replace with real Gmail / IMAP integration when available.

STUB_INBOX: list[dict] = [
    {
        "id": "e001",
        "from": "professor@university.edu",
        "subject": "Final Project Deadline Reminder",
        "body": (
            "Hi — just a reminder that your final project submission is due next Friday at 23:59. "
            "Please submit through the university portal. Reach out if you have any questions."
        ),
        "date": "2024-01-15",
        "read": False,
        "important": True,
    },
    {
        "id": "e002",
        "from": "teammate@gmail.com",
        "subject": "Re: RAG Pipeline Integration",
        "body": (
            "Hey! I pushed the ChromaDB integration. The retriever works but I think "
            "there's a chunking edge-case when PDFs have tables. Can you review PR #23 "
            "and run the test suite?"
        ),
        "date": "2024-01-15",
        "read": False,
        "important": True,
    },
    {
        "id": "e003",
        "from": "github@notifications.github.com",
        "subject": "[second-brain] Issue #47 — Memory leak in vectorstore",
        "body": (
            "User devuser123 opened issue #47: 'Memory leak in vectorstore initialisation'. "
            "Repeated calls to build_chroma_db() consume increasing RAM. "
            "Suggested fix: use a persistent client singleton."
        ),
        "date": "2024-01-14",
        "read": False,
        "important": True,
    },
    {
        "id": "e004",
        "from": "hr@techcorp.com",
        "subject": "Software Engineering Internship — Interview Invitation",
        "body": (
            "We reviewed your application and would like to invite you for a technical interview. "
            "Please book a slot via calendly.com/techcorp/interview. "
            "The role is a 6-month SWE internship on our AI platform team."
        ),
        "date": "2024-01-13",
        "read": False,
        "important": True,
    },
    {
        "id": "e005",
        "from": "newsletter@aiweekly.com",
        "subject": "AI Weekly #142 — Top LLM Papers",
        "body": (
            "This week: 1) New sparse attention mechanism cuts inference cost by 40%. "
            "2) Meta releases Llama 3.1 405B with improved reasoning. "
            "3) DeepMind publishes AlphaCode 2 competitive-programming results."
        ),
        "date": "2024-01-14",
        "read": True,
        "important": False,
    },
]

# ── Prompts ───────────────────────────────────────────────────────────────────

_SUMMARISE_PROMPT = """\
Summarise the following emails for a busy developer/student.
For each email, extract:
- The core message
- Any action items or deadlines

Emails:
{emails}

Write a concise, bullet-pointed summary. Group urgent items first."""

_DRAFT_PROMPT = """\
Draft a professional, clear email based on the following instructions.
Write only the email body — no subject line, no salutation header.

Instructions: {instructions}
Context (if any): {context}

Tone: professional yet friendly. Be concise."""


class EmailAgent(BaseAgent):
    """Manages a simulated email inbox: read, summarise, and draft emails."""

    # ── Inbox access ─────────────────────────────────────────────────────────

    def get_inbox(self, unread_only: bool = False) -> list[dict]:
        """Return the inbox, optionally filtered to unread messages."""
        if unread_only:
            return [e for e in STUB_INBOX if not e["read"]]
        return list(STUB_INBOX)

    def get_important_emails(self) -> list[dict]:
        """Return emails marked as important."""
        return [e for e in STUB_INBOX if e["important"]]

    def get_important_summaries(self) -> list[str]:
        """Return one-line summaries of important emails (for daily briefing)."""
        return [f"{e['subject']} — from {e['from']}" for e in self.get_important_emails()]

    # ── LLM operations ───────────────────────────────────────────────────────

    def summarize_inbox(self, unread_only: bool = True) -> dict:
        """Summarise unread (or all) emails using the LLM.

        Returns:
            ``{"summary": str, "count": int, "emails": list[dict]}``
        """
        emails = self.get_inbox(unread_only=unread_only)
        if not emails:
            return {"summary": "📭 No unread emails.", "count": 0, "emails": []}

        email_text = "\n\n---\n\n".join(
            f"From: {e['from']}\nSubject: {e['subject']}\nDate: {e['date']}\n\n{e['body']}"
            for e in emails
        )

        try:
            chain = (
                ChatPromptTemplate.from_template(_SUMMARISE_PROMPT)
                | self.llm
                | StrOutputParser()
            )
            summary = chain.invoke({"emails": email_text})
            return {"summary": summary, "count": len(emails), "emails": emails}
        except Exception as exc:  # noqa: BLE001
            return {
                "summary": f"Summarisation error: {exc}",
                "count": len(emails),
                "emails": emails,
            }

    def draft_email(self, instructions: str, context: str = "") -> str:
        """Draft a professional email body based on natural-language instructions."""
        try:
            chain = (
                ChatPromptTemplate.from_template(_DRAFT_PROMPT)
                | self.llm
                | StrOutputParser()
            )
            return chain.invoke({"instructions": instructions, "context": context})
        except Exception as exc:  # noqa: BLE001
            return f"❌ Draft failed: {exc}"

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        sender_email: str = "",
        app_password: str = "",
    ) -> dict:
        """Send an email using SMTP (Google App Password)."""
        from core.email_sender import send_email_via_smtp

        return send_email_via_smtp(
            to_email=to_email,
            subject=subject,
            body=body,
            sender_email=sender_email,
            app_password=app_password,
        )


email_agent = EmailAgent()
