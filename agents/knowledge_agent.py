"""RAG-based knowledge agent using ChromaDB + LangChain LCEL."""
from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from agents.base import BaseAgent
from core.vectorstore import get_retriever

RAG_PROMPT = """\
You are a knowledgeable assistant with access to the user's personal document library.
Use ONLY the retrieved context below to answer the question.
If the context does not contain enough information, say so clearly — do not invent facts.

Retrieved context:
{context}

Question: {question}

Provide a clear, well-structured answer. Cite the source document(s) when relevant."""


class KnowledgeAgent(BaseAgent):
    """Answers questions using retrieval-augmented generation over ChromaDB."""

    def __init__(self) -> None:
        super().__init__()
        self._prompt = ChatPromptTemplate.from_template(RAG_PROMPT)
        self._parser = StrOutputParser()

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _format_docs(docs: list) -> str:
        return "\n\n---\n\n".join(d.page_content for d in docs)

    # ── Public API ───────────────────────────────────────────────────────────

    def answer(self, question: str) -> dict:
        """Answer ``question`` using RAG.

        Returns:
            ``{"answer": str, "sources": list[str], "documents": list[dict]}``
        """
        retriever = get_retriever()
        if retriever is None:
            return {
                "answer": (
                    "📭 The knowledge base is empty. "
                    "Upload documents in the sidebar and click **Build Knowledge Base**."
                ),
                "sources": [],
                "documents": [],
            }

        try:
            docs = retriever.invoke(question)
            context = self._format_docs(docs)
            chain = self._prompt | self.llm | self._parser
            answer = chain.invoke({"context": context, "question": question})
            sources = list({d.metadata.get("source", "unknown") for d in docs})
            return {
                "answer": answer,
                "sources": sources,
                "documents": [
                    {"content": d.page_content[:300], "metadata": d.metadata}
                    for d in docs
                ],
            }
        except Exception as exc:  # noqa: BLE001
            return {"answer": f"❌ Error: {exc}", "sources": [], "documents": []}


knowledge_agent = KnowledgeAgent()
