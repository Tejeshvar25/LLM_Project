"""Global configuration loaded from environment variables.

All settings are centralised here so every module imports from a single source.
Change provider, model names, or paths here (or via .env) — nowhere else.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application-wide settings derived from environment variables."""

    # ── Paths ────────────────────────────────────────────────────────────────
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOADS_DIR: Path = DATA_DIR / "uploads"
    CHROMA_DIR: str = str(DATA_DIR / "chroma_db")
    SQLITE_PATH: str = str(DATA_DIR / "assistant.db")

    # ── LLM provider ─────────────────────────────────────────────────────────
    # Supported: "groq" | "openai" | "google"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")

    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_MODEL: str = os.getenv("GOOGLE_MODEL", "gemini-1.5-flash")

    # ── Embeddings ───────────────────────────────────────────────────────────
    # HuggingFace local model — no API key required
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # ── RAG ──────────────────────────────────────────────────────────────────
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "4"))
    CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "second_brain")

    # ── App ──────────────────────────────────────────────────────────────────
    DEFAULT_USER_ID: str = os.getenv("DEFAULT_USER_ID", "default_user")
    MAX_HISTORY_MESSAGES: int = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))

    # ── SMTP Email (Google App Password) ──────────────────────────────────────
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_EMAIL: str = os.getenv("SMTP_EMAIL", "")
    SMTP_APP_PASSWORD: str = os.getenv("SMTP_APP_PASSWORD", "")

    def __init__(self) -> None:
        """Create all required directories on startup."""
        self.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        Path(self.CHROMA_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.SQLITE_PATH).parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
