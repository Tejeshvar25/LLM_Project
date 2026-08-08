"""Research agent: Wikipedia-augmented LLM research and tech-news summaries."""
from __future__ import annotations

import json

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from agents.base import BaseAgent

RESEARCH_PROMPT = """\
You are an expert research assistant for developers and students.
The user wants to learn about: {topic}

{wiki_context}

Provide a thorough but concise research summary covering:
1. Overview and definition
2. Key concepts and recent developments
3. Practical implications for developers / students
4. Notable tools, papers, or projects
5. Recommended next steps / resources

Be factual, specific, and useful."""

NEWS_PROMPT = """\
List exactly 5 important recent trends or developments in AI, machine learning,
and modern software development that a developer/student should know about in 2024-2025.

Return ONLY a valid JSON array of short, one-sentence strings.
Example format: ["Trend 1 description.", "Trend 2 description."]

No markdown, no extra text — just the JSON array."""


class ResearchAgent(BaseAgent):
    """Researches topics using Wikipedia and LLM knowledge."""

    def __init__(self) -> None:
        super().__init__()
        self._prompt = ChatPromptTemplate.from_template(RESEARCH_PROMPT)
        self._parser = StrOutputParser()
        self._wiki_ok = self._probe_wikipedia()

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _probe_wikipedia() -> bool:
        try:
            import wikipedia  # noqa: F401

            return True
        except ImportError:
            return False

    def _wiki_summary(self, topic: str) -> str:
        """Return the first 2000 chars of the best Wikipedia article for topic."""
        if not self._wiki_ok:
            return ""
        try:
            import wikipedia

            results = wikipedia.search(topic, results=3)
            if not results:
                return ""
            page = wikipedia.page(results[0], auto_suggest=False)
            return page.summary[:2000]
        except Exception:
            return ""

    # ── Public API ───────────────────────────────────────────────────────────

    def research(self, topic: str) -> dict:
        """Research ``topic`` and return a structured result dict.

        Returns:
            ``{"topic": str, "summary": str, "wikipedia_extract": str, "source": str}``
        """
        wiki = self._wiki_summary(topic)
        wiki_context = f"Wikipedia context:\n{wiki}" if wiki else ""

        try:
            chain = self._prompt | self.llm | self._parser
            summary = chain.invoke({"topic": topic, "wiki_context": wiki_context})
            return {
                "topic": topic,
                "summary": summary,
                "wikipedia_extract": wiki,
                "source": "Wikipedia + LLM" if wiki else "LLM knowledge",
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "topic": topic,
                "summary": f"Research failed: {exc}",
                "wikipedia_extract": wiki,
                "source": "error",
            }

    def get_tech_news_summary(self) -> list[str]:
        """Return 5 current AI/tech trends as a list of strings.

        Used by the daily briefing parallel gather step.
        Falls back to a hard-coded list if the LLM call fails.
        """
        try:
            prompt = ChatPromptTemplate.from_template(NEWS_PROMPT)
            chain = prompt | self.llm | self._parser
            raw = chain.invoke({})
            start, end = raw.find("["), raw.rfind("]") + 1
            if start >= 0 and end > start:
                items = json.loads(raw[start:end])
                return [str(i) for i in items[:5]]
        except Exception:
            pass

        return [
            "Large language models continue rapid advancement in reasoning and code generation.",
            "Agentic AI frameworks (LangGraph, AutoGen) gaining enterprise adoption.",
            "Vector databases and RAG pipelines becoming the standard for knowledge retrieval.",
            "Open-source models (Llama 3, Mistral) closing the gap with proprietary LLMs.",
            "AI-powered coding assistants transforming developer productivity workflows.",
        ]


research_agent = ResearchAgent()
